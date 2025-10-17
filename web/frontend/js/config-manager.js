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
        if (!this.selectedConfig) {
            alert('Please select a configuration first');
            return;
        }

        const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
        if (!config) {
            alert('Configuration not found');
            return;
        }

        // Create modal content
        const modalContent = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>📋 ${config.name} - Configuration Details</h3>
                        <button class="modal-close" onclick="closeModal()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="config-detail-section">
                            <h4>📊 Overview</h4>
                            <div class="config-detail-grid">
                                <div class="detail-item">
                                    <strong>Type:</strong> ${config.type || 'Built-in'}
                                </div>
                                <div class="detail-item">
                                    <strong>Rules Enabled:</strong> ${config.rules_count}
                                </div>
                                <div class="detail-item">
                                    <strong>Performance:</strong> ${config.performance}
                                </div>
                                <div class="detail-item">
                                    <strong>Description:</strong> ${config.description}
                                </div>
                            </div>
                        </div>
                        
                        <div class="config-detail-section">
                            <h4>📁 File Path</h4>
                            <div class="file-path-display">
                                <code>${config.path}</code>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalContent);
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
}

// Global function for HTML onclick handlers
window.showConfigBreakdown = function() {
    if (window.app && window.app.configManager) {
        window.app.configManager.showConfigBreakdown();
    }
};

window.closeModal = function() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.remove();
    }
};
