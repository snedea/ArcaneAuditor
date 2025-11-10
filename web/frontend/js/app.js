// Main application orchestration for Arcane Auditor web interface

import { ConfigManager } from './config-manager.js';
import { ResultsRenderer } from './results-renderer.js';
import { downloadResults, getLastSortBy, getLastSortFilesBy } from './utils.js';
import { showMagicalAnalysisComplete } from './magic-mode.js';
import { DialogManager } from './dialog-manager.js';

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
        
        this.updatePreferences = {
            enabled: false,
            first_run_completed: false
        };
        this.updatePreferencesPromise = null;
        this.versionRetryAttempts = 0;
        this.versionRetryTimer = null;

        // Initialize managers
        this.configManager = new ConfigManager(this);
        this.resultsRenderer = new ResultsRenderer(this);
        
        this.initializeEventListeners();
        this.configManager.initializeTheme();
        this.configManager.loadConfigurations();
        // Load update preferences then version asynchronously after initialization
        this.updatePreferencesPromise = this.loadUpdatePreferences();
        this.updatePreferencesPromise.catch(err => console.error('Failed to load update preferences:', err));
        this.loadVersion().catch(err => console.error('Failed to load version:', err));

        if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
            window.addEventListener('pywebviewready', () => {
                try {
                    this.updatePreferencesPromise = this.loadUpdatePreferences();
                    this.updatePreferencesPromise
                        .catch(err => console.error('Failed to refresh update preferences:', err))
                        .finally(() => {
                            this.loadVersion().catch(err => console.error('Failed to refresh version:', err));
                        });
                } catch (error) {
                    console.error('pywebviewready handler error:', error);
                }
            }, { once: false });
        }
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

    async ensureUpdatePreferencesLoaded() {
        if (this.updatePreferencesPromise) {
            try {
                await this.updatePreferencesPromise;
            } catch (error) {
                console.error('Failed waiting for update preferences:', error);
            } finally {
                this.updatePreferencesPromise = null;
            }
        }
    }

    async loadUpdatePreferences() {
        try {
            let data = null;
            const hasDesktopBridge = (
                window.pywebview &&
                window.pywebview.api &&
                typeof window.pywebview.api.get_update_preferences === 'function'
            );

            if (hasDesktopBridge) {
                data = await window.pywebview.api.get_update_preferences();
            } else {
                const response = await fetch('/api/update-preferences');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                data = await response.json();
            }

            if (!data || typeof data !== 'object') {
                throw new Error('Invalid update preferences payload');
            }

            if (typeof data.enabled === 'boolean') {
                this.updatePreferences.enabled = data.enabled;
            }
            if (typeof data.first_run_completed === 'boolean') {
                this.updatePreferences.first_run_completed = data.first_run_completed;
            }
        } catch (error) {
            console.error('Failed to load update preferences:', error);
            // Keep defaults (disabled) if we can't load preferences
            this.updatePreferences.enabled = false;
        }
    }

    resetVersionIndicator() {
        const versionElement = document.getElementById('version-info');
        if (!versionElement) return;
        versionElement.classList.remove('update-available', 'pulse');
        versionElement.style.cursor = 'default';
        versionElement.onclick = null;
    }

    hideAllSections() {
        document.getElementById('upload-section').style.display = 'none';
        document.getElementById('loading-section').style.display = 'none';
        document.getElementById('error-section').style.display = 'none';
        document.getElementById('results-section').style.display = 'none';
        document.getElementById('context-section').style.display = 'none';
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
            const message = 'Please select a file or files to analyze';
            if (DialogManager && typeof DialogManager.showAlert === 'function') {
                DialogManager.showAlert(message);
            } else {
                alert(message);
            }
            return;
        }

        if (!this.configManager.selectedConfig) {
            const message = 'Please select a configuration';
            if (DialogManager && typeof DialogManager.showAlert === 'function') {
                DialogManager.showAlert(message);
            } else {
                alert(message);
            }
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
        const result = await downloadResults(this.currentResult);
        
        // Show toast notification on success
        if (result && result.success) {
            if (window.pywebview) {
                // Desktop app - show file path in toast
                this.showToast(`✅ File saved to Downloads folder: ${result.filename}`, 'success');
            } else {
                // Web browser - generic success message
                this.showToast('✅ Download complete!', 'success');
            }
        } else if (result && !result.success) {
            // Show error toast if download failed
            this.showToast('❌ Download failed. Please try again.', 'error');
        }
    }

    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `arcane-toast ${type}`;
        toast.textContent = message;
        
        // Add to body
        document.body.appendChild(toast);
        
        // Trigger animation by adding 'show' class after a brief delay
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove after 4 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
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
        
        // Reset renderers
        this.resultsRenderer.resetForNewUpload();
        
        // Re-render configurations to ensure selected config appears at top
        this.configManager.renderConfigurations();
    }

    async loadVersion() {
        await this.ensureUpdatePreferencesLoaded();
        if (this.versionRetryTimer) {
            clearTimeout(this.versionRetryTimer);
            this.versionRetryTimer = null;
        }

        try {
            let data = null;
            const hasDesktopBridge = (
                window.pywebview &&
                window.pywebview.api &&
                typeof window.pywebview.api.get_health_status === 'function'
            );

            if (hasDesktopBridge) {
                data = await window.pywebview.api.get_health_status();
            } else {
                const response = await fetch('/api/health');
                data = await response.json();
            }

            if (!data || typeof data !== 'object') {
                throw new Error('Invalid health payload');
            }

            if (data.version) {
                const versionElement = document.getElementById('version-info');
                if (versionElement) {
                    versionElement.textContent = `v${data.version}`;
                    versionElement.title = `Arcane Auditor version ${data.version}`;
                    this.resetVersionIndicator();
                }

                const updateInfo = data.update_info;
                if (updateInfo && updateInfo.update_available) {
                    this.updateVersionDisplay(updateInfo);
                    this.versionRetryAttempts = 0;
                } else if (hasDesktopBridge && !updateInfo) {
                    if (this.scheduleVersionRetry()) {
                        return;
                    }
                    this.versionRetryAttempts = 0;
                } else {
                    this.versionRetryAttempts = 0;
                }
            }
        } catch (error) {
            console.error('Failed to load version:', error);
            const hasDesktopBridge = (
                window.pywebview &&
                window.pywebview.api &&
                typeof window.pywebview.api.get_health_status === 'function'
            );
            if (hasDesktopBridge && this.scheduleVersionRetry()) {
                return;
            }
            // If fetch fails, show "v?" to indicate version unavailable
            const versionElement = document.getElementById('version-info');
            if (versionElement) {
                versionElement.textContent = 'v?';
                versionElement.title = 'Version unavailable';
                this.resetVersionIndicator();
            }
        }
    }
    
    scheduleVersionRetry() {
        const maxAttempts = 5;
        if (this.versionRetryAttempts >= maxAttempts) {
            return false;
        }

        this.versionRetryAttempts += 1;

        const delay = 1000 * this.versionRetryAttempts;
        this.versionRetryTimer = setTimeout(() => {
            this.versionRetryTimer = null;
            this.loadVersion().catch(err => {
                console.error('Retrying loadVersion failed:', err);
            });
        }, delay);

        return true;
    }

    updateVersionDisplay(updateInfo) {
        // Update version indicator to show update available
        const versionElement = document.getElementById('version-info');
        if (!versionElement) return;
        
        const latestVersion = updateInfo.latest_version || '';
        const currentVersion = updateInfo.current_version || '';
        
        // Update display
        versionElement.textContent = `v${latestVersion} available ⚡`;
        versionElement.title = `Update available! Current: ${currentVersion}, Latest: ${latestVersion}.`;
        
        // Add classes for styling and interaction
        versionElement.classList.add('update-available', 'pulse');
        versionElement.style.cursor = 'default';
        versionElement.onclick = null;
    }
    
    showUpdateNotification(updateInfo) {
        // Show update notification dialog
        const latest = updateInfo.latest_version || '';
        const current = updateInfo.current_version || '';
        const lines = [
            `Current version: ${current}`,
            `Latest version: ${latest}`,
            'Visit GitHub Releases to download.'
        ];
        const fallbackMessage = `Update available!\n\n${lines.join('\n')}`;

        if (DialogManager && typeof DialogManager.showUpdatePrompt === 'function') {
            DialogManager.showUpdatePrompt('Update available! ⚡', lines).catch(() => {
                alert(fallbackMessage);
            });
        } else {
            alert(fallbackMessage);
        }
    }
}

// Initialize the app
const app = new ArcaneAuditorApp();
window.app = app; // Make app globally accessible
window.DialogManager = window.DialogManager || DialogManager;

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
