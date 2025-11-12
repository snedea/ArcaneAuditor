// Configuration management for Arcane Auditor web interface

import { getLastSelectedConfig, saveSelectedConfig } from './utils.js';

export class ConfigManager {
    constructor(app) {
        this.app = app;
        this.availableConfigs = [];
        this.selectedConfig = getLastSelectedConfig();
    }

    async loadConfigurations() {
        try {
            const response = await fetch('/api/configs');
            const data = await response.json();
            this.availableConfigs = data.configs;
            
            // If no config is selected, select the first available one
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

        // Find and select the clicked config
        const selectedElement = Array.from(configElements).find(element => {
            const configName = element.querySelector('.config-name').textContent;
            const config = this.availableConfigs.find(c => c.name === configName);
            return config && config.id === this.selectedConfig;
        });

        if (selectedElement) {
            selectedElement.classList.add('selected');
            
            // Add config actions to selected element
            const selectedConfig = this.availableConfigs.find(c => c.id === this.selectedConfig);
            if (selectedConfig) {
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
