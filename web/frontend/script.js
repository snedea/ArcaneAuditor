// Simple HTML/JavaScript frontend for Arcane Auditor

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
        this.selectedConfig = this.getLastSelectedConfig();
        this.availableConfigs = [];
        this.uploadedFileName = null;
        this.selectedFiles = []; // For multiple file uploads
        this.contextPanelExpanded = false; // Context panel starts collapsed
        
        this.initializeEventListeners();
        this.loadFilterState();
        this.initializeTheme();
        this.loadConfigurations();
    }

    // Filter and sort persistence
    loadFilterState() {
        try {
            const saved = localStorage.getItem('arcaneAuditorFilters');
            if (saved) {
                const filters = JSON.parse(saved);
                this.currentFilters = { ...this.currentFilters, ...filters };
            }
        } catch (e) {
            console.warn('Failed to load filter state:', e);
        }
    }

    saveFilterState() {
        try {
            localStorage.setItem('arcaneAuditorFilters', JSON.stringify(this.currentFilters));
        } catch (e) {
            console.warn('Failed to save filter state:', e);
        }
    }

    initializeTheme() {
        // Check for saved theme preference or default to dark mode
        const savedTheme = localStorage.getItem('arcane-auditor-theme') || 'dark';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        
        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Cast Light';
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Cast Darkness';
        }
        
        // Save preference
        localStorage.setItem('arcane-auditor-theme', theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    getLastSelectedConfig() {
        // Get the last selected config from localStorage, no fallback
        return localStorage.getItem('arcane-auditor-selected-config') || null;
    }

    saveSelectedConfig(configId) {
        // Save the selected config to localStorage
        localStorage.setItem('arcane-auditor-selected-config', configId);
    }

    async loadConfigurations() {
        try {
            const response = await fetch('/api/configs');
            const data = await response.json();
            this.availableConfigs = data.configs;
            
            // If no config is selected, select the first available one
            if (!this.selectedConfig && this.availableConfigs.length > 0) {
                this.selectedConfig = this.availableConfigs[0].id;
                this.saveSelectedConfig(this.selectedConfig);
            }
            
            this.renderConfigurations();
        } catch (error) {
            console.error('Failed to load configurations:', error);
            this.showError('Failed to load configurations. Please refresh the page.');
        }
    }

    renderConfigurations() {
        const configGrid = document.getElementById('config-grid');
        configGrid.innerHTML = '';

        // Group configurations by type
        const configGroups = {
            'Built-in': [],
            'Team': [],
            'Personal': []
        };

        this.availableConfigs.forEach(config => {
            const configType = config.type || 'Built-in';
            if (configGroups[configType]) {
                configGroups[configType].push(config);
            }
        });

        // Sort each group to put selected config first
        Object.keys(configGroups).forEach(groupName => {
            configGroups[groupName].sort((a, b) => {
                if (a.id === this.selectedConfig) return -1;
                if (b.id === this.selectedConfig) return 1;
                return 0;
            });
        });

        // Render each group in original order
        Object.entries(configGroups).forEach(([groupName, configs]) => {
            if (configs.length === 0) return;

            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'config-section';
            
            const sectionTitle = document.createElement('h4');
            sectionTitle.textContent = groupName;
            sectionDiv.appendChild(sectionTitle);

            const groupGrid = document.createElement('div');
            groupGrid.className = 'config-grid';

            configs.forEach(config => {
                const configElement = document.createElement('div');
                configElement.className = 'config-option';
                if (config.id === this.selectedConfig) {
                    configElement.classList.add('selected');
                }
                
                const isSelected = config.id === this.selectedConfig;
                configElement.innerHTML = `
                    <div class="config-type ${config.type?.toLowerCase() || 'built-in'}">${config.type || 'Built-in'}</div>
                    <div class="config-name">${config.name}</div>
                    <div class="config-description">${config.description}</div>
                    <div class="config-meta">
                        <span class="config-rules-count">${config.rules_count} rules</span>
                        <span class="config-performance ${config.performance.toLowerCase()}">${config.performance}</span>
                    </div>
                    ${isSelected ? `
                        <div class="config-actions">
                            <button class="btn btn-secondary config-details-btn" onclick="showConfigBreakdown()">
                                📋 View Details
                            </button>
                        </div>
                    ` : ''}
                `;
                
                configElement.addEventListener('click', () => this.selectConfiguration(config.id));
                groupGrid.appendChild(configElement);
            });

            sectionDiv.appendChild(groupGrid);
            configGrid.appendChild(sectionDiv);
        });
    }

    selectConfiguration(configId) {
        this.selectedConfig = configId;
        this.saveSelectedConfig(configId);
        // Don't re-render configurations to avoid jumping behavior
        // Just update the visual selection state
        this.updateConfigSelection();
    }

    updateConfigSelection() {
        // Update visual selection without re-rendering the entire grid
        const configElements = document.querySelectorAll('.config-option');
        configElements.forEach(element => {
            element.classList.remove('selected');
            // Remove any existing config-actions
            const existingActions = element.querySelector('.config-actions');
            if (existingActions) {
                existingActions.remove();
            }
        });

        // Find and select the clicked config
        const selectedElement = Array.from(configElements).find(element => {
            const configName = element.querySelector('.config-name').textContent;
            const config = this.availableConfigs.find(c => c.name === configName);
            return config && config.id === this.selectedConfig;
        });

        if (selectedElement) {
            selectedElement.classList.add('selected');
            // Add config actions to selected element
            const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
            if (config) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'config-actions';
                actionsDiv.innerHTML = `
                    <button class="btn btn-secondary config-details-btn" onclick="showConfigBreakdown()">
                        📋 View Details
                    </button>
                `;
                selectedElement.appendChild(actionsDiv);
            }
        }
    }

    initializeEventListeners() {
        // ZIP file input change
        const fileInput = document.getElementById('file-input');
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));

        // Multiple files input change
        const filesInput = document.getElementById('files-input');
        filesInput.addEventListener('change', (e) => this.handleMultipleFilesSelect(Array.from(e.target.files)));

        // Drag and drop
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        uploadArea.addEventListener('drop', (e) => this.handleDrop(e));

        // File header clicks for expansion (event delegation)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.file-header')) {
                const fileHeader = e.target.closest('.file-header');
                const filePath = fileHeader.getAttribute('data-file-path');
                if (filePath) {
                    this.toggleFileExpansion(filePath);
                }
            }
        });
        
        // ZIP button click handler
        const chooseFileBtn = document.getElementById('choose-file-btn');
        chooseFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });
        
        // Individual files button click handler
        const chooseFilesBtn = document.getElementById('choose-files-btn');
        chooseFilesBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            filesInput.click();
        });
        
        // Upload files button (for multiple files)
        const uploadFilesBtn = document.getElementById('upload-files-btn');
        uploadFilesBtn.addEventListener('click', () => this.uploadSelectedFiles());
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

        this.uploadedFileName = file.name;
        this.uploadFile(file);
    }

    async uploadFile(file) {
        // Validate configuration is selected
        if (!this.selectedConfig) {
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
        formData.append('files', file); // Changed to 'files' to match API
        formData.append('config', this.selectedConfig);

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
        
        // Display context awareness panel if available
        if (this.currentResult && this.currentResult.context) {
            this.displayContext(this.currentResult.context);
        }
        
        this.renderResults();
        
        // Show magical analysis completion if in magic mode
        if (typeof showMagicalAnalysisComplete === 'function') {
            showMagicalAnalysisComplete(this.currentResult);
        }
    }

    hideAllSections() {
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('loading-section').style.display = 'none';
        document.getElementById('error-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('context-section').style.display = 'none';
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

        summary.innerHTML = `
            <h4>📈 Summary</h4>
            ${this.uploadedFileName ? `
                <div class="summary-filename-section">
                    <div class="summary-filename">📁 ${this.uploadedFileName}</div>
                    <div class="summary-filename-label">Analyzed Application</div>
                </div>
            ` : ''}
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-number summary-number-blue">${result.summary?.total_findings || result.findings.length}</div>
                    <div class="summary-label">Issues Found</div>
                </div>
                <div class="summary-item">
                    <div class="summary-number summary-number-purple">${result.summary?.rules_executed || 0}</div>
                    <div class="summary-label">Rules Enabled</div>
                </div>
                <div class="summary-item magic-summary-card action">
                    <div class="count">${result.summary?.by_severity?.action || 0}</div>
                    <div class="label">
                        <span class="icon">${this.getSeverityIcon('ACTION')}</span> Actions
                    </div>
                </div>
                <div class="summary-item magic-summary-card advice">
                    <div class="count">${result.summary?.by_severity?.advice || 0}</div>
                    <div class="label">
                        <span class="icon">${this.getSeverityIcon('ADVICE')}</span> Advices
                    </div>
                </div>
            </div>
        `;
    }

    renderFilters() {
        // Filters are now rendered inline with findings, so this method is no longer needed
        // The filters are rendered directly in renderFindings()
        return;
    }

    renderFindings() {
        const findings = document.getElementById('findings');
        
        if (this.filteredFindings.length === 0) {
            findings.innerHTML = `
                <div class="no-issues">
                    ✅ <strong>No issues found!</strong> Your code is magical!
                </div>
            `;
            return;
        }

        const groupedFindings = this.groupFindingsByFile(this.filteredFindings);
        
        findings.innerHTML = `
            <div class="findings-header">
                <div class="expand-collapse-buttons">
                    <button class="btn btn-secondary" onclick="app.expandAllFiles()">Expand All</button>
                    <button class="btn btn-secondary" onclick="app.collapseAllFiles()">Collapse All</button>
                </div>
                <div class="filters">
                    <div class="filter-group">
                        <div class="micro-label">Severity</div>
                        <select id="severity-filter" onchange="app.updateSeverityFilter(this.value)">
                            <option value="all" ${this.currentFilters.severity === 'all' ? 'selected' : ''}>All (${this.currentResult.findings.length})</option>
                            ${this.getOrderedSeverityEntries(this.getSeverityCounts(this.currentResult.findings)).map(([severity, count]) => `
                                <option value="${severity}" ${this.currentFilters.severity === severity ? 'selected' : ''}>${severity} (${count})</option>
                            `).join('')}
                        </select>
                    </div>
                    <div class="filter-group">
                        <div class="micro-label">File Type</div>
                        <select id="file-type-filter" onchange="app.updateFileTypeFilter(this.value)">
                            <option value="all" ${this.currentFilters.fileType === 'all' ? 'selected' : ''}>All Types (${this.currentResult.findings.length})</option>
                            ${Object.entries(this.getFileTypeCounts(this.currentResult.findings)).map(([fileType, count]) => `
                                <option value="${fileType}" ${this.currentFilters.fileType === fileType ? 'selected' : ''}>${fileType} (${count})</option>
                            `).join('')}
                        </select>
                    </div>
                    <div class="filter-group">
                        <div class="micro-label">File Order</div>
                        <select id="sort-files-by" onchange="app.updateSortFilesBy(this.value)">
                            <option value="alphabetical" ${this.currentFilters.sortFilesBy === 'alphabetical' ? 'selected' : ''}>Files</option>
                            <option value="issue-count" ${this.currentFilters.sortFilesBy === 'issue-count' ? 'selected' : ''}>Issue Count</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <div class="micro-label">Issue Order</div>
                        <select id="sort-by" onchange="app.updateSortBy(this.value)">
                            <option value="severity" ${this.currentFilters.sortBy === 'severity' ? 'selected' : ''}>Issues</option>
                            <option value="line" ${this.currentFilters.sortBy === 'line' ? 'selected' : ''}>Line Number</option>
                            <option value="rule" ${this.currentFilters.sortBy === 'rule' ? 'selected' : ''}>Rule ID</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="findings-content">
                ${Object.entries(groupedFindings).map(([filePath, fileFindings]) => {
                    const isExpanded = this.expandedFiles.has(filePath);
                    const fileName = filePath.split(/[/\\]/).pop() || filePath;
                    const severityCounts = this.getSeverityCounts(fileFindings);
                    
                    return `
                        <div class="file-group">
                            <div class="file-header" data-file-path="${filePath.replace(/"/g, '&quot;')}">
                                <div class="file-header-left">
                                    ${isExpanded ? '▼' : '▶'}
                                    📄
                                    <div class="file-info">
                                        <span class="file-name">${fileName}</span>
                                    </div>
                                </div>
                                <div class="file-header-right">
                                    ${this.currentFilters.severity === 'all' ? `
                                        <div class="file-count-badge">
                                            ${fileFindings.length} issue${fileFindings.length !== 1 ? 's' : ''}
                                        </div>
                                    ` : ''}
                                    <div class="severity-badges">
                                        ${this.getOrderedSeverityEntries(severityCounts).map(([severity, count]) => {
                                            // Only show severity badges when severity filter is 'all' or matches this severity
                                            if (this.currentFilters.severity === 'all' || this.currentFilters.severity === severity) {
                                                return `
                                                    <span class="severity-count-badge ${severity.toLowerCase()}">
                                                        ${count} ${severity.toLowerCase()}
                                                    </span>
                                                `;
                                            }
                                            return '';
                                        }).join('')}
                                    </div>
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
        this.saveFilterState();
        this.applyFilters();
    }

    updateFileTypeFilter(fileType) {
        this.currentFilters.fileType = fileType;
        this.saveFilterState();
        this.applyFilters();
    }

    updateSortBy(sortBy) {
        this.currentFilters.sortBy = sortBy;
        this.saveFilterState();
        this.renderFindings();
    }

    updateSortFilesBy(sortFilesBy) {
        this.currentFilters.sortFilesBy = sortFilesBy;
        this.saveFilterState();
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
        const counts = findings.reduce((acc, finding) => {
            const severity = finding.severity || 'unknown';
            acc[severity] = (acc[severity] || 0) + 1;
            return acc;
        }, {});
        
        // Define severity order: ISSUES, ACTION, ADVICE (uppercase to match backend)
        const severityOrder = ['ISSUES', 'ACTION', 'ADVICE'];
        
        // Create ordered object
        const orderedCounts = {};
        severityOrder.forEach(severity => {
            if (counts[severity]) {
                orderedCounts[severity] = counts[severity];
            }
        });
        
        // Add any other severities not in the predefined order
        Object.keys(counts).forEach(severity => {
            if (!severityOrder.includes(severity)) {
                orderedCounts[severity] = counts[severity];
            }
        });
        
        return orderedCounts;
    }

    getOrderedSeverityEntries(severityCounts) {
        // Define severity order: ISSUES, ACTION, ADVICE (uppercase to match backend)
        const severityOrder = ['ISSUES', 'ACTION', 'ADVICE'];
        
        // Create ordered array of entries
        const orderedEntries = [];
        severityOrder.forEach(severity => {
            if (severityCounts[severity]) {
                orderedEntries.push([severity, severityCounts[severity]]);
            }
        });
        
        // Add any other severities not in the predefined order
        Object.entries(severityCounts).forEach(([severity, count]) => {
            if (!severityOrder.includes(severity)) {
                orderedEntries.push([severity, count]);
            }
        });
        
        return orderedEntries;
    }

    getFileTypeCounts(findings) {
        return findings.reduce((acc, finding) => {
            const fileType = this.getFileTypeFromPath(finding.file_path);
            acc[fileType] = (acc[fileType] || 0) + 1;
            return acc;
        }, {});
    }

    getFileTypeFromPath(filePath) {
        if (!filePath || typeof filePath !== 'string') {
            return 'Unknown';
        }
        const extension = filePath.split('.').pop()?.toLowerCase() || '';
        switch (extension) {
            case 'pmd': return 'PMD';
            case 'pod': return 'POD';
            case 'script': return 'Script';
            case 'smd': return 'SMD';
            case 'amd': return 'AMD';
            default: return 'Other';
        }
    }

    getSeverityIcon(severity) {
        switch (severity) {
            case 'ACTION': return '🚨';
            case 'ADVICE': return 'ℹ️';
            default: return 'ℹ️';
        }
    }

    groupFindingsByFile(findings) {
        const grouped = findings.reduce((acc, finding) => {
            const filePath = finding.file_path || 'Unknown';
            // Remove job ID prefix if present (format: uuid_filename.ext)
            const cleanFilePath = filePath.replace(/^[a-f0-9-]+_/, '');
            if (!acc[cleanFilePath]) {
                acc[cleanFilePath] = [];
            }
            acc[cleanFilePath].push(finding);
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
                    const severityOrder = { ACTION: 0, ADVICE: 1 };
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

    handleMultipleFilesSelect(files) {
        // Add selected files to the array
        this.selectedFiles = files;
        this.renderSelectedFiles();
    }

    renderSelectedFiles() {
        const listContainer = document.getElementById('selected-files-list');
        const listContent = document.getElementById('files-list-content');
        
        if (this.selectedFiles.length === 0) {
            listContainer.style.display = 'none';
            return;
        }
        
        listContainer.style.display = 'block';
        listContent.innerHTML = '';
        
        this.selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <span class="file-item-name">${file.name}</span>
                <button class="file-item-remove" onclick="app.removeSelectedFile(${index})" title="Remove file">×</button>
            `;
            listContent.appendChild(fileItem);
        });
    }

    removeSelectedFile(index) {
        this.selectedFiles.splice(index, 1);
        this.renderSelectedFiles();
        
        // Reset the file input
        const filesInput = document.getElementById('files-input');
        filesInput.value = '';
    }

    async uploadSelectedFiles() {
        if (this.selectedFiles.length === 0) {
            this.showError('Please select at least one file');
            return;
        }
        
        // Validate configuration is selected
        if (!this.selectedConfig) {
            this.showError('Please select a configuration before uploading files.');
            return;
        }
        
        const formData = new FormData();
        this.selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('config', this.selectedConfig);
        
        try {
            this.showLoading();
            this.updateLoadingMessage('Uploading files...');
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }
            
            const data = await response.json();
            this.updateLoadingMessage('Files uploaded. Analyzing...');
            this.pollJobStatus(data.job_id);
            
        } catch (error) {
            this.showError(`Upload failed: ${error.message}`);
        }
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        
        // Check if it's a single ZIP file
        if (files.length === 1 && files[0].name.toLowerCase().endsWith('.zip')) {
            this.handleFileSelect(files[0]);
        } else {
            // Multiple files or individual files
            const validExtensions = ['.pmd', '.pod', '.amd', '.smd', '.script'];
            const validFiles = files.filter(file => {
                return validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
            });
            
            if (validFiles.length > 0) {
                this.handleMultipleFilesSelect(validFiles);
            } else {
                this.showError('Please drop valid files (.zip or .pmd, .pod, .amd, .smd, .script)');
            }
        }
    }

    displayContext(contextData) {
        if (!contextData) return;
        
        const contextSection = document.getElementById('context-section');
        const contextContent = document.getElementById('context-content');
        const contextIcon = document.getElementById('context-icon');
        const contextTitleText = document.getElementById('context-title-text');
        
        // Determine if analysis is complete or partial
        const isComplete = contextData.context_status === 'complete';
        
        // Update icon and title with magical flair
        if (isComplete) {
            contextIcon.textContent = '✨';
            contextTitleText.textContent = 'Evaluation ✦';
        } else {
            contextIcon.textContent = '🌙';
            contextTitleText.textContent = 'Divination Incomplete';
        }
        
        // Add status badge to the header
        const contextHeader = document.querySelector('.context-header');
        if (contextHeader) {
            // Remove any existing status badge
            const existingBadge = contextHeader.querySelector('.context-header-badge');
            if (existingBadge) {
                existingBadge.remove();
            }
            
            // Determine badge text based on context
            let badgeText = '';
            if (isComplete) {
                badgeText = '✅ Complete';
            } else {
                // Check if any rules were skipped
                const hasSkippedRules = contextData.impact && 
                    ((contextData.impact.rules_not_executed && contextData.impact.rules_not_executed.length > 0) ||
                     (contextData.impact.rules_partially_executed && contextData.impact.rules_partially_executed.length > 0));
                
                if (hasSkippedRules) {
                    badgeText = '⚠️ Partial';
                } else {
                    badgeText = '⚠️ Partial';
                }
            }
            
            // Add new status badge
            const statusBadge = document.createElement('div');
            statusBadge.className = `context-header-badge ${isComplete ? 'complete' : 'partial'}`;
            statusBadge.textContent = badgeText;
            contextHeader.appendChild(statusBadge);
        }
        
        // Build context content HTML (no duplicate badge)
        let html = '';
        
        // Files examined (magical terminology)
        if (contextData.files_analyzed && contextData.files_analyzed.length > 0) {
            html += `
                <div class="context-files">
                    <h4>✅ Files Examined (${contextData.files_analyzed.length})</h4>
                    <div class="context-files-list">
                        ${contextData.files_analyzed.map(file => {
                            // Remove job ID prefix if present (format: uuid_filename.ext)
                            const cleanFileName = file.replace(/^[a-f0-9-]+_/, '');
                            const extension = cleanFileName.split('.').pop().toUpperCase();
                            const icon = extension === 'PMD' ? '📄' : 
                                       extension === 'SMD' ? '⚙️' : 
                                       extension === 'AMD' ? '🏗️' : 
                                       extension === 'POD' ? '🎨' : 
                                       extension === 'SCRIPT' ? '📜' : '📄';
                            return `
                                <div class="context-file-item">
                                    <span class="file-icon">${icon}</span>
                                    <span class="file-name">${cleanFileName}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        // Configuration used
        if (this.currentResult && this.currentResult.config_name) {
            html += `
                <div class="context-config">
                    <h4>⚙️ Configuration Used</h4>
                    <div class="context-config-item">
                        <span class="config-icon">🔧</span>
                        <span class="config-name">${this.currentResult.config_name}</span>
                    </div>
                </div>
            `;
        }
        
        // Missing files (renamed and restructured)
        if (contextData.files_missing && contextData.files_missing.length > 0) {
            // Only show AMD and SMD as "needed for full validation"
            const requiredFiles = contextData.files_missing.filter(type => ['AMD', 'SMD'].includes(type));
            
            if (requiredFiles.length > 0) {
                html += `
                    <div class="context-missing">
                        <h4>⚠️ Missing Artifacts</h4>
                        <div class="context-missing-items">
                `;
                
                // Show only required files
                requiredFiles.forEach(type => {
                    html += `<span class="context-missing-item required">${type}</span>`;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
        }
        
        // Rules not invoked (magical terminology)
        if (contextData.impact) {
            const hasNotExecuted = contextData.impact.rules_not_executed && contextData.impact.rules_not_executed.length > 0;
            const hasPartiallyExecuted = contextData.impact.rules_partially_executed && contextData.impact.rules_partially_executed.length > 0;
            
            // Rules Not Invoked section
            if (hasNotExecuted) {
                html += `
                    <div class="context-impact">
                        <h4>📜 Rules Not Invoked</h4>
                        <p class="context-impact-subtitle">Some validations could not be cast due to missing components.</p>
                        <div class="context-impact-list">
                `;
                
                contextData.impact.rules_not_executed.forEach(rule => {
                    html += `
                        <div class="context-impact-item">
                            <strong>🚫 ${rule.rule}</strong>
                            <span>Skipped — missing required ${rule.reason.toLowerCase().replace('requires ', '').replace(' file', '')} file.</span>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
            
            // Rules Partially Invoked section
            if (hasPartiallyExecuted) {
                html += `
                    <div class="context-impact context-impact-partial">
                        <h4>⚠️ Rules Partially Invoked</h4>
                        <p class="context-impact-subtitle">Some validations were partially cast due to missing components.</p>
                        <div class="context-impact-list">
                `;
                
                contextData.impact.rules_partially_executed.forEach(rule => {
                    html += `
                        <div class="context-impact-item">
                            <strong>⚠️ ${rule.rule}</strong>
                            <span>Skipped: ${rule.skipped_checks.join(', ')} — ${rule.reason.toLowerCase()}</span>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
        }
        
        // Tip (magical guidance)
        if (!isComplete) {
            const requiredFiles = (contextData.files_missing || []).filter(type => ['AMD', 'SMD'].includes(type));
            
            let tipText = '';
            if (requiredFiles.length > 0) {
                tipText = `Add these components to complete the circle: ${requiredFiles.join(' and ')}.`;
            } else {
                tipText = 'Add missing components to complete the divination.';
            }
            
            html += `
                <div class="context-tip">
                    <p>💡 <strong>Tip:</strong> ${tipText}</p>
                </div>
            `;
        }
        
        contextContent.innerHTML = html;
        contextSection.style.display = 'block';
        
        // Set initial collapsed state
        this.contextPanelExpanded = false;
        const contextToggle = document.getElementById('context-toggle');
        contextToggle.classList.remove('expanded');
    }

    toggleContextPanel() {
        const contextContent = document.getElementById('context-content');
        const contextToggle = document.getElementById('context-toggle');
        
        this.contextPanelExpanded = !this.contextPanelExpanded;
        
        if (this.contextPanelExpanded) {
            contextContent.classList.remove('collapsed');
            contextToggle.classList.add('expanded');
        } else {
            contextContent.classList.add('collapsed');
            contextToggle.classList.remove('expanded');
        }
    }

    resetForNewUpload() {
        this.hideAllSections();
        document.getElementById('upload-section').style.display = 'block';
        this.currentResult = null;
        this.filteredFindings = [];
        this.expandedFiles.clear();
        this.uploadedFileName = null;
        this.selectedFiles = [];
        this.contextPanelExpanded = true;
        
        // Reset file inputs
        const fileInput = document.getElementById('file-input');
        fileInput.value = '';
        const filesInput = document.getElementById('files-input');
        filesInput.value = '';
        
        // Hide selected files list
        document.getElementById('selected-files-list').style.display = 'none';
        
        // Re-render configurations to ensure selected config appears at top
        this.renderConfigurations();
    }
}

// Initialize the app
const app = new ArcaneAuditorApp();
window.app = app; // Make app globally accessible

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

function toggleContextPanel() {
    app.toggleContextPanel();
}

// Configuration Breakdown Functions
function showConfigBreakdown() {
    const modal = document.getElementById('config-breakdown-modal');
    const content = document.getElementById('config-breakdown-content');
    
    if (!app.selectedConfig) {
        alert('Please select a configuration first');
        return;
    }
    
    const config = app.availableConfigs.find(c => c.id === app.selectedConfig);
    if (!config) {
        alert('Configuration not found');
        return;
    }
    
    const rules = config.rules || {};
    const enabledRules = Object.entries(rules).filter(([_, ruleConfig]) => ruleConfig.enabled);
    const disabledRules = Object.entries(rules).filter(([_, ruleConfig]) => !ruleConfig.enabled);
    
    let html = `
        <div class="config-breakdown-section">
            <h4>📊 Configuration: ${config.name}</h4>
            <div class="config-summary-grid">
                <div class="summary-card enabled">
                    <div class="summary-number">${enabledRules.length}</div>
                    <div class="summary-label">Enabled Rules</div>
                </div>
                <div class="summary-card disabled">
                    <div class="summary-number">${disabledRules.length}</div>
                    <div class="summary-label">Disabled Rules</div>
                </div>
                <div class="summary-card total">
                    <div class="summary-number">${Object.keys(rules).length}</div>
                    <div class="summary-label">Total Rules</div>
                </div>
            </div>
        </div>
    `;
    
    if (enabledRules.length > 0) {
        html += `
            <div class="config-breakdown-section">
                <h4>✅ Enabled Rules</h4>
                <div class="rule-breakdown">
        `;
        
        enabledRules.forEach(([ruleName, ruleConfig]) => {
            const severity = ruleConfig.severity_override || 'ADVICE';
            const customSettings = ruleConfig.custom_settings || {};
            const settingsText = Object.keys(customSettings).length > 0 
                ? JSON.stringify(customSettings, null, 2) 
                : '';
            
            html += `
                <div class="rule-item enabled">
                    <div class="rule-header-row">
                        <div class="rule-name">${ruleName}</div>
                        <span class="rule-status-badge enabled">✓ Enabled</span>
                    </div>
                    <div class="rule-description">Severity: ${severity}</div>
                    ${settingsText ? `
                        <div class="rule-settings">
                            <div class="settings-label">Custom Settings:</div>
                            <pre class="settings-json">${settingsText}</pre>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    if (disabledRules.length > 0) {
        html += `
            <div class="config-breakdown-section">
                <h4>❌ Disabled Rules</h4>
                <div class="rule-breakdown">
        `;
        
        disabledRules.forEach(([ruleName, ruleConfig]) => {
            html += `
                <div class="rule-item disabled">
                    <div class="rule-header-row">
                        <div class="rule-name">${ruleName}</div>
                        <span class="rule-status-badge disabled">✗ Disabled</span>
                    </div>
                    <div class="rule-description">Disabled</div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    content.innerHTML = html;
    
    modal.style.display = 'flex';
}

function hideConfigBreakdown() {
    const modal = document.getElementById('config-breakdown-modal');
    modal.style.display = 'none';
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('config-breakdown-modal');
    if (event.target === modal) {
        hideConfigBreakdown();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideConfigBreakdown();
    }
});

// ⚡️ ARCANE MODE: THE GRAND RITUAL EDITION ⚡️
// Magical functionality for the living spellbook

// 🌠 Particle Wisps of Energy
function summonParticles(count = 20) {
    for (let i = 0; i < count; i++) {
        const spark = document.createElement('div');
        spark.className = 'arcane-spark';
        document.body.appendChild(spark);
        animateSpark(spark);
    }
}

function animateSpark(el) {
    const x = Math.random() * window.innerWidth;
    const y = Math.random() * window.innerHeight;
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
    el.style.animationDuration = `${5 + Math.random() * 5}s`;
    el.addEventListener('animationend', () => el.remove());
}

// 🌈 Arcane Cursor Trail
let cursorTrailEnabled = false;

function enableCursorTrail() {
    if (cursorTrailEnabled) return;
    cursorTrailEnabled = true;
    
    document.addEventListener('mousemove', createWisp);
}

function disableCursorTrail() {
    cursorTrailEnabled = false;
    document.removeEventListener('mousemove', createWisp);
}

function createWisp(e) {
    const wisp = document.createElement('div');
    wisp.className = 'wisp';
    wisp.style.left = `${e.pageX}px`;
    wisp.style.top = `${e.pageY}px`;
    document.body.appendChild(wisp);
    setTimeout(() => wisp.remove(), 1000);
}

// 🌌 Dynamic Constellation Effects
function createConstellationLines() {
    if (!document.body.classList.contains('magic-mode')) return;
    
    const canvas = document.createElement('canvas');
    canvas.id = 'constellation-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '1';
    canvas.style.opacity = '0.3';
    
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const stars = [];
    
    // Create star positions
    for (let i = 0; i < 50; i++) {
        stars.push({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            brightness: Math.random()
        });
    }
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    function animateConstellation() {
        if (!document.body.classList.contains('magic-mode')) {
            canvas.remove();
            return;
        }
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Update and draw stars
        stars.forEach(star => {
            star.x += star.vx;
            star.y += star.vy;
            star.brightness += (Math.random() - 0.5) * 0.02;
            star.brightness = Math.max(0.3, Math.min(1, star.brightness));
            
            // Wrap around screen
            if (star.x < 0) star.x = canvas.width;
            if (star.x > canvas.width) star.x = 0;
            if (star.y < 0) star.y = canvas.height;
            if (star.y > canvas.height) star.y = 0;
            
            // Draw star
            ctx.beginPath();
            ctx.arc(star.x, star.y, 1, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(234, 163, 66, ${star.brightness * 0.6})`;
            ctx.fill();
        });
        
        // Draw constellation lines
        for (let i = 0; i < stars.length; i++) {
            for (let j = i + 1; j < stars.length; j++) {
                const dx = stars[i].x - stars[j].x;
                const dy = stars[i].y - stars[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 150) {
                    const opacity = (1 - distance / 150) * 0.3;
                    ctx.beginPath();
                    ctx.moveTo(stars[i].x, stars[i].y);
                    ctx.lineTo(stars[j].x, stars[j].y);
                    ctx.strokeStyle = `rgba(117, 106, 162, ${opacity})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
        
        requestAnimationFrame(animateConstellation);
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    animateConstellation();
}

function removeConstellationLines() {
    const canvas = document.getElementById('constellation-canvas');
    if (canvas) {
        canvas.remove();
    }
}

// 🪄 Magic Mode Toggle
function toggleMagicMode() {
    const body = document.body;
    
    if (body.classList.contains('magic-mode')) {
        // Dispel Magic
        body.classList.remove('magic-mode');
        
        // Clean up magical effects
        document.querySelectorAll('.arcane-spark, .wisp').forEach(el => el.remove());
        disableCursorTrail();
        removeConstellationLines();
        
        console.log("%c🪄 The Weave settles... Arcane Mode dispelled.", "color:#756AA2; font-weight:bold");
    } else {
        // Invoke Magic
        body.classList.add('magic-mode');
        
        // Activate magical effects
        summonParticles();
        enableCursorTrail();
        createConstellationLines();
        
        console.log("%c✨ The Weave stirs... Arcane Mode enabled.", "color:#EAA342; font-weight:bold");
        
        // Show magical achievement toast
        showArcaneToast("✨ The Grand Ritual begins... The Weave awakens!");
    }
}

// 🔔 Arcane Achievement Toasts
function showArcaneToast(message) {
    const toast = document.createElement('div');
    toast.className = 'arcane-toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 🪄 Keyboard Incantation (Konami-style combo)
const spell = ['Alt', 'Shift', 'M']; // "Alt + Shift + M" for Magic
let buffer = [];

document.addEventListener('keydown', e => {
    buffer.push(e.key);
    if (buffer.length > spell.length) {
        buffer.shift();
    }
    
    if (buffer.slice(-spell.length).join('') === spell.join('')) {
        toggleMagicMode();
        buffer = [];
    }
});

// Initialize Magic Mode functionality
document.addEventListener('DOMContentLoaded', function() {
    // Magic Mode initialization - no initial greeting for normal users
});

// Enhanced analysis completion with magical flair
function showMagicalAnalysisComplete(result) {
    if (document.body.classList.contains('magic-mode')) {
        const totalFindings = result.findings.length;
        const actionCount = result.summary?.by_severity?.action || 0;
        const adviceCount = result.summary?.by_severity?.advice || 0;
        
        let message = `✨ Divination Complete — The Weave reveals ${totalFindings} portents`;
        if (actionCount > 0) {
            message += ` (${actionCount} urgent omens)`;
        }
        if (adviceCount > 0) {
            message += ` (${adviceCount} wise counsel)`;
        }
        
        showArcaneToast(message);
        
        // Summon extra particles for celebration
        setTimeout(() => summonParticles(10), 500);
    }
}