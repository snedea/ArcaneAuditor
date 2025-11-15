// Configuration management for Arcane Auditor web interface

import { getLastSelectedConfig, saveSelectedConfig } from './utils.js';

export class ConfigManager {
    pendingDuplicateId = null;

    constructor(app) {
        this.app = app;
        this.availableConfigs = [];
        // Don't load from localStorage in constructor - wait until configs are loaded
        // This ensures localStorage is ready (important for pywebview)
        this.selectedConfig = null;
        this.activeCardMenuCleanup = null;
        this.activeCardMenuTrigger = null;

        this.bindGlobalConfigControls();

    }

    updateMetadataLine() {
        const metaDiv = document.getElementById('config-meta-line');
        if (!metaDiv) return;
    
        const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
        if (!config || !config.rules) {
            metaDiv.textContent = '';
            return;
        }
    
        const rules = config.rules;
        const enabled = Object.values(rules).filter(r => r.enabled).length;
        const disabled = Object.values(rules).filter(r => !r.enabled).length;
    
        const perf = config.performance || '';
    
        metaDiv.textContent = `${enabled} enabled • ${disabled} disabled${perf ? ' • ' + perf : ''}`;
    }
    

    openDuplicateModal(configId) {
        this.pendingDuplicateId = configId;
    
        const modal = document.getElementById("duplicate-config-modal");
        const nameInput = document.getElementById("duplicate-config-name");
    
        nameInput.value = "";
        modal.classList.remove("hidden");
    }
    
    closeDuplicateModal() {
        const modal = document.getElementById("duplicate-config-modal");
        modal.classList.add("hidden");
    }
    

    bindGlobalConfigControls() {
        // Duplicate Modal Buttons
        document.getElementById("duplicate-close-btn").onclick =
        document.getElementById("duplicate-cancel-btn").onclick = () => {
            this.closeDuplicateModal();
        };

        document.getElementById("duplicate-confirm-btn").onclick = () => {
            const newName = document.getElementById("duplicate-config-name").value.trim();
            const category = document.querySelector("input[name='duplicate-category']:checked").value;

            if (!newName) {
                this.app.showToast("Please enter a name.", "info");
                return;
            }

            this.duplicateConfiguration(
                this.pendingDuplicateId,
                newName,
                category
            );

            this.closeDuplicateModal();
        };

        // --- TOP BAR BUTTONS ---
        const editBtn = document.getElementById('config-edit-btn');
        const copyBtn = document.getElementById('config-copy-btn');
        const deleteBtn = document.getElementById('config-delete-btn');
    
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                if (!this.selectedConfig) {
                    this.app.showToast('Select a configuration first', 'info');
                    return;
                }
                this.editConfiguration(this.selectedConfig);
            });
        }
    
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                if (!this.selectedConfig) {
                    this.app.showToast('Select a configuration first', 'info');
                    return;
                }
                this.openDuplicateModal(this.selectedConfig);
            });
        }
    
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                if (!this.selectedConfig) {
                    this.app.showToast('Select a configuration first', 'info');
                    return;
                }
                const cfg = this.availableConfigs.find(c => c.id === this.selectedConfig);
                this.requestDeleteConfiguration(cfg);
            });
        }
    
        // --- DUPLICATE MODAL ---
        const duplicateModal = document.getElementById("duplicate-config-modal");
        const duplicateCloseBtn = document.getElementById("duplicate-close-btn");
        const duplicateCancelBtn = document.getElementById("duplicate-cancel-btn");
        const duplicateConfirmBtn = document.getElementById("duplicate-confirm-btn");
    
        if (duplicateCloseBtn) {
            duplicateCloseBtn.onclick = () => this.closeDuplicateModal();
        }
        if (duplicateCancelBtn) {
            duplicateCancelBtn.onclick = () => this.closeDuplicateModal();
        }
        if (duplicateConfirmBtn) {
            duplicateConfirmBtn.onclick = () => {
                const name = document.getElementById("duplicate-config-name").value.trim();
                const category = document.querySelector("input[name='duplicate-category']:checked").value;
    
                if (!name) {
                    this.app.showToast("Please enter a name.", "info");
                    return;
                }
    
                this.duplicateConfiguration(this.pendingDuplicateId, name, category);
                this.closeDuplicateModal();
            };
        }
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
            
            this.renderConfigCards();
            this.updateMetadataLine();

        } catch (error) {
            console.error('Failed to load configurations:', error);
            this.app.showError('Failed to load configurations. Please refresh the page.');
        }
    }
    
    
    renderConfigCards() {
        const container = document.getElementById('config-card-container');
        const columns = {
            builtIn: document.getElementById('config-column-built-in'),
            team: document.getElementById('config-column-team'),
            personal: document.getElementById('config-column-personal')
        };

        if (!container || !columns.builtIn || !columns.team || !columns.personal) {
            return;
        }

        this.closeActiveCardMenu();
        Object.values(columns).forEach(column => {
            if (column) {
                column.innerHTML = '';
            }
        });

        if (!Array.isArray(this.availableConfigs) || this.availableConfigs.length === 0) {
            return;
        }

        const sortedConfigs = [...this.availableConfigs];
        if (this.selectedConfig) {
            sortedConfigs.sort((a, b) => {
                if (a.id === this.selectedConfig) return -1;
                if (b.id === this.selectedConfig) return 1;
                return 0;
            });
        }

        sortedConfigs.forEach(config => {
            const card = document.createElement('div');
            card.className = 'config-option config-card';
            card.dataset.configId = config.id;

            if (config.id === this.selectedConfig) {
                card.classList.add('selected');
            }

            const menuBtn = document.createElement('div');
            menuBtn.className = 'card-menu';
            menuBtn.dataset.id = config.id;
            menuBtn.setAttribute('role', 'button');
            menuBtn.setAttribute('tabindex', '0');
            menuBtn.setAttribute('aria-label', `Configuration actions for ${config.name}`);
            menuBtn.textContent = '⋮';

            const nameDiv = document.createElement('div');
            nameDiv.className = 'config-name';
            nameDiv.textContent = config.name;

            const metaDiv = document.createElement('div');
            metaDiv.className = 'config-meta';
            const ruleCounts = this.getRuleCounts(config);
            metaDiv.textContent = `${ruleCounts.enabled} enabled • ${ruleCounts.disabled} disabled`;

            card.appendChild(menuBtn);
            card.appendChild(nameDiv);
            card.appendChild(metaDiv);

            card.addEventListener('click', (event) => {
                if (event.target.closest('.card-menu')) {
                    return;
                }
                this.selectConfiguration(config.id);
            });

            menuBtn.addEventListener('click', (event) => {
                event.stopPropagation();
                this.showCardMenu(config.id, menuBtn);
            });
            menuBtn.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    event.stopPropagation();
                    this.showCardMenu(config.id, menuBtn);
                }
            });

            const typeKey = (config.type || 'built-in').toLowerCase();
            const targetColumn =
                typeKey === 'team' ? columns.team :
                typeKey === 'personal' ? columns.personal :
                columns.builtIn;

            targetColumn.appendChild(card);
        });
    }

    getRuleCounts(config) {
        const rulesArray = config?.rules && typeof config.rules === 'object'
            ? Object.values(config.rules)
            : [];

        let enabled = 0;
        let disabled = 0;

        if (rulesArray.length > 0) {
            enabled = rulesArray.filter(rule => rule && rule.enabled).length;
            disabled = rulesArray.filter(rule => rule && rule.enabled === false).length;
        } else {
            const total = typeof config.rules_count === 'number' ? config.rules_count : 0;
            const disabledMeta = typeof config.disabled_rules === 'number'
                ? config.disabled_rules
                : (typeof config.rules_disabled === 'number' ? config.rules_disabled : 0);
            const enabledMeta = typeof config.enabled_rules === 'number'
                ? config.enabled_rules
                : total - disabledMeta;
            enabled = Math.max(enabledMeta, 0);
            disabled = Math.max(total - enabled, 0);
        }

        return { enabled, disabled };
    }

    updateCardSelection() {
        const cards = document.querySelectorAll('.config-card');
        cards.forEach(card => {
            const configId = card.dataset.configId;
            card.classList.toggle('selected', configId === this.selectedConfig);
        });
    }

    closeActiveCardMenu() {
        if (this.activeCardMenuCleanup) {
            this.activeCardMenuCleanup();
            this.activeCardMenuCleanup = null;
        }
    }

    showCardMenu(configId, triggerElement) {
        const targetConfig = this.availableConfigs.find(cfg => cfg.id === configId);
        if (!targetConfig || !triggerElement) {
            return;
        }

        if (this.activeCardMenuTrigger === triggerElement) {
            this.closeActiveCardMenu();
            return;
        }

        this.closeActiveCardMenu();

        const menu = document.createElement('div');
        menu.className = 'config-card-menu-popover';
        menu.style.position = 'absolute';
        menu.style.visibility = 'hidden';

        const configType = (targetConfig.type || 'built-in').toLowerCase();
        const isBuiltIn = configType === 'built-in';
        const actions = [
            { action: 'view', label: 'View Details' }
        ];

        if (!isBuiltIn) {
            actions.push({ action: 'edit', label: 'Edit' });
        }

        actions.push({ action: 'copy', label: 'Copy' });

        if (!isBuiltIn) {
            actions.push({ action: 'delete', label: 'Delete', danger: true });
        }

        actions.forEach(({ action, label, danger }) => {
            const item = document.createElement('div');
            item.className = 'menu-item';
            if (danger) {
                item.classList.add('danger');
            }
            item.dataset.action = action;
            item.textContent = label;
            menu.appendChild(item);
        });

        document.body.appendChild(menu);

        const triggerRect = triggerElement.getBoundingClientRect();
        const menuRect = menu.getBoundingClientRect();
        const top = triggerRect.bottom + window.scrollY + 8;
        const minLeft = 8 + window.scrollX;
        const maxLeft = window.scrollX + document.documentElement.clientWidth - menuRect.width - 8;
        let left = triggerRect.right + window.scrollX - menuRect.width;
        left = Math.min(Math.max(left, minLeft), maxLeft);

        menu.style.top = `${top}px`;
        menu.style.left = `${left}px`;
        menu.style.visibility = 'visible';

        const handleAction = (action) => {
            if (isBuiltIn && (action === 'edit' || action === 'delete')) {
                return;
            }
            switch (action) {
                case 'view':
                    this.showConfigBreakdown();
                    break;
                case 'edit':
                    this.editConfiguration(configId);
                    break;
                case 'copy':
                    this.openDuplicateModal(configId);
                    break;
                case 'delete':
                    this.requestDeleteConfiguration(targetConfig);
                    break;
                default:
                    break;
            }
        };

        const handleMenuClick = (event) => {
            const target = event.target.closest('.menu-item');
            if (!target) {
                return;
            }
            const action = target.dataset.action;
            handleAction(action);
            closeMenu();
        };

        const handleClickOutside = (event) => {
            if (menu.contains(event.target) || triggerElement.contains(event.target)) {
                return;
            }
            closeMenu();
        };

        const handleEscape = (event) => {
            if (event.key === 'Escape') {
                closeMenu();
            }
        };

        const closeMenu = () => {
            menu.removeEventListener('click', handleMenuClick);
            document.removeEventListener('click', handleClickOutside);
            document.removeEventListener('keydown', handleEscape);
            if (menu.parentNode) {
                menu.parentNode.removeChild(menu);
            }
            this.activeCardMenuCleanup = null;
            this.activeCardMenuTrigger = null;
        };

        menu.addEventListener('click', handleMenuClick);
        setTimeout(() => {
            document.addEventListener('click', handleClickOutside);
        }, 0);
        document.addEventListener('keydown', handleEscape);

        this.activeCardMenuCleanup = closeMenu;
        this.activeCardMenuTrigger = triggerElement;
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
        this.closeActiveCardMenu();
        this.updateConfigSelection();
        this.updateCardSelection();
        this.updateMetadataLine();
    }

    updateConfigSelection() {
        const configElements = document.querySelectorAll('.config-option');
        const selectEl = document.getElementById('config-select');
    
        configElements.forEach(element => {
            element.classList.remove('selected');
            element.classList.remove('show-actions');
        });
    
        const selectedElement = Array.from(configElements).find(element => {
            const configId = element.dataset.configId;
            return configId === this.selectedConfig;
        });
    
        if (selectedElement) {
            selectedElement.classList.add('selected');
            selectedElement.classList.add('show-actions');
        }
    
        if (selectEl && this.selectedConfig) {
            selectEl.value = this.selectedConfig;
        }
    }

    openDuplicateModal(configId) {
        const modal = document.getElementById("duplicate-config-modal");
        const nameInput = document.getElementById("duplicate-config-name");
        const categoryInput = document.querySelector("input[name='duplicate-category']:checked");
        this.pendingDuplicateId = configId;
        nameInput.value = "";
        categoryInput.checked = true;
        modal.classList.remove("hidden");
    }
    
    closeDuplicateModal() {
        const modal = document.getElementById("duplicate-config-modal");
        modal.classList.add("hidden");
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

    async duplicateConfiguration(configId, newName, category) {
        try {
            const response = await fetch(`/api/config/create`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: newName,
                    target: category.toLowerCase(),
                    base_id: configId
                })
            });

            if (!response.ok) throw new Error("Failed to duplicate configuration");
    
            this.app.showToast("Configuration duplicated!", "success");
    
            // Refresh list
            await this.loadConfigurations();
    
        } catch (err) {
            this.app.showToast(err.message, "error");
        }
    }
    

    requestDeleteConfiguration(config) {
        const modal = document.getElementById('config-delete-modal');
        const message = document.getElementById('config-delete-message');
        const confirmBtn = document.getElementById('config-delete-confirm');
        const cancelBtn = document.getElementById('config-delete-cancel');
        const closeBtn = document.getElementById('config-delete-close');

        if (!modal || !message || !confirmBtn || !cancelBtn || !closeBtn) {
            console.error('Delete modal elements not found');
            return;
        }

        message.textContent = `Are you sure you want to delete "${config.name}"?`;

        const cleanup = () => {
            confirmBtn.removeEventListener('click', confirmHandler);
            cancelBtn.onclick = null;
            closeBtn.onclick = null;
        };

        const confirmHandler = async () => {
            cleanup();
            modal.hidden = true;
            await this.deleteConfiguration(config.id);
        };

        confirmBtn.addEventListener('click', confirmHandler);

        cancelBtn.onclick = () => {
            cleanup();
            modal.hidden = true;
        };
        closeBtn.onclick = () => {
            cleanup();
            modal.hidden = true;
        };

        modal.hidden = false;
    }

    async deleteConfiguration(configId) {
        try {
            const response = await fetch(`/api/config/${configId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const err = await response.json().catch(() => null);
                throw new Error(err?.detail || `HTTP ${response.status}`);
            }

            await this.loadConfigurations();
            this.app.showToast('🗑️ Configuration deleted', 'success');
        } catch (error) {
            console.error(error);
            this.app.showToast(`❌ Delete failed: ${error.message}`, 'error');
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
