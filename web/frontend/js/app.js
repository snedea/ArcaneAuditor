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
        this.uploadedFileName = null;
        this.selectedFiles = []; // For multiple file uploads
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

        // Display context awareness panel if available
        if (this.currentResult && this.currentResult.context) {
            this.resultsRenderer.displayContext(this.currentResult.context);
        }

        this.resultsRenderer.renderResults();

        // Show "Explain with AI" button if there are findings
        const explainBtn = document.getElementById('explain-btn');
        if (explainBtn && this.currentResult && this.currentResult.findings.length > 0) {
            explainBtn.style.display = 'inline-flex';
        }

        // Show magical analysis completion if in magic mode
        showMagicalAnalysisComplete(this.currentResult);
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
        document.getElementById('explain-section').style.display = 'none';
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

    async explainWithAI() {
        if (!this.currentResult || !this.currentResult.findings.length) return;

        const explainBtn = document.getElementById('explain-btn');
        const explainSection = document.getElementById('explain-section');
        const explainLoading = document.getElementById('explain-loading');
        const explainError = document.getElementById('explain-error');
        const explainContent = document.getElementById('explain-content');

        // Disable button, show loading
        explainBtn.disabled = true;
        explainBtn.textContent = '🤖 Explaining...';
        explainSection.style.display = 'block';
        explainLoading.style.display = 'flex';
        explainError.style.display = 'none';
        explainContent.innerHTML = '';

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

            explainLoading.style.display = 'none';
            explainContent.innerHTML = this.renderMarkdown(data.explanation);

            // Replace button with "explained" state
            explainBtn.textContent = '✅ Explained';
        } catch (error) {
            explainLoading.style.display = 'none';
            explainError.style.display = 'block';
            document.getElementById('explain-error-message').textContent =
                `Failed to get AI explanation: ${error.message}`;

            // Re-enable button for retry
            explainBtn.disabled = false;
            explainBtn.textContent = '🤖 Retry Explain';
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
            const html = this._markdownToHtml(rawText.trim());
            if (!html) return '';

            // Numbered sections get cards with copy buttons
            if (section.title) {
                const cardId = `explain-card-${idx}`;
                return `<div class="explain-card" id="${cardId}">` +
                    `<button class="explain-copy-btn" onclick="copyExplainCard('${cardId}')" title="Copy to clipboard">📋 Copy</button>` +
                    html +
                    `</div>`;
            }
            // Preamble/summary gets a plain card
            return `<div class="explain-card explain-card-summary">${html}</div>`;
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

    resetForNewUpload() {
        this.hideAllSections();
        document.getElementById('upload-section').style.display = 'block';
        this.currentResult = null;
        this.uploadedFileName = null;
        this.selectedFiles = [];
        
        // Reset file inputs
        const fileInput = document.getElementById('file-input');
        fileInput.value = '';
        const filesInput = document.getElementById('files-input');
        filesInput.value = '';
        
        // Hide selected files list
        document.getElementById('selected-files-list').style.display = 'none';
        
        // Reset explain section
        const explainBtn = document.getElementById('explain-btn');
        if (explainBtn) {
            explainBtn.style.display = 'none';
            explainBtn.disabled = false;
            explainBtn.textContent = '🤖 Explain with AI';
        }
        document.getElementById('explain-section').style.display = 'none';
        document.getElementById('explain-content').innerHTML = '';

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

window.explainWithAI = function() {
    app.explainWithAI();
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

export default app;
