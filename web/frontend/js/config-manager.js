// Configuration management for Arcane Auditor web interface

import { getLastSelectedConfig, saveSelectedConfig } from './utils.js';

export class ConfigManager {
    constructor(app) {
        this.app = app;
        this.availableConfigs = [];
        // Don't load from localStorage in constructor - wait until configs are loaded
        // This ensures localStorage is ready (important for pywebview)
        this.selectedConfig = null;
    }

    async loadConfigurations() {
        try {
            // Add cache-busting query parameter to prevent browser caching
            const cacheBuster = `?t=${Date.now()}`;
            const response = await fetch(`/api/configs${cacheBuster}`);
            const data = await response.json();
            this.availableConfigs = data.configs;
            
            // NOW load from localStorage (after configs are loaded, ensuring localStorage is ready)
            // This is important for pywebview which may not have localStorage ready immediately
            if (!this.selectedConfig) {
                try {
                    const savedConfig = getLastSelectedConfig();
                    this.selectedConfig = savedConfig;
                } catch (e) {
                    this.selectedConfig = null;
                }
            }
            
            // Validate that the saved config ID exists in available configs
            // If not, clear it and select the first available one
            if (this.selectedConfig) {
                const configExists = this.availableConfigs.some(c => c.id === this.selectedConfig);
                if (!configExists) {
                    this.selectedConfig = null;
                }
            }
            
            // If no config is selected (or was invalid), select the first available one
            if (!this.selectedConfig && this.availableConfigs.length > 0) {
                this.selectedConfig = this.availableConfigs[0].id;
                saveSelectedConfig(this.selectedConfig);
            }
            
            this.renderConfigurations();
        } catch (error) {
            console.error('Failed to load configurations:', error);
            this.app.showError('Failed to load configurations. Please refresh the page.');
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
                const isSelected = config.id === this.selectedConfig;
                configElement.dataset.configId = config.id;

                // Selected styling
                if (isSelected) {
                    configElement.classList.add('selected');
                }

                // --- Build DOM nodes manually (fixes PyWebView dataset bug) ---

                // Type
                const typeDiv = document.createElement('div');
                typeDiv.className = `config-type ${config.type?.toLowerCase() || 'built-in'}`;
                typeDiv.textContent = config.type || 'Built-in';

                // Name
                const nameDiv = document.createElement('div');
                nameDiv.className = 'config-name';
                nameDiv.textContent = config.name;

                // Description
                const descDiv = document.createElement('div');
                descDiv.className = 'config-description';
                descDiv.textContent = config.description || '';

                // Counts container
                const countsDiv = document.createElement('div');
                countsDiv.className = 'config-counts';
                const enabledSpan = document.createElement('span');
                enabledSpan.className = 'count enabled';
                enabledSpan.textContent = `${config.rules_count} enabled`;
                const totalSpan = document.createElement('span');
                totalSpan.className = 'count total';
                totalSpan.textContent = `${config.total_rules}`;

                // Separator
                const slashText = document.createTextNode(' / ');

                countsDiv.appendChild(enabledSpan);
                countsDiv.appendChild(slashText);
                countsDiv.appendChild(totalSpan);

                // Performance
                const perfDiv = document.createElement('div');
                perfDiv.className = 'config-performance';
                perfDiv.textContent = config.performance;

                // Actions
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'config-actions';

                const editBtn = document.createElement('button');
                editBtn.className = 'wt-btn secondary small';
                editBtn.dataset.action = 'edit';
                editBtn.textContent = 'Edit';

                const dupBtn = document.createElement('button');
                dupBtn.className = 'wt-btn secondary small';
                dupBtn.dataset.action = 'duplicate';
                dupBtn.textContent = 'Duplicate';

                actionsDiv.appendChild(editBtn);
                actionsDiv.appendChild(dupBtn);

                // Append everything
                configElement.appendChild(typeDiv);
                configElement.appendChild(nameDiv);
                configElement.appendChild(descDiv);
                configElement.appendChild(countsDiv);
                configElement.appendChild(perfDiv);
                configElement.appendChild(actionsDiv);

                // Click handlers remain unchanged
                configElement.addEventListener('click', (event) => {
                    if (event.target.dataset.action === 'edit') {
                        this.editConfiguration(config.id);
                        event.stopPropagation();
                        return;
                    }

                    if (event.target.dataset.action === 'duplicate') {
                        this.duplicateConfiguration(config.id);
                        event.stopPropagation();
                        return;
                    }

                    this.selectConfiguration(config.id);
                });

                groupGrid.appendChild(configElement);
            });

            sectionDiv.appendChild(groupGrid);
            configGrid.appendChild(sectionDiv);
        });
    }

    selectConfiguration(configId) {
        // Validate that the config ID exists in available configs
        const configExists = this.availableConfigs.some(c => c.id === configId);
        if (!configExists) {
            console.error(`Config ID "${configId}" not found in available configs`);
            this.app.showToast(`Configuration not found: ${configId}`, 'error');
            return;
        }
        
        this.selectedConfig = configId;
        saveSelectedConfig(configId);
        
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

        // Find and select the clicked config using unique ID
        const selectedElement = Array.from(configElements).find(element => {
            const configId = element.dataset.configId;
            return configId === this.selectedConfig;
        });

        if (selectedElement) {
            selectedElement.classList.add('selected');
            
            // Add config actions to selected element
            const selectedConfig = this.availableConfigs.find(c => c.id === this.selectedConfig);
            if (selectedConfig) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'config-actions';
                const canEdit = selectedConfig.source !== 'presets';
                actionsDiv.innerHTML = `
                    <button class="btn btn-secondary config-details-btn" onclick="showConfigBreakdown()">
                        📋 View Details
                    </button>
                    ${canEdit ? `
                        <button class="btn btn-secondary config-edit-btn" onclick="app.configManager.editConfiguration('${selectedConfig.id}')">
                            ✏️ Edit
                        </button>
                        <button class="btn btn-secondary config-duplicate-btn" onclick="app.configManager.duplicateConfiguration('${selectedConfig.id}')">
                            📋 Duplicate
                        </button>
                    ` : ''}
                `;
                selectedElement.appendChild(actionsDiv);
            }
        }
    }

    showConfigBreakdown() {
        const modal = document.getElementById('config-breakdown-modal');
        const content = document.getElementById('config-breakdown-content');
        
        if (!this.selectedConfig) {
            alert('Please select a configuration first');
            return;
        }
        
        const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
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
                        </div>
                        <div class="rule-description">Severity: ${severity}</div>
                        ${settingsText ? `
                            <div class="rule-settings">
                                <div class="settings-label">Custom Settings:</div>
                                <pre class="settings-json">${settingsText}</pre>
                            </div>
                        ` : ''}
                        <div class="rule-status-badge enabled">✓ Enabled</div>
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
                const severity = ruleConfig.severity_override || 'ADVICE';
                html += `
                    <div class="rule-item disabled">
                        <div class="rule-header-row">
                            <div class="rule-name">${ruleName}</div>
                        </div>
                        <div class="rule-description">Severity: ${severity}</div>
                        <div class="rule-status-badge disabled">✗ Disabled</div>
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

    // Theme management
    initializeTheme() {
        // Check for saved theme preference or default to dark mode
        const savedTheme = localStorage.getItem('arcane-auditor-theme') || 'dark';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const themeIcon = document.getElementById('theme-icon');
        const themeText = document.getElementById('theme-text');
        const themeButton = document.getElementById('theme-toggle');
        
        if (theme === 'dark') {
            themeIcon.textContent = '☀️';
            themeText.textContent = 'Cast Light';
            if (themeButton) {
                themeButton.setAttribute('aria-label', 'Cast Light');
            }
        } else {
            themeIcon.textContent = '🌙';
            themeText.textContent = 'Cast Darkness';
            if (themeButton) {
                themeButton.setAttribute('aria-label', 'Cast Darkness');
            }
        }
        
        // Save preference
        localStorage.setItem('arcane-auditor-theme', theme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    async duplicateConfiguration(configId) {
        try {
            const config = this.availableConfigs.find(c => c.id === configId);
            if (!config) {
                this.app.showToast('Configuration not found', 'error');
                return;
            }

            // Determine target directory (personal or team)
            const target = config.source === 'teams' ? 'team' : 'personal';
            
            // Prompt for new name
            const baseName = config.name || config.id.split('_')[0];
            const newName = prompt(`Enter a name for the duplicate configuration:`, `${baseName} copy`);
            if (!newName || !newName.trim()) {
                return;
            }

            // Call API to create duplicate
            const response = await fetch('/api/config/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: newName.trim(),
                    target: target,
                    base_id: configId
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            // Reload configurations to show the new one
            await this.loadConfigurations();
            this.app.showToast('✅ Configuration duplicated successfully', 'success');
        } catch (error) {
            console.error('Failed to duplicate configuration:', error);
            this.app.showToast(`❌ Failed to duplicate configuration: ${error.message}`, 'error');
        }
    }

    async editConfiguration(configId) {
        // Stub for Phase 4 - will be implemented when editor modal is built
        this.app.showToast('Configuration editor will be available in Phase 4', 'info');
        console.log('Edit configuration:', configId);
    }
}

// Global function for HTML onclick handlers
window.showConfigBreakdown = function() {
    if (window.app && window.app.configManager) {
        window.app.configManager.showConfigBreakdown();
    }
};

window.hideConfigBreakdown = function() {
    const modal = document.getElementById('config-breakdown-modal');
    if (modal) {
        modal.style.display = 'none';
    }
};

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('config-breakdown-modal');
    if (event.target === modal) {
        window.hideConfigBreakdown();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        window.hideConfigBreakdown();
    }
});
