// Main application orchestration for Arcane Auditor web interface

import { ConfigManager } from './config/manager.js';
import { ThemeManager } from './theme-manager.js';
import { ResultsManager } from './results/manager.js';
import { downloadResults, getLastSortBy, getLastSortFilesBy } from './utils.js';
import { showMagicalAnalysisComplete } from './magic-mode.js';
import { DialogManager } from './dialog-manager.js';

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
        this.dismissedFindings = new Set();      // set of finding indices dismissed/acknowledged by user
        this.autofixInProgress = new Set();      // finding indices currently being auto-fixed
        this.diffWarnings = new Map();           // findingIndex → diff_warning object from autofix
        this.isRevalidating = false;
        this.lastRevalidationFindingCount = null; // total findings from latest revalidation (null = not yet run)

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
        this.ruleEvolutionPreferences = {
            new_rule_default_enabled: true
        };
        this.exportPreferences = {
            excel_single_tab: false
        };
        this.updatePreferencesPromise = null;
        this.ruleEvolutionPreferencesPromise = null;
        this.exportPreferencesPromise = null;
        this.versionRetryAttempts = 0;
        this.versionRetryTimer = null;
        this.settingsPanelElements = null;

        // Initialize managers
        this.configManager = new ConfigManager(this);
        this.resultsManager = new ResultsManager(this);
        
        this.initializeEventListeners();

        // Initialize theme manager
        this.themeManager = new ThemeManager();
        this.themeManager.initialize();

        // Fix: Force-remove focus from the Grimoire button on Desktop App load
        // We use a timeout to let the desktop wrapper finish its initial focus routine first.
        setTimeout(() => {
            const grimoireBtn = document.getElementById('global-grimoire-btn');
            if (grimoireBtn) {
                grimoireBtn.blur(); // Remove focus
                grimoireBtn.classList.remove('hover'); // Force remove any sticky hover classes
            }
            // Optional: Shift focus to the body so nothing is highlighted
            document.body.focus(); 
        }, 500); // 500ms delay is usually the sweet spot

        // Load configurations
        this.configManager.loadConfigurations();

        // Load update preferences then version asynchronously after initialization
        this.updatePreferencesPromise = this.loadUpdatePreferences();
        this.updatePreferencesPromise.catch(err => console.error('Failed to load update preferences:', err));
        this.ruleEvolutionPreferencesPromise = this.loadRuleEvolutionPreferences();
        this.ruleEvolutionPreferencesPromise.catch(err => console.error('Failed to load rule evolution preferences:', err));
        this.exportPreferencesPromise = this.loadExportPreferences();
        this.exportPreferencesPromise.catch(err => console.error('Failed to load export preferences:', err));
        this.loadVersion().catch(err => console.error('Failed to load version:', err));

        // Initialize settings panel after DOM is loaded
        if (document.readyState === 'loading') {
            window.addEventListener('DOMContentLoaded', () => this.initializeSettingsPanel());
        } else {
            this.initializeSettingsPanel();
        }

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

        // Header click to return to home/upload screen
        const headerTitle = document.querySelector('header h1');
        if (headerTitle) {
            headerTitle.style.cursor = 'pointer';
            headerTitle.addEventListener('click', () => this.showUpload());
        }

        // File expansion listeners (delegated)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.file-header')) {
                const filePath = e.target.closest('.file-header').dataset.filePath;
                if (filePath) {
                    this.resultsManager.toggleFileExpansion(filePath);
                }
            }
        });
    }

    initializeSettingsPanel() {
        const settingsButton = document.getElementById('settings-toggle');
        const settingsPanel = document.getElementById('settings-panel');
        const updateCheckbox = document.getElementById('settings-update-checkbox');
        const newRuleDefaultCheckbox = document.getElementById('settings-new-rule-default-checkbox');
        const excelSingleTabCheckbox = document.getElementById('setting-excel-single-tab');

        if (!settingsButton || !settingsPanel) {
            return;
        }

        const openPanel = () => {
            settingsButton.setAttribute('aria-expanded', 'true');
            settingsPanel.hidden = false;
            settingsPanel.setAttribute('aria-hidden', 'false');
        };

        const closePanel = () => {
            settingsButton.setAttribute('aria-expanded', 'false');
            settingsPanel.hidden = true;
            settingsPanel.setAttribute('aria-hidden', 'true');
        };

        const isOpen = () => settingsButton.getAttribute('aria-expanded') === 'true';

        settingsButton.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (isOpen()) {
                closePanel();
            } else {
                openPanel();
            }
        });

        settingsPanel.addEventListener('click', (event) => {
            event.stopPropagation();
        });

        const handleDocumentClick = (event) => {
            if (!settingsPanel.contains(event.target) && !settingsButton.contains(event.target) && isOpen()) {
                closePanel();
            }
        };

        document.addEventListener('click', handleDocumentClick);

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && isOpen()) {
                closePanel();
                settingsButton.focus();
            }
        });

        if (updateCheckbox) {
            updateCheckbox.addEventListener('change', (event) => {
                const { checked } = event.target;
                this.persistUpdatePreference(checked);
            });
        }

        if (newRuleDefaultCheckbox) {
            newRuleDefaultCheckbox.addEventListener('change', (event) => {
                const { checked } = event.target;
                this.persistRuleEvolutionPreference(checked);
            });
        }

        if (excelSingleTabCheckbox) {
            excelSingleTabCheckbox.addEventListener('change', (event) => {
                const { checked } = event.target;
                this.persistExportPreference(checked);
            });
        }

        this.settingsPanelElements = {
            button: settingsButton,
            panel: settingsPanel,
            updateCheckbox,
            newRuleDefaultCheckbox,
            excelSingleTabCheckbox
        };

        // Ensure panel starts hidden
        closePanel();
        this.syncUpdatePreferenceUI();
        this.syncRuleEvolutionPreferenceUI();
        this.syncExportPreferenceUI();

        // Prevent initial focus outline on load unless the user tabs to the control
        setTimeout(() => {
            if (settingsButton === document.activeElement) {
                settingsButton.blur();
            }
        }, 50);
    }

    syncPreferenceUI(key, value) {
        const checkbox = this.settingsPanelElements[key];
        if (!checkbox) {
            return;
        }
        checkbox.checked = Boolean(value);
    }

    syncUpdatePreferenceUI() {
        this.syncPreferenceUI('updateCheckbox', this.updatePreferences.enabled);
    }

    syncRuleEvolutionPreferenceUI() {
        this.syncPreferenceUI('newRuleDefaultCheckbox', this.ruleEvolutionPreferences.new_rule_default_enabled);
    }

    syncExportPreferenceUI() {
        this.syncPreferenceUI('excelSingleTabCheckbox', this.exportPreferences.excel_single_tab);
    }

    async persistUpdatePreference(enabled) {
        const checkbox = this.settingsPanelElements.updateCheckbox;
        const previous = this.updatePreferences.enabled;
        this.updatePreferences.enabled = Boolean(enabled);

        checkbox.disabled = true;

        try {
            if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_update_preferences === 'function') {
                const result = await window.pywebview.api.set_update_preferences(enabled);
                if (result && result.success === false) {
                    throw new Error(result.error || 'Failed to save preferences');
                }
            } else {
                const response = await fetch('/api/update-preferences', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ enabled })
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
            }
        } catch (error) {
            console.error('Failed to update preferences:', error);
            this.updatePreferences.enabled = previous;
            this.syncUpdatePreferenceUI();
            this.showToast('❌ Failed to update settings. Please try again.', 'error');
        } finally {
            checkbox.disabled = false;
        }
    }

    // Navigation methods
    showUpload() {
        this.hideAllSections();
        document.getElementById('upload-section').style.display = 'block';
        
        // Show config toolbar on analyze page
        const configToolbar = document.getElementById('config-toolbar');
        if (configToolbar) {
            configToolbar.style.display = 'flex';
        }
        
        const configSectionContainer = document.querySelector('.config-section-container');
        if (configSectionContainer) {
            configSectionContainer.style.display = 'block';
        }
    }

    showLoading() {
        this.hideAllSections();
        document.getElementById('loading-section').style.display = 'block';
        
        // Hide config toolbar when analysis is running
        const configToolbar = document.getElementById('config-toolbar');
        if (configToolbar) {
            configToolbar.style.display = 'none';
        }
        
        const configSectionContainer = document.querySelector('.config-section-container');
        if (configSectionContainer) {
            configSectionContainer.style.display = 'none';
        }
    }

    showResults() {
        this.hideAllSections();
        document.getElementById('results-section').style.display = 'block';
        
        // Hide config toolbar on results page
        const configToolbar = document.getElementById('config-toolbar');
        if (configToolbar) {
            configToolbar.style.display = 'none';
        }
        
        const configSectionContainer = document.querySelector('.config-section-container');
        if (configSectionContainer) {
            configSectionContainer.style.display = 'none';
        }
        
        // Initialize filtered findings with current result findings
        if (this.currentResult) {
            this.filteredFindings = [...this.currentResult.findings];
        }

        // Initialize file contents for autofix
        this.initializeFileContents();

        // Display context awareness panel if available
        if (this.currentResult && this.currentResult.context) {
            this.resultsManager.displayContext(this.currentResult.context);
        }

        this.resultsManager.renderResults();

        // Show magical analysis completion if in magic mode
        showMagicalAnalysisComplete(this.currentResult);

        // Fire AI explain in background
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
        
        // Show config toolbar on analyze page (error is part of analyze flow)
        const configToolbar = document.getElementById('config-toolbar');
        if (configToolbar) {
            configToolbar.style.display = 'flex';
        }
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
            this.syncUpdatePreferenceUI();
        } catch (error) {
            console.error('Failed to load update preferences:', error);
            // Keep defaults (disabled) if we can't load preferences
            this.updatePreferences.enabled = false;
            this.syncUpdatePreferenceUI();
        }
    }

    async loadRuleEvolutionPreferences() {
        try {
            const response = await fetch('/api/rule-evolution-preferences');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();

            if (!data || typeof data !== 'object') {
                throw new Error('Invalid rule evolution preferences payload');
            }

            if (typeof data.new_rule_default_enabled === 'boolean') {
                this.ruleEvolutionPreferences.new_rule_default_enabled = data.new_rule_default_enabled;
            }
            this.syncRuleEvolutionPreferenceUI();
        } catch (error) {
            console.error('Failed to load rule evolution preferences:', error);
            // Keep defaults (enabled) if we can't load preferences
            this.ruleEvolutionPreferences.new_rule_default_enabled = true;
            this.syncRuleEvolutionPreferenceUI();
        }
    }

    async persistRuleEvolutionPreference(enabled) {
        const checkbox = this.settingsPanelElements.newRuleDefaultCheckbox;
        const previous = this.ruleEvolutionPreferences.new_rule_default_enabled;
        this.ruleEvolutionPreferences.new_rule_default_enabled = Boolean(enabled);

        checkbox.disabled = true;

        try {
            const response = await fetch('/api/rule-evolution-preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ new_rule_default_enabled: enabled })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }
            
            if (data.success !== true) {
                throw new Error('Save operation did not return success');
            }
            
            // Ensure UI is in sync after successful save
            this.syncRuleEvolutionPreferenceUI();
            console.log('Rule evolution preference saved:', enabled);
        } catch (error) {
            console.error('Failed to update rule evolution preferences:', error);
            this.ruleEvolutionPreferences.new_rule_default_enabled = previous;
            this.syncRuleEvolutionPreferenceUI();
            this.showToast(`❌ Failed to update settings: ${error.message}`, 'error');
        } finally {
            checkbox.disabled = false;
        }
    }

    async loadExportPreferences() {
        try {
            const response = await fetch('/api/export-preferences');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();

            if (!data || typeof data !== 'object') {
                throw new Error('Invalid export preferences payload');
            }

            if (typeof data.excel_single_tab === 'boolean') {
                this.exportPreferences.excel_single_tab = data.excel_single_tab;
            }
            this.syncExportPreferenceUI();
        } catch (error) {
            console.error('Failed to load export preferences:', error);
            // Keep defaults (disabled) if we can't load preferences
            this.exportPreferences.excel_single_tab = false;
            this.syncExportPreferenceUI();
        }
    }

    async persistExportPreference(enabled) {
        const checkbox = this.settingsPanelElements.excelSingleTabCheckbox;
        const previous = this.exportPreferences.excel_single_tab;
        this.exportPreferences.excel_single_tab = Boolean(enabled);

        checkbox.disabled = true;

        try {
            const response = await fetch('/api/export-preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ excel_single_tab: enabled })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }
            
            if (data.success !== true) {
                throw new Error('Save operation did not return success');
            }
            
            // Ensure UI is in sync after successful save
            this.syncExportPreferenceUI();
            console.log('Export preference saved:', enabled);
        } catch (error) {
            console.error('Failed to update export preferences:', error);
            this.exportPreferences.excel_single_tab = previous;
            this.syncExportPreferenceUI();
            this.showToast(`❌ Failed to update settings: ${error.message}`, 'error');
        } finally {
            checkbox.disabled = false;
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
        this.resultsManager.updateSeverityFilter(value);
    }

    updateFileTypeFilter(value) {
        this.resultsManager.updateFileTypeFilter(value);
    }

    updateSortBy(value) {
        this.resultsManager.updateSortBy(value);
    }

    updateSortFilesBy(value) {
        this.resultsManager.updateSortFilesBy(value);
    }

    expandAllFiles() {
        this.resultsManager.expandAllFiles();
    }

    collapseAllFiles() {
        this.resultsManager.collapseAllFiles();
    }

    // -----------------------------------------------------------------------
    // AI Features: Explain, Autofix, Revalidate, Export
    // -----------------------------------------------------------------------

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
        if (!fab || !label) return;

        const phrases = ArcaneAuditorApp.AI_LOADING_PHRASES;
        let idx;
        do {
            idx = Math.floor(Math.random() * phrases.length);
        } while (phrases.length > 1 && idx === this._lastPhraseIdx);
        this._lastPhraseIdx = idx;
        label.textContent = phrases[idx];

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

            if (response.status === 429) {
                console.warn('Rate limited on /api/explain — will retry on next analysis');
                fab.style.display = 'none';
                return;
            }

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
                this.resultsManager.renderResults();
            }
            fab.style.display = 'none';
        } catch (error) {
            fab.style.display = 'none';
            console.error('AI explanation failed:', error.message);
        }
    }

    initializeFileContents() {
        this.editedFileContents.clear();
        this.originalFileContents.clear();
        this.resolvedFindings.clear();
        this.dismissedFindings.clear();
        if (!this.currentResult) return;

        this._originalFindingCount = this.currentResult.findings.length;

        const seen = new Set();
        for (const finding of this.currentResult.findings) {
            const fp = finding.file_path;
            if (seen.has(fp) || !finding.snippet) continue;
            seen.add(fp);
            const content = finding.snippet.lines.map(l => l.text).join('\n');
            this.editedFileContents.set(fp, content);
            this.originalFileContents.set(fp, content);
        }
    }

    async revalidate() {
        if (!this.currentResult || this.editedFileContents.size === 0) return;
        this.isRevalidating = true;

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

            this.lastRevalidationFindingCount = result.findings.length;
            this.diffFindings(result.findings);
            this.filteredFindings = [...this.currentResult.findings];
            this.resultsManager.renderResults();
        } catch (error) {
            console.error('Revalidation error:', error);
        } finally {
            this.isRevalidating = false;
        }
    }

    _stableFindingKey(f) {
        const stableMsg = f.message.replace(/'[^']{20,}'/g, "'...'");
        return `${f.rule_id}::${f.file_path}::${stableMsg}`;
    }

    diffFindings(newFindings) {
        const newKeys = new Set();
        for (const f of newFindings) {
            newKeys.add(this._stableFindingKey(f));
        }

        this.resolvedFindings.clear();
        if (!this.currentResult) return;

        // Preserve dismissed findings across revalidation
        const prevDismissed = new Set(this.dismissedFindings);
        this.dismissedFindings.clear();

        const existingKeys = new Set();
        for (let i = 0; i < this.currentResult.findings.length; i++) {
            const f = this.currentResult.findings[i];
            existingKeys.add(this._stableFindingKey(f));
            if (!newKeys.has(this._stableFindingKey(f))) {
                this.resolvedFindings.add(i);
            }
            // Re-apply dismissed status if finding still exists after revalidation
            if (prevDismissed.has(i)) {
                this.dismissedFindings.add(i);
            }
        }

        for (const f of newFindings) {
            const key = this._stableFindingKey(f);
            if (!existingKeys.has(key)) {
                this.currentResult.findings.push(f);
                existingKeys.add(key);
            }
        }
    }

    getFileContentFromSnippets(filePath) {
        if (!this.currentResult) return null;
        for (const f of this.currentResult.findings) {
            if (f.file_path === filePath && f.snippet && f.snippet.lines) {
                return f.snippet.lines.map(l => l.text).join('\n');
            }
        }
        return null;
    }

    dismissFinding(findingIndex) {
        if (!this.currentResult || findingIndex < 0 || findingIndex >= this.currentResult.findings.length) return;
        this.dismissedFindings.add(findingIndex);
        this.resultsManager.renderResults();
    }

    undismissFinding(findingIndex) {
        if (!this.currentResult || findingIndex < 0 || findingIndex >= this.currentResult.findings.length) return;
        this.dismissedFindings.delete(findingIndex);
        this.resultsManager.renderResults();
    }

    async revertFix(findingIndex) {
        if (!this.currentResult || findingIndex < 0 || findingIndex >= this.currentResult.findings.length) return;

        const filePath = this.currentResult.findings[findingIndex].file_path;
        const originalContent = this.originalFileContents.get(filePath);
        if (!originalContent) return;

        // Restore original file content
        this.editedFileContents.set(filePath, originalContent);

        // Un-resolve all findings in this file and clear their diff warnings
        for (let i = 0; i < this.currentResult.findings.length; i++) {
            if (this.currentResult.findings[i].file_path === filePath) {
                this.resolvedFindings.delete(i);
                this.diffWarnings.delete(i);
            }
        }

        // Trim findings back to original set (remove any added by revalidation)
        if (this._originalFindingCount != null) {
            this.currentResult.findings.length = this._originalFindingCount;
        }

        // Rebuild snippets from original content
        const lines = originalContent.split('\n');
        for (const f of this.currentResult.findings) {
            if (f.file_path === filePath) {
                f.snippet = {
                    start_line: 1,
                    lines: lines.map((text, i) => ({
                        number: i + 1,
                        text,
                        highlight: (i + 1) === f.line,
                    })),
                };
            }
        }

        // Check if any files still have actual edits — if so, revalidate; otherwise just render
        let hasRemainingEdits = false;
        for (const [fp, content] of this.editedFileContents) {
            if (content !== this.originalFileContents.get(fp)) {
                hasRemainingEdits = true;
                break;
            }
        }

        if (hasRemainingEdits) {
            await this.revalidate();
        }

        this.filteredFindings = [...this.currentResult.findings];
        this.resultsManager.renderResults();
    }

    async autofix(findingIndex) {
        if (!this.currentResult || findingIndex < 0 || findingIndex >= this.currentResult.findings.length) return;

        const finding = this.currentResult.findings[findingIndex];
        const filePath = finding.file_path;

        let fileContent = this.editedFileContents.get(filePath);
        if (!fileContent) {
            fileContent = this.getFileContentFromSnippets(filePath);
            if (fileContent) {
                this.editedFileContents.set(filePath, fileContent);
                this.originalFileContents.set(filePath, fileContent);
            }
        }
        if (!fileContent) {
            alert('Cannot auto-fix: file content not available. Try re-uploading.');
            return;
        }

        this.autofixInProgress.add(findingIndex);
        this.resultsManager.renderResults();

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

            if (response.status === 429) {
                throw new Error('Rate limit reached — wait a minute before trying again');
            }

            if (!response.ok) {
                throw new Error(data.detail || 'Autofix failed');
            }

            this.editedFileContents.set(filePath, data.fixed_content);

            if (data.diff_warning) {
                this.diffWarnings.set(findingIndex, data.diff_warning);
            } else {
                this.diffWarnings.delete(findingIndex);
            }

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
            this.resultsManager.renderResults();
        }
    }

    async autofixFile(filePath) {
        if (!this.currentResult) return;

        const isRemovalFinding = (f) => {
            const id = (f.rule_id || '').toLowerCase();
            const msg = (f.message || '').toLowerCase();
            return /unused|dead.?code|console.?log|remove|debug.?statement/.test(id + ' ' + msg);
        };

        const maxPasses = 3;
        for (let pass = 0; pass < maxPasses; pass++) {
            const indices = [];
            for (let i = 0; i < this.currentResult.findings.length; i++) {
                if (this.currentResult.findings[i].file_path === filePath && !this.resolvedFindings.has(i)) {
                    indices.push(i);
                }
            }

            if (indices.length === 0) break;
            if (pass > 0) {
                console.log(`Fix All pass ${pass + 1}: ${indices.length} findings still unresolved`);
            }

            indices.sort((a, b) => {
                const aRemoval = isRemovalFinding(this.currentResult.findings[a]) ? 1 : 0;
                const bRemoval = isRemovalFinding(this.currentResult.findings[b]) ? 1 : 0;
                return aRemoval - bRemoval;
            });

            for (const idx of indices) {
                await this.autofix(idx);
            }
        }
    }

    async exportAllZip() {
        if (this.editedFileContents.size === 0) return;

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
            const baseName = this.uploadedFileName
                ? this.uploadedFileName.replace(/\.zip$/i, '')
                : 'fixed_files';
            a.download = `${baseName}_reviewed.zip`;
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

        // Show config toolbar when returning to analyze page
        const configToolbar = document.getElementById('config-toolbar');
        if (configToolbar) {
            configToolbar.style.display = 'flex';
        }

        const configSectionContainer = document.querySelector('.config-section-container');
        if (configSectionContainer) {
            configSectionContainer.style.display = 'block';
        }

        document.getElementById('upload-section').style.display = 'block';
        this.currentResult = null;
        this.findingExplanations.clear();
        this.uploadedFileName = null;
        this.selectedFiles = [];

        // Clear fix state
        this.editedFileContents.clear();
        this.originalFileContents.clear();
        this.resolvedFindings.clear();
        this.dismissedFindings.clear();
        this.autofixInProgress.clear();
        this.diffWarnings.clear();
        this.isRevalidating = false;
        this.lastRevalidationFindingCount = null;

        // Reset file inputs
        const fileInput = document.getElementById('file-input');
        fileInput.value = '';
        const filesInput = document.getElementById('files-input');
        filesInput.value = '';

        // Hide selected files list
        document.getElementById('selected-files-list').style.display = 'none';

        // Hide AI FAB
        const fab = document.getElementById('ai-loading-fab');
        if (fab) fab.style.display = 'none';

        // Reset renderers
        this.resultsManager.resetForNewUpload();
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
                    versionElement.removeAttribute('data-loading');
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
                versionElement.removeAttribute('data-loading');
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
        const releaseUrl = updateInfo.release_url || 'https://github.com/Developers-and-Dragons/ArcaneAuditor/releases';
        
        // Update display
        const linkLabel = latestVersion ? `v${latestVersion} now available! ⚡` : 'New version available! ⚡';
        versionElement.innerHTML = `<a href="${releaseUrl}" target="_blank" rel="noopener noreferrer">${linkLabel}</a>`;
        versionElement.title = `Update available! Current: v${currentVersion}, Latest: v${latestVersion}.`;
        versionElement.removeAttribute('data-loading');
        
        // Add classes for styling and interaction
        versionElement.classList.add('update-available', 'pulse');
        versionElement.style.cursor = 'pointer';
    }
    
    showUpdateNotification(updateInfo) {
        // Show update notification dialog
        const latest = updateInfo.latest_version || '';
        const current = updateInfo.current_version || '';
        const releaseUrl = updateInfo.release_url || 'https://github.com/Developers-and-Dragons/ArcaneAuditor/releases';
        const lines = [
            `Current: v${current}`,
            `Latest: v${latest}`,
            releaseUrl
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
    app.themeManager.toggleTheme();
};

window.toggleContextPanel = function() {
    app.resultsManager.toggleContextPanel();
};

// Results renderer global functions
window.expandAllFiles = function() {
    app.resultsManager.expandAllFiles();
};

window.collapseAllFiles = function() {
    app.resultsManager.collapseAllFiles();
};

window.updateSeverityFilter = function(value) {
    app.resultsManager.updateSeverityFilter(value);
};

window.updateFileTypeFilter = function(value) {
    app.resultsManager.updateFileTypeFilter(value);
};

window.updateSortBy = function(value) {
    app.resultsManager.updateSortBy(value);
};

window.updateSortFilesBy = function(value) {
    app.resultsManager.updateSortFilesBy(value);
};

// AI feature global functions
window.autofix = function(findingIndex) {
    app.autofix(findingIndex);
};

window.dismissFinding = function(findingIndex) {
    app.dismissFinding(findingIndex);
};

window.undismissFinding = function(findingIndex) {
    app.undismissFinding(findingIndex);
};

window.revertFix = function(findingIndex) {
    app.revertFix(findingIndex);
};

window.autofixFile = function(filePath) {
    app.autofixFile(filePath);
};

window.exportAllZip = function() {
    app.exportAllZip();
};

window.copyExplainCard = function(cardId) {
    const card = document.getElementById(cardId);
    if (!card) return;
    const text = card.innerText;
    navigator.clipboard.writeText(text).then(() => {
        const btn = card.querySelector('.explain-copy-btn');
        if (btn) {
            const orig = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(() => { btn.textContent = orig; }, 1500);
        }
    });
};

export default app;
