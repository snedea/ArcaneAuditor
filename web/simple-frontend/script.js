// Simple HTML/JavaScript frontend for Arcane Auditor
// No React, no Node.js dependencies - just vanilla JavaScript

class ArcaneAuditorApp {
    constructor() {
        this.currentResult = null;
        this.filteredFindings = [];
        this.currentFilters = {
            severity: 'all',
            fileType: 'all',
            sortBy: 'severity',
            sortFilesBy: 'alphabetical'
        };
        this.expandedFiles = new Set();
        
        this.initializeEventListeners();
        this.initializeTheme();
    }

    initializeTheme() {
        // Check for saved theme preference or default to light mode
        const savedTheme = localStorage.getItem('arcane-auditor-theme') || 'light';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        
        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Light';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Dark';
        }
        
        // Save preference
        localStorage.setItem('arcane-auditor-theme', theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    initializeEventListeners() {
        // File input change
        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));

        // Drag and drop
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        
        // Button click handler
        const chooseFileBtn = document.getElementById('choose-file-btn');
        chooseFileBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent upload area click
            fileInput.click();
        });
        
        // Upload area click handler (for clicking outside the button)
        uploadArea.addEventListener('click', (e) => {
            // Only trigger if clicking on the upload area itself, not the button
            if (e.target === uploadArea || e.target.classList.contains('upload-content')) {
                fileInput.click();
            }
        });
    }

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
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFileSelect(files[0]);
        }
    }

    handleFileSelect(file) {
        if (!file) return;
        
        if (!file.name.endsWith('.zip')) {
            this.showError('Please select a ZIP file');
            return;
        }

        this.uploadFile(file);
    }

    async uploadFile(file) {
        // Client-side file size validation
        const maxFileSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxFileSize) {
            this.showError(`File too large. Maximum size: ${maxFileSize / (1024 * 1024)}MB`);
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

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

    updateLoadingMessage(message) {
        const loadingSection = document.getElementById('loading-section');
        const loadingText = loadingSection.querySelector('.loading-text');
        if (loadingText) {
            loadingText.textContent = message;
        }
    }

    showLoading() {
        this.hideAllSections();
        document.getElementById('loading-section').style.display = 'block';
    }

    showError(message) {
        this.hideAllSections();
        document.getElementById('error-section').style.display = 'block';
        document.getElementById('error-message').textContent = message;
    }

    showResults() {
        this.hideAllSections();
        document.getElementById('results-section').style.display = 'block';
        this.renderResults();
    }

    hideAllSections() {
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('loading-section').style.display = 'none';
        document.getElementById('error-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
    }

    renderResults() {
        this.renderSummary();
        this.renderFilters();
        this.renderFindings();
    }

    renderSummary() {
        const summary = document.getElementById('summary');
        const result = this.currentResult;
        
        const severityCounts = this.getSeverityCounts(result.findings);
        const fileTypeCounts = this.getFileTypeCounts(result.findings);

        summary.innerHTML = `
            <h4>📈 Summary</h4>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-number summary-number-blue">${result.total_files}</div>
                    <div class="summary-label">Files Analyzed</div>
                </div>
                <div class="summary-item">
                    <div class="summary-number summary-number-purple">${result.total_rules}</div>
                    <div class="summary-label">Rules Executed</div>
                </div>
                <div class="summary-item">
                    <div class="summary-number summary-number-orange">${result.findings.length}</div>
                    <div class="summary-label">Issues Found</div>
                </div>
                <div class="summary-item">
                    <div class="summary-filename">${result.zip_filename}</div>
                    <div class="summary-label">Application</div>
                </div>
            </div>
            
            ${Object.keys(severityCounts).length > 0 ? `
                <div class="severity-section">
                    <h5>Issues by Severity:</h5>
                    <div class="severity-badges">
                        ${Object.entries(severityCounts).map(([severity, count]) => `
                            <div class="severity-badge">
                                ${this.getSeverityIcon(severity)}
                                <span class="severity-count">${count}</span>
                                <span class="severity-name">${severity.toLowerCase()}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${Object.keys(fileTypeCounts).length > 0 ? `
                <div class="severity-section">
                    <h5>Issues by File Type:</h5>
                    <div class="severity-badges">
                        ${Object.entries(fileTypeCounts).map(([fileType, count]) => `
                            <div class="severity-badge">
                                📄
                                <span class="severity-count">${count}</span>
                                <span class="severity-name">${fileType.toLowerCase()}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }

    renderFilters() {
        const filters = document.getElementById('filters');
        const result = this.currentResult;
        
        if (result.findings.length === 0) {
            filters.innerHTML = '';
            return;
        }

        const severityCounts = this.getSeverityCounts(result.findings);
        const fileTypeCounts = this.getFileTypeCounts(result.findings);

        filters.innerHTML = `
            <div class="filter-group">
                <label for="severity-filter">Filter by severity:</label>
                <select id="severity-filter" onchange="app.updateSeverityFilter(this.value)">
                    <option value="all">All (${result.findings.length})</option>
                    ${Object.entries(severityCounts).map(([severity, count]) => `
                        <option value="${severity}">${severity} (${count})</option>
                    `).join('')}
                </select>
            </div>

            <div class="filter-group">
                <label for="file-type-filter">Filter by file type:</label>
                <select id="file-type-filter" onchange="app.updateFileTypeFilter(this.value)">
                    <option value="all">All File Types (${result.findings.length})</option>
                    ${Object.entries(fileTypeCounts).map(([fileType, count]) => `
                        <option value="${fileType}">${fileType} (${count})</option>
                    `).join('')}
                </select>
            </div>

            <div class="filter-group">
                <label for="sort-by">Sort issues by:</label>
                <select id="sort-by" onchange="app.updateSortBy(this.value)">
                    <option value="severity">Severity</option>
                    <option value="line">Line Number</option>
                    <option value="rule">Rule ID</option>
                </select>
            </div>

            <div class="filter-group">
                <label for="sort-files-by">Sort files by:</label>
                <select id="sort-files-by" onchange="app.updateSortFilesBy(this.value)">
                    <option value="alphabetical">Alphabetical</option>
                    <option value="issue-count">Issue Count</option>
                </select>
            </div>
        `;
    }

    renderFindings() {
        const findings = document.getElementById('findings');
        
        if (this.filteredFindings.length === 0) {
            findings.innerHTML = `
                <div class="no-issues">
                    ✅ <strong>No issues found!</strong> Your code looks great!
                </div>
            `;
            return;
        }

        const groupedFindings = this.groupFindingsByFile(this.filteredFindings);
        
        findings.innerHTML = `
            <div class="findings-header">
                <h4>🚨 Issues Found (${this.filteredFindings.length})</h4>
                <div class="findings-actions">
                    <button class="btn btn-secondary" onclick="app.expandAllFiles()">Expand All</button>
                    <button class="btn btn-secondary" onclick="app.collapseAllFiles()">Collapse All</button>
                </div>
            </div>
            
            <div class="findings-content">
                ${Object.entries(groupedFindings).map(([filePath, fileFindings]) => {
                    const isExpanded = this.expandedFiles.has(filePath);
                    const fileName = filePath.split(/[/\\]/).pop() || filePath;
                    const severityCounts = this.getSeverityCounts(fileFindings);
                    
                    return `
                        <div class="file-group">
                            <div class="file-header" onclick="app.toggleFileExpansion('${filePath}')">
                                <div class="file-header-left">
                                    ${isExpanded ? '▼' : '▶'}
                                    📄
                                    <span class="file-name">${fileName}</span>
                                    <span class="file-path">${filePath}</span>
                                </div>
                                <div class="file-header-right">
                                    <span class="file-count">${fileFindings.length} issue${fileFindings.length !== 1 ? 's' : ''}</span>
                                    ${Object.entries(severityCounts).map(([severity, count]) => `
                                        <span class="severity-count-badge ${severity.toLowerCase()}">
                                            ${count} ${severity.toLowerCase()}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                            
                            ${isExpanded ? `
                                <div class="file-findings">
                                    ${this.sortFindingsInGroup(fileFindings).map((finding, index) => `
                                        <div class="finding ${finding.severity.toLowerCase()}">
                                            <div class="finding-header">
                                                ${this.getSeverityIcon(finding.severity)}
                                                <strong>[${finding.rule_id}:${finding.line}]</strong> ${finding.message}
                                            </div>
                                            <div class="finding-details">
                                                <span><strong>Line:</strong> ${finding.line}</span>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    // Filter and sort methods
    updateSeverityFilter(severity) {
        this.currentFilters.severity = severity;
        this.applyFilters();
    }

    updateFileTypeFilter(fileType) {
        this.currentFilters.fileType = fileType;
        this.applyFilters();
    }

    updateSortBy(sortBy) {
        this.currentFilters.sortBy = sortBy;
        this.renderFindings();
    }

    updateSortFilesBy(sortFilesBy) {
        this.currentFilters.sortFilesBy = sortFilesBy;
        this.renderFindings();
    }

    applyFilters() {
        this.filteredFindings = this.currentResult.findings.filter(finding => {
            const severityMatch = this.currentFilters.severity === 'all' || finding.severity === this.currentFilters.severity;
            const fileTypeMatch = this.currentFilters.fileType === 'all' || this.getFileTypeFromPath(finding.file_path) === this.currentFilters.fileType;
            return severityMatch && fileTypeMatch;
        });
        this.renderFindings();
    }

    // Utility methods
    getSeverityCounts(findings) {
        return findings.reduce((acc, finding) => {
            acc[finding.severity] = (acc[finding.severity] || 0) + 1;
            return acc;
        }, {});
    }

    getFileTypeCounts(findings) {
        return findings.reduce((acc, finding) => {
            const fileType = this.getFileTypeFromPath(finding.file_path);
            acc[fileType] = (acc[fileType] || 0) + 1;
            return acc;
        }, {});
    }

    getFileTypeFromPath(filePath) {
        const extension = filePath.split('.').pop()?.toLowerCase() || '';
        switch (extension) {
            case 'pmd': return 'PMD Files';
            case 'pod': return 'POD Files';
            case 'script': return 'Script Files';
            case 'smd': return 'SMD File';
            case 'amd': return 'AMD File';
            default: return 'Other Files';
        }
    }

    getSeverityIcon(severity) {
        switch (severity) {
            case 'SEVERE': return '🚨';
            case 'WARNING': return '⚠️';
            case 'INFO': return 'ℹ️';
            case 'HINT': return '💡';
            default: return 'ℹ️';
        }
    }

    groupFindingsByFile(findings) {
        const grouped = findings.reduce((acc, finding) => {
            const filePath = finding.file_path || 'Unknown';
            if (!acc[filePath]) {
                acc[filePath] = [];
            }
            acc[filePath].push(finding);
            return acc;
        }, {});

        // Sort file groups based on user preference
        const sortedEntries = Object.entries(grouped).sort(([fileA, findingsA], [fileB, findingsB]) => {
            switch (this.currentFilters.sortFilesBy) {
                case 'alphabetical':
                    return fileA.localeCompare(fileB);
                case 'issue-count':
                    return findingsB.length - findingsA.length;
                default:
                    return 0;
            }
        });

        return Object.fromEntries(sortedEntries);
    }

    sortFindingsInGroup(findings) {
        return [...findings].sort((a, b) => {
            switch (this.currentFilters.sortBy) {
                case 'severity':
                    const severityOrder = { SEVERE: 0, WARNING: 1, INFO: 2, HINT: 3 };
                    return severityOrder[a.severity] - severityOrder[b.severity];
                case 'line':
                    return a.line - b.line;
                case 'rule':
                    return a.rule_id.localeCompare(b.rule_id);
                default:
                    return 0;
            }
        });
    }

    toggleFileExpansion(filePath) {
        if (this.expandedFiles.has(filePath)) {
            this.expandedFiles.delete(filePath);
        } else {
            this.expandedFiles.add(filePath);
        }
        this.renderFindings();
    }

    expandAllFiles() {
        const allFiles = Object.keys(this.groupFindingsByFile(this.filteredFindings));
        this.expandedFiles = new Set(allFiles);
        this.renderFindings();
    }

    collapseAllFiles() {
        this.expandedFiles.clear();
        this.renderFindings();
    }

    async downloadResults() {
        try {
            // Get the current job ID from the results
            const jobId = this.currentResult?.job_id;
            if (!jobId) {
                throw new Error('No job ID available for download');
            }

            const response = await fetch(`/api/download/${jobId}`);

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `arcane-auditor-results-${new Date().toISOString().split('T')[0]}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            console.error('Download failed:', error);
            alert('Download failed. Please try again.');
        }
    }

    resetForNewUpload() {
        this.hideAllSections();
        document.getElementById('upload-section').style.display = 'block';
        this.currentResult = null;
        this.filteredFindings = [];
        this.expandedFiles.clear();
        
        // Reset the file input to allow re-uploading the same file
        const fileInput = document.getElementById('file-input');
        fileInput.value = '';
    }
}

// Initialize the app
const app = new ArcaneAuditorApp();

// Global functions for HTML onclick handlers
function resetInterface() {
    app.resetForNewUpload();
}

function downloadResults() {
    app.downloadResults();
}

function toggleTheme() {
    app.toggleTheme();
}
