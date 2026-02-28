// Main application orchestration for Arcane Auditor web interface

import { ConfigManager } from './config-manager.js';
import { ResultsRenderer } from './results-renderer.js';
import { downloadResults, getLastSortBy, getLastSortFilesBy } from './utils.js';
import { showMagicalAnalysisComplete } from './magic-mode.js';

class ArcaneAuditorApp {
    constructor() {
        this.currentResult = null;
        this.filteredFindings = [];
        this.expandedFiles = new Set();
        this.findingExplanations = new Map(); // key: "index::rule_id::file_path::line" → explanation obj
        this.uploadedFileName = null;
        this.selectedFiles = []; // For multiple file uploads

        // File contents and fix state
        this.editedFileContents = new Map();    // file_path → current content (updated by autofix)
        this.originalFileContents = new Map();  // file_path → original content
        this.resolvedFindings = new Set();       // set of original finding indices that are resolved
        this.autofixInProgress = new Set();      // finding indices currently being auto-fixed
        this.isRevalidating = false;

        this.currentFilters = {
            severity: 'all',
            fileType: 'all',
            sortBy: getLastSortBy(),
            sortFilesBy: getLastSortFilesBy()
        };
        
        // Initialize managers
        this.configManager = new ConfigManager(this);
        this.resultsRenderer = new ResultsRenderer(this);
        
        this.initializeEventListeners();
        this.configManager.initializeTheme();
        this.configManager.loadConfigurations();
    }

    initializeEventListeners() {
        // File input listeners
        const fileInput = document.getElementById('file-input');
        const filesInput = document.getElementById('files-input');
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        
        if (filesInput) {
            filesInput.addEventListener('change', (e) => this.handleFilesSelect(e));
        }

        // Button click handlers for file selection
        const chooseFileBtn = document.getElementById('choose-file-btn');
        if (chooseFileBtn) {
            chooseFileBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }
        
        const chooseFilesBtn = document.getElementById('choose-files-btn');
        if (chooseFilesBtn) {
            chooseFilesBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                filesInput.click();
            });
        }

        // Upload button listeners
        const uploadFilesBtn = document.getElementById('upload-files-btn');
        if (uploadFilesBtn) {
            uploadFilesBtn.addEventListener('click', () => this.uploadAndAnalyze());
        }

        // Drag and drop handlers
        const uploadArea = document.getElementById('upload-area');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
            uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        }

        // File expansion listeners (delegated)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.file-header')) {
                const filePath = e.target.closest('.file-header').dataset.filePath;
                if (filePath) {
                    this.resultsRenderer.toggleFileExpansion(filePath);
                }
            }
        });
    }

    // Navigation methods
    showUpload() {
        this.hideAllSections();
        document.getElementById('upload-section').style.display = 'block';
    }

    showLoading() {
        this.hideAllSections();
        document.getElementById('loading-section').style.display = 'block';
    }

    showResults() {
        this.hideAllSections();
        document.getElementById('results-section').style.display = 'block';

        // Initialize filtered findings with current result findings
        if (this.currentResult) {
            this.filteredFindings = [...this.currentResult.findings];
        }

        // Initialize file contents for inline editor
        this.initializeFileContents();

        // Display context awareness panel if available
        if (this.currentResult && this.currentResult.context) {
            this.resultsRenderer.displayContext(this.currentResult.context);
        }

        this.resultsRenderer.renderResults();

        // Show magical analysis completion if in magic mode
        showMagicalAnalysisComplete(this.currentResult);

        // Auto-trigger AI explanations if there are findings
        if (this.currentResult && this.currentResult.findings.length > 0) {
            this.explainWithAI();
        }
    }

    showError(message) {
        this.hideAllSections();
        const errorSection = document.getElementById('error-section');
        const errorMessage = document.getElementById('error-message');
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
    }

    hideAllSections() {
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('loading-section').style.display = 'none';
        document.getElementById('error-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('context-section').style.display = 'none';
        document.getElementById('ai-loading-fab').style.display = 'none';
    }

    // File handling methods
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        
        if (files.length > 0) {
            // Check if any ZIP files are present
            const zipFiles = files.filter(file => file.name.endsWith('.zip'));
            
            if (zipFiles.length > 0) {
                // If multiple ZIP files are present, show error
                if (zipFiles.length > 1) {
                    this.showError('Only one ZIP file can be uploaded at a time. Please drop a single ZIP file or individual files (.pmd, .pod, .amd, .smd, .script).');
                    return;
                }
                // Single ZIP file - proceed with upload
                this.selectedFiles = [zipFiles[0]];
                this.uploadedFileName = zipFiles[0].name;
                this.uploadFile(zipFiles[0]); // Auto-upload ZIP files
            } else {
                // No ZIP files - handle individual files
                const validExtensions = ['.pmd', '.pod', '.amd', '.smd', '.script'];
                const validFiles = files.filter(file => {
                    return validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
                });
                
                if (validFiles.length > 0) {
                    this.selectedFiles = validFiles;
                    this.uploadedFileName = null; // Don't set for individual files
                    this.updateSelectedFilesDisplay(); // Show files in list for individual files
                } else {
                    this.showError('Please drop valid files (.zip or .pmd, .pod, .amd, .smd, .script)');
                    return;
                }
            }
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            if (file.name.endsWith('.zip')) {
                // ZIP files should auto-upload immediately
                this.uploadedFileName = file.name;
                this.uploadFile(file);
            } else {
                // Non-ZIP files go to file list
                this.showError('Please select a ZIP file');
            }
        }
    }

    handleFilesSelect(event) {
        const files = Array.from(event.target.files);
        if (files.length > 0) {
            // Don't set uploadedFileName for individual files
            this.uploadedFileName = null;
            this.selectedFiles = files;
            this.updateSelectedFilesDisplay();
        }
    }

    updateSelectedFilesDisplay() {
        const selectedFilesList = document.getElementById('selected-files-list');
        const selectedFilesContainer = document.getElementById('files-list-content');
        
        if (this.selectedFiles.length === 0) {
            selectedFilesList.style.display = 'none';
            return;
        }

        selectedFilesList.style.display = 'block';
        const html = this.selectedFiles.map(file => `
            <div class="selected-file">
                <span class="file-icon">📄</span>
                <span class="file-name">${file.name}</span>
                <span class="file-size">(${this.formatFileSize(file.size)})</span>
            </div>
        `).join('');
        
        selectedFilesContainer.innerHTML = html;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async uploadFile(file) {
        // Validate configuration is selected
        if (!this.configManager.selectedConfig) {
            this.showError('Please select a configuration before uploading files.');
            return;
        }

        // Client-side file size validation
        const maxFileSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxFileSize) {
            this.showError(`File too large. Maximum size: ${maxFileSize / (1024 * 1024)}MB`);
            return;
        }

        const formData = new FormData();
        formData.append('files', file);
        formData.append('config', this.configManager.selectedConfig);

        try {
            this.showLoading();
            this.updateLoadingMessage('Uploading file...');

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                if (data.job_id) {
                    // New async API - poll for results
                    await this.pollJobStatus(data.job_id);
                } else {
                    // Legacy sync API - show results immediately
                    this.currentResult = data;
                    this.filteredFindings = data.findings;
                    this.showResults();
                }
            } else {
                throw new Error(data.detail || 'Analysis failed');
            }
        } catch (error) {
            this.showError(error.message || 'Upload failed');
        }
    }

    async uploadAndAnalyze() {
        if (this.selectedFiles.length === 0) {
            alert('Please select a file or files to analyze');
            return;
        }

        if (!this.configManager.selectedConfig) {
            alert('Please select a configuration');
            return;
        }

        this.showLoading();

        try {
            const formData = new FormData();
            
            // Always use 'files' field name for consistency with backend
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            formData.append('config', this.configManager.selectedConfig);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Upload failed: ${errorText}`);
            }

            const result = await response.json();
            const jobId = result.job_id;

            // Start polling for job completion
            this.pollJobStatus(jobId);

        } catch (error) {
            console.error('Upload error:', error);
            this.showError(`Upload failed: ${error.message}`);
        }
    }

    updateLoadingMessage(message) {
        const loadingSection = document.getElementById('loading-section');
        const loadingText = loadingSection.querySelector('.loading-text');
        if (loadingText) {
            loadingText.textContent = message;
        }
    }

    async pollJobStatus(jobId) {
        const maxAttempts = 60; // 5 minutes with 5-second intervals
        let attempts = 0;

        const poll = async () => {
            try {
                const response = await fetch(`/api/job/${jobId}`);
                const jobData = await response.json();

                if (response.ok) {
                    if (jobData.status === 'completed') {
                        this.currentResult = jobData.result;
                        this.currentResult.job_id = jobId; // Store job_id for download
                        this.filteredFindings = jobData.result.findings;
                        this.showResults();
                        return;
                    } else if (jobData.status === 'failed') {
                        throw new Error(jobData.error || 'Analysis failed');
                    } else if (jobData.status === 'running' || jobData.status === 'queued') {
                        // Update loading message with status
                        this.updateLoadingMessage(`Analysis ${jobData.status}...`);
                        
                        // Continue polling
                        attempts++;
                        if (attempts < maxAttempts) {
                            setTimeout(poll, 5000); // Poll every 5 seconds
                        } else {
                            throw new Error('Analysis timed out');
                        }
                    }
                } else {
                    throw new Error('Failed to check job status');
                }
            } catch (error) {
                this.showError(error.message || 'Job polling failed');
            }
        };

        poll();
    }

    // Utility methods
    async downloadResults() {
        await downloadResults(this.currentResult);
    }

    // Filter and sort methods (delegated to results renderer)
    updateSeverityFilter(value) {
        this.resultsRenderer.updateSeverityFilter(value);
    }

    updateFileTypeFilter(value) {
        this.resultsRenderer.updateFileTypeFilter(value);
    }

    updateSortBy(value) {
        this.resultsRenderer.updateSortBy(value);
    }

    updateSortFilesBy(value) {
        this.resultsRenderer.updateSortFilesBy(value);
    }

    expandAllFiles() {
        this.resultsRenderer.expandAllFiles();
    }

    collapseAllFiles() {
        this.resultsRenderer.collapseAllFiles();
    }

    static AI_LOADING_PHRASES = [
        'Scrying the code',
        'Consulting the archmage',
        'Brewing insight potion',
        'Reading the runes',
        'Channeling the Weave',
        'Summoning dragon wisdom',
        'Decoding ancient scrolls',
        'Casting divination',
        'Invoking elder sight',
        'Attuning the crystal',
        'Unraveling the hex',
        'Whispering to wyrms',
        'Forging arcane links',
        'Gazing into the abyss',
        'Conjuring clarity',
        'Awakening the oracle',
        'Sifting through omens',
        'Parsing the prophecy',
        'Taming wild magic',
        'Communing with spirits',
    ];

    async explainWithAI() {
        if (!this.currentResult || !this.currentResult.findings.length) return;

        const fab = document.getElementById('ai-loading-fab');
        const label = document.getElementById('ai-loading-text');

        // Pick a random phrase, never repeating the last one
        const phrases = ArcaneAuditorApp.AI_LOADING_PHRASES;
        let idx;
        do {
            idx = Math.floor(Math.random() * phrases.length);
        } while (phrases.length > 1 && idx === this._lastPhraseIdx);
        this._lastPhraseIdx = idx;
        label.textContent = phrases[idx];

        // Show pill in bottom-left corner
        fab.style.display = 'block';

        try {
            const response = await fetch('/api/explain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    findings: {
                        findings: this.currentResult.findings,
                        summary: this.currentResult.summary
                    }
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'AI explanation failed');
            }

            if (data.format === 'structured' && data.explanations && data.findings_order) {
                this.findingExplanations.clear();
                for (const expl of data.explanations) {
                    const idx = expl.index;
                    if (idx >= 0 && idx < data.findings_order.length) {
                        const f = data.findings_order[idx];
                        const key = `${idx}::${f.rule_id}::${f.file_path}::${f.line}`;
                        this.findingExplanations.set(key, expl);
                    }
                }
                // Re-render findings with inline explanations
                this.resultsRenderer.renderFindings();
            }
            // Hide FAB — done (structured or fallback)
            fab.style.display = 'none';
        } catch (error) {
            // Hide FAB on error too — no lingering spinner
            fab.style.display = 'none';
            console.error('AI explanation failed:', error.message);
        }
    }

    renderMarkdown(text) {
        // Split into sections by numbered headings (### 1. or ## 1.)
        // Everything before the first numbered heading is "preamble"
        const sections = [];
        let currentSection = null;
        const lines = text.split('\n');

        for (const line of lines) {
            const numberedHeading = line.match(/^(#{2,4})\s+(\d+)\.\s+(.+)$/);
            if (numberedHeading) {
                if (currentSection) sections.push(currentSection);
                currentSection = { title: line, body: [] };
            } else if (currentSection) {
                currentSection.body.push(line);
            } else {
                // Preamble (before any numbered section)
                if (!sections.length || sections[sections.length - 1].title !== null) {
                    sections.push({ title: null, body: [] });
                }
                sections[sections.length - 1].body.push(line);
            }
        }
        if (currentSection) sections.push(currentSection);

        // Render each section
        const renderedSections = sections.map((section, idx) => {
            const rawText = section.title
                ? section.title + '\n' + section.body.join('\n')
                : section.body.join('\n');
            const trimmed = rawText.trim();
            if (!trimmed) return '';
            const html = this._markdownToHtml(trimmed);
            if (!html) return '';

            const cardId = `explain-card-${idx}`;
            const copyBtn = `<button class="explain-copy-btn" onclick="copyExplainCard('${cardId}')" title="Copy to clipboard">📋 Copy</button>`;
            const extraClass = section.title ? '' : ' explain-card-summary';
            return `<div class="explain-card${extraClass}" id="${cardId}">${copyBtn}${html}</div>`;
        });

        return renderedSections.join('\n');
    }

    _markdownToHtml(text) {
        let html = text
            // Escape HTML entities first
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Code blocks (``` ... ```)
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
            return `<pre><code class="lang-${lang}">${code.trim()}</code></pre>`;
        });

        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Blockquotes
        html = html.replace(/^&gt;\s*(.+)$/gm, '<blockquote>$1</blockquote>');

        // Headings
        html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

        // Bold and italic
        html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

        // Tables
        html = html.replace(/((?:^\|.+\|$\n?)+)/gm, (tableBlock) => {
            const rows = tableBlock.trim().split('\n').filter(r => r.trim());
            if (rows.length < 2) return tableBlock;
            const isSeparator = /^\|[\s:-]+\|/.test(rows[1]);
            if (!isSeparator) return tableBlock;
            let tableHtml = '<table><thead><tr>';
            rows[0].split('|').filter(c => c.trim() !== '').forEach(cell => {
                tableHtml += `<th>${cell.trim()}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';
            for (let i = 2; i < rows.length; i++) {
                tableHtml += '<tr>';
                rows[i].split('|').filter(c => c.trim() !== '').forEach(cell => {
                    tableHtml += `<td>${cell.trim()}</td>`;
                });
                tableHtml += '</tr>';
            }
            tableHtml += '</tbody></table>';
            return tableHtml;
        });

        // Horizontal rules
        html = html.replace(/^---$/gm, '<hr>');

        // Unordered lists
        html = html.replace(/^(\s*)[-*] (.+)$/gm, (_, indent, content) => {
            const depth = Math.floor(indent.length / 2);
            return `<li class="md-depth-${depth}">${content}</li>`;
        });
        html = html.replace(/((?:<li[^>]*>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

        // Ordered lists
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(?:^|(?<=<\/ul>)\n)((?:<li>.*<\/li>\n?)+)/gm, '<ol>$1</ol>');

        // Paragraphs
        html = html.replace(/^(?!<[houplbt]|<li|<pre|<hr|<t)(.+)$/gm, '<p>$1</p>');

        // Clean up
        html = html.replace(/\n{2,}/g, '\n');

        return html;
    }

    initializeFileContents() {
        this.editedFileContents.clear();
        this.originalFileContents.clear();
        this.resolvedFindings.clear();
        if (!this.currentResult) return;

        // Collect unique file_paths and reconstruct full content from snippet lines
        const seen = new Set();
        for (const finding of this.currentResult.findings) {
            const fp = finding.file_path;
            if (seen.has(fp) || !finding.snippet) continue;
            seen.add(fp);
            // snippet.lines is the full file (context_lines=None)
            const content = finding.snippet.lines.map(l => l.text).join('\n');
            this.editedFileContents.set(fp, content);
            this.originalFileContents.set(fp, content);
        }
    }

    async revalidate() {
        if (!this.currentResult || this.editedFileContents.size === 0) return;
        this.isRevalidating = true;

        // Build files payload: send ALL files (some rules check cross-file references)
        const files = {};
        for (const [fp, content] of this.editedFileContents) {
            files[fp] = content;
        }

        try {
            const response = await fetch('/api/revalidate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    files,
                    config: this.currentResult.config_name || 'default',
                }),
            });
            const result = await response.json();
            if (!response.ok) {
                console.error('Revalidation failed:', result);
                return;
            }

            this.diffFindings(result.findings);
            this.resultsRenderer.renderFindings();
        } catch (error) {
            console.error('Revalidation error:', error);
        } finally {
            this.isRevalidating = false;
        }
    }

    /**
     * Build a stable comparison key for a finding.
     * Strips long quoted strings (code context) from messages so that
     * keys don't shift when surrounding code changes.  Short values
     * like '42' or 'maxCount' are kept as stable identifiers.
     */
    _stableFindingKey(f) {
        const stableMsg = f.message.replace(/'[^']{20,}'/g, "'...'");
        return `${f.rule_id}::${f.file_path}::${stableMsg}`;
    }

    diffFindings(newFindings) {
        // Build set of stable keys from new findings
        const newKeys = new Set();
        for (const f of newFindings) {
            newKeys.add(this._stableFindingKey(f));
        }

        // For each original finding, if its stable key is absent → resolved
        this.resolvedFindings.clear();
        if (!this.currentResult) return;
        for (let i = 0; i < this.currentResult.findings.length; i++) {
            const f = this.currentResult.findings[i];
            if (!newKeys.has(this._stableFindingKey(f))) {
                this.resolvedFindings.add(i);
            }
        }
    }

    /**
     * Reconstruct file content from snippet data for a given file path.
     * Returns the content string or null if no snippet is available.
     */
    getFileContentFromSnippets(filePath) {
        if (!this.currentResult) return null;
        for (const f of this.currentResult.findings) {
            if (f.file_path === filePath && f.snippet && f.snippet.lines) {
                return f.snippet.lines.map(l => l.text).join('\n');
            }
        }
        return null;
    }

    async autofix(findingIndex) {
        if (!this.currentResult || findingIndex < 0 || findingIndex >= this.currentResult.findings.length) return;

        const finding = this.currentResult.findings[findingIndex];
        const filePath = finding.file_path;

        // Get file content: try editedFileContents first, then reconstruct from snippets
        let fileContent = this.editedFileContents.get(filePath);
        if (!fileContent) {
            fileContent = this.getFileContentFromSnippets(filePath);
            if (fileContent) {
                // Populate for future use
                this.editedFileContents.set(filePath, fileContent);
                this.originalFileContents.set(filePath, fileContent);
            }
        }
        if (!fileContent) {
            alert('Cannot auto-fix: file content not available. Try re-uploading.');
            return;
        }

        // Mark as in progress and re-render
        this.autofixInProgress.add(findingIndex);
        this.resultsRenderer.renderFindings();

        try {
            const response = await fetch('/api/autofix', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_path: filePath,
                    file_content: fileContent,
                    finding: {
                        rule_id: finding.rule_id,
                        message: finding.message,
                        line: finding.line,
                        severity: finding.severity,
                    },
                }),
            });

            let data;
            try {
                data = await response.json();
            } catch {
                throw new Error(`Server returned invalid response (HTTP ${response.status})`);
            }

            if (!response.ok) {
                throw new Error(data.detail || 'Autofix failed');
            }

            // Store the fixed content
            this.editedFileContents.set(filePath, data.fixed_content);

            // Update snippet data for all findings in this file so they show the fixed code
            const fixedLines = data.fixed_content.split('\n');
            for (const f of this.currentResult.findings) {
                if (f.file_path === filePath) {
                    f.snippet = {
                        start_line: 1,
                        lines: fixedLines.map((text, i) => ({
                            number: i + 1,
                            text,
                            highlight: (i + 1) === f.line,
                        })),
                    };
                }
            }

            await this.revalidate();
        } catch (error) {
            console.error('Autofix failed:', error.message);
            alert(`Auto-fix failed: ${error.message}`);
        } finally {
            this.autofixInProgress.delete(findingIndex);
            this.resultsRenderer.renderFindings();
        }
    }

    async autofixFile(filePath) {
        if (!this.currentResult) return;

        const maxPasses = 3;
        for (let pass = 0; pass < maxPasses; pass++) {
            // Collect unresolved findings for this file
            const indices = [];
            for (let i = 0; i < this.currentResult.findings.length; i++) {
                if (this.currentResult.findings[i].file_path === filePath && !this.resolvedFindings.has(i)) {
                    indices.push(i);
                }
            }

            if (indices.length === 0) break; // all resolved
            if (pass > 0) {
                console.log(`Fix All pass ${pass + 1}: ${indices.length} findings still unresolved`);
            }

            // Fix sequentially — each fix changes the file content for the next
            for (const idx of indices) {
                await this.autofix(idx);
            }
        }
    }

    async exportAllZip() {
        if (this.editedFileContents.size === 0) return;

        // Build files map: file_path → content
        const files = {};
        for (const [fp, content] of this.editedFileContents) {
            files[fp] = content;
        }

        try {
            const response = await fetch('/api/export-zip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Export failed');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            // Use the original upload name (minus .zip) + _fixed.zip, or generic
            const baseName = this.uploadedFileName
                ? this.uploadedFileName.replace(/\.zip$/i, '')
                : 'fixed_files';
            a.download = `${baseName}_fixed.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Export ZIP failed:', error.message);
            alert(`Export failed: ${error.message}`);
        }
    }

    resetForNewUpload() {
        this.hideAllSections();
        document.getElementById('upload-section').style.display = 'block';
        this.currentResult = null;
        this.findingExplanations.clear();
        this.uploadedFileName = null;
        this.selectedFiles = [];

        // Clear fix state
        this.editedFileContents.clear();
        this.originalFileContents.clear();
        this.resolvedFindings.clear();
        this.autofixInProgress.clear();
        this.isRevalidating = false;

        // Reset file inputs
        const fileInput = document.getElementById('file-input');
        fileInput.value = '';
        const filesInput = document.getElementById('files-input');
        filesInput.value = '';
        
        // Hide selected files list
        document.getElementById('selected-files-list').style.display = 'none';
        
        // Reset AI explain status
        document.getElementById('ai-loading-fab').style.display = 'none';

        // Reset renderers
        this.resultsRenderer.resetForNewUpload();
        
        // Re-render configurations to ensure selected config appears at top
        this.configManager.renderConfigurations();
    }
}

// Initialize the app
const app = new ArcaneAuditorApp();
window.app = app; // Make app globally accessible

// Global functions for HTML onclick handlers
window.resetInterface = function() {
    app.resetForNewUpload();
};

window.downloadResults = function() {
    app.downloadResults();
};

window.toggleTheme = function() {
    app.configManager.toggleTheme();
};

window.toggleContextPanel = function() {
    app.resultsRenderer.toggleContextPanel();
};

window.copyExplainCard = function(cardId) {
    const card = document.getElementById(cardId);
    if (!card) return;

    // Get plain text content (strip HTML)
    const text = card.innerText.replace(/^📋 Copy\s*/, '').replace(/^✅ Copied!\s*/, '');
    navigator.clipboard.writeText(text).then(() => {
        const btn = card.querySelector('.explain-copy-btn');
        btn.textContent = '✅ Copied!';
        setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000);
    });
};

// Results renderer global functions
window.expandAllFiles = function() {
    app.resultsRenderer.expandAllFiles();
};

window.collapseAllFiles = function() {
    app.resultsRenderer.collapseAllFiles();
};

window.updateSeverityFilter = function(value) {
    app.resultsRenderer.updateSeverityFilter(value);
};

window.updateFileTypeFilter = function(value) {
    app.resultsRenderer.updateFileTypeFilter(value);
};

window.updateSortBy = function(value) {
    app.resultsRenderer.updateSortBy(value);
};

window.updateSortFilesBy = function(value) {
    app.resultsRenderer.updateSortFilesBy(value);
};

window.exportAllZip = function() {
    app.exportAllZip();
};

window.autofix = function(findingIndex) {
    app.autofix(findingIndex);
};

window.autofixFile = function(filePath) {
    app.autofixFile(filePath);
};

export default app;
