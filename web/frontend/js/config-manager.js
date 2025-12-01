// Configuration management for Arcane Auditor web interface

import { getLastSelectedConfig, saveSelectedConfig } from './utils.js';

export class ConfigManager {
    pendingDuplicateId = null;
    productionTemplateId = null;

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

    updateConfigSummary(config) {
        const nameEl = document.getElementById("summary-config-name");
        const categoryEl = document.getElementById("summary-config-category");
        const rulesEl = document.getElementById("summary-config-rules");

        if (!config) return;

        const enabled = Object.values(config.rules).filter(r => r.enabled).length;
        const disabled = Object.values(config.rules).filter(r => !r.enabled).length;

        if (nameEl) {
            nameEl.textContent = config.name;
            nameEl.classList.add("config-summary-name");
        }

        // Category
        if (categoryEl) {
            const category = (config.type || config.category || 'built-in').toLowerCase();
            categoryEl.textContent = category.toLowerCase();
            categoryEl.classList.add("config-summary-category");
        }

        // Rules wording
        if (rulesEl) {
            rulesEl.textContent = `${enabled} enabled, ${disabled} disabled`;
            rulesEl.classList.add("config-summary-rules");
        }
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
            
            // Update toolbar and dropdown with new UI
            this.updateConfigToolbar();
            this.buildConfigDropdown();

            // Initialize event listeners for toolbar
            this.initializeToolbarListeners();

            this.productionTemplateId = null;
            const productionTemplate = this.availableConfigs.find(cfg => (cfg.name || '').toLowerCase() === 'production-ready');
            if (productionTemplate) {
                this.productionTemplateId = productionTemplate.id;
            }
            if (!this.productionTemplateId) {
                const fallbackTemplate = this.availableConfigs.find(cfg => (cfg.type || '').toLowerCase() === 'built-in');
                if (fallbackTemplate) {
                    this.productionTemplateId = fallbackTemplate.id;
                }
            }

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

        this.attachColumnButtons();
    }

    attachColumnButtons() {
        const buttons = document.querySelectorAll('.column-action-btn');
        buttons.forEach(btn => {
            btn.onclick = () => this.openCreateFromTemplate(btn.dataset.category);
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
                    this.openDuplicateModal(configId, configType);
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
        
        // Update toolbar
        const config = this.availableConfigs.find(c => c.id === configId);
        if (config) {
            this.updateConfigToolbar();
            this.buildConfigDropdown();
        }
        
        // Close dropdown if open
        const dropdown = document.getElementById('config-dropdown');
        if (dropdown) {
            dropdown.classList.remove('visible');
        }
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

    openDuplicateModal(configId, defaultCategory = 'Personal') {
        const modal = document.getElementById("duplicate-config-modal");
        const nameInput = document.getElementById("duplicate-config-name");
        this.pendingDuplicateId = configId;
        nameInput.value = "";
        const normalizedCategory = (defaultCategory || 'Personal').toLowerCase();
        const categoryInputs = document.querySelectorAll("input[name='duplicate-category']");
        categoryInputs.forEach(input => {
            input.checked = input.value.toLowerCase() === normalizedCategory;
        });
        modal.classList.remove("hidden");
    }
    
    openCreateFromTemplate(categoryLabel) {
        if (!this.productionTemplateId) {
            this.app.showToast('Production template not available.', 'error');
            return;
        }
        this.openDuplicateModal(this.productionTemplateId, categoryLabel);
    }
    
    closeDuplicateModal() {
        const modal = document.getElementById("duplicate-config-modal");
        modal.classList.add("hidden");
    }
    
    

    showConfigBreakdown() {
        const modal = document.getElementById('config-breakdown-modal');
        const content = document.getElementById('config-breakdown-content');
        const header = document.querySelector('.modal-header');
        
        if (!this.selectedConfig) {
            alert('Please select a configuration first');
            return;
        }
        
        const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
        if (!config) {
            alert('Configuration not found');
            return;
        }
        
        const isBuiltIn = config.category === 'built-in';
        
        // Update modal header with action buttons
        if (header) {
            const existingActions = header.querySelector('.modal-actions');
            if (existingActions) {
                existingActions.remove();
            }
            
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'modal-actions';
            
            if (isBuiltIn) {
                actionsDiv.innerHTML = `<button id="duplicate-config">Duplicate to Customize</button>`;
            } else {
                actionsDiv.innerHTML = `
                    <button id="save-config">Save</button>
                    <button id="config-more">⋮</button>
                `;
            }
            
            header.appendChild(actionsDiv);
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
                
                const disabledAttr = isBuiltIn ? 'disabled' : '';
                const readonlyAttr = isBuiltIn ? 'readonly' : '';
                
                html += `
                    <div class="rule-item enabled">
                        <div class="rule-header-row">
                            <div class="rule-name">${ruleName}</div>
                            ${!isBuiltIn ? `
                                <label class="rule-toggle">
                                    <input type="checkbox" data-rule="${ruleName}" checked ${disabledAttr}>
                                    <span class="toggle-slider"></span>
                                </label>
                            ` : ''}
                        </div>
                        <div class="rule-description">Severity: ${severity}</div>
                        ${settingsText ? `
                            <div class="rule-settings">
                                <div class="settings-label">Custom Settings:</div>
                                <textarea class="settings-json" data-rule="${ruleName}" ${readonlyAttr}>${settingsText}</textarea>
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
                const disabledAttr = isBuiltIn ? 'disabled' : '';
                const readonlyAttr = isBuiltIn ? 'readonly' : '';
                
                html += `
                    <div class="rule-item disabled">
                        <div class="rule-header-row">
                            <div class="rule-name">${ruleName}</div>
                            ${!isBuiltIn ? `
                                <label class="rule-toggle">
                                    <input type="checkbox" data-rule="${ruleName}" ${disabledAttr}>
                                    <span class="toggle-slider"></span>
                                </label>
                            ` : ''}
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
        
        // Wire up event handlers
        if (isBuiltIn) {
            const duplicateBtn = document.getElementById('duplicate-config');
            if (duplicateBtn) {
                duplicateBtn.addEventListener('click', async () => {
                    try {
                        await this.duplicateConfiguration(config.id, config.name + ' Copy', 'personal');
                        this.app.showToast('Configuration duplicated! Opening in edit mode...', 'success');
                        // Reload configs and reopen modal
                        await this.loadConfigurations();
                        const newConfig = this.availableConfigs.find(c => c.name === config.name + ' Copy');
                        if (newConfig) {
                            this.selectConfiguration(newConfig.id);
                            this.showConfigBreakdown();
                        }
                    } catch (err) {
                        this.app.showToast(err.message, 'error');
                    }
                });
            }
        } else {
            const saveBtn = document.getElementById('save-config');
            if (saveBtn) {
                saveBtn.addEventListener('click', () => {
                    this.saveCurrentConfigChanges(config);
                });
            }
        }
        
        modal.style.display = 'flex';
    }

    async saveCurrentConfigChanges(config) {
        // TODO: Implement save functionality
        // This should collect all the rule toggles and custom settings
        // and send them to the backend to update the config
        this.app.showToast('Save functionality will be implemented in Phase 4', 'info');
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

    // === NEW TOOLBAR UI FUNCTIONS ===

    updateConfigToolbar() {
        const config = this.availableConfigs.find(c => c.id === this.selectedConfig);
        if (!config) return;

        const nameEl = document.getElementById('config-selected-name');
        const categoryEl = document.getElementById('config-selected-category');
        const rulesEl = document.getElementById('config-selected-rules');
        
        if (nameEl) nameEl.textContent = config.name;
        
        // Update category as text (not badge)
        if (categoryEl) {
            const category = (config.category || config.type || '').toLowerCase();
            let categoryText = '';
            let categoryColor = '';
            
            if (category === 'built-in' || category === 'builtin') {
                categoryText = 'Built-in';
                categoryColor = '#a78bfa';
            } else if (category === 'personal') {
                categoryText = 'Personal';
                categoryColor = '#2dd4bf';
            } else if (category === 'team') {
                categoryText = 'Team';
                categoryColor = '#60a5fa';
            }
            
            if (categoryText) {
                categoryEl.textContent = categoryText;
                categoryEl.style.color = categoryColor;
                categoryEl.className = 'config-selected-category-text';
                categoryEl.style.display = 'inline';
            } else {
                categoryEl.style.display = 'none';
            }
        }
        
        // Update rule count
        if (rulesEl && config.rules) {
            const enabledRules = Object.values(config.rules).filter(r => r.enabled).length;
            rulesEl.textContent = `${enabledRules} active`;
        } else if (rulesEl) {
            rulesEl.textContent = '';
        }
    }

    buildConfigDropdown() {
        const container = document.getElementById('config-dropdown');
        if (!container) {
            console.warn('config-dropdown container not found');
            return;
        }

        if (!this.availableConfigs || this.availableConfigs.length === 0) {
            console.warn('No available configs to populate dropdown');
            container.innerHTML = '<div class="config-dropdown-item" style="padding: 12px 20px; color: var(--text-secondary);">No configurations available</div>';
            return;
        }

        container.innerHTML = '';

        const groups = {
            "BUILT-IN": this.availableConfigs.filter(c => {
                const category = c.category || c.type || '';
                return category.toLowerCase() === 'built-in' || category.toLowerCase() === 'builtin';
            }),
            "TEAM": this.availableConfigs.filter(c => {
                const category = c.category || c.type || '';
                return category.toLowerCase() === 'team';
            }),
            "PERSONAL": this.availableConfigs.filter(c => {
                const category = c.category || c.type || '';
                return category.toLowerCase() === 'personal';
            })
        };

        Object.entries(groups).forEach(([header, list]) => {
            if (!list.length) return;

            const h = document.createElement('h4');
            h.textContent = header;
            container.appendChild(h);

            list.forEach(cfg => {
                const div = document.createElement('div');
                const isSelected = cfg.id === this.selectedConfig;
                
                if (isSelected) {
                    div.className = 'config-dropdown-item config-dropdown-item-selected';
                } else {
                    div.className = 'config-dropdown-item';
                }
                
                div.style.display = 'flex';
                div.style.alignItems = 'center';
                div.style.gap = '8px';

                // Calculate rule count
                const enabledRules = cfg.rules ? Object.values(cfg.rules).filter(r => r.enabled).length : 0;
                const rulesText = enabledRules > 0 ? `${enabledRules} active` : '';

                div.innerHTML = `
                    <span style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;">${cfg.name}</span>
                    ${rulesText ? `<span class="config-rules-count">${rulesText}</span>` : ''}
                    ${isSelected ? '<span class="config-checkmark">✓</span>' : ''}
                `;

                div.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.selectConfiguration(cfg.id);
                    // Close dropdown after selection
                    container.classList.remove('visible');
                });

                container.appendChild(div);
            });
        });

        const createBtn = document.createElement('div');
        createBtn.className = 'config-dropdown-create';
        createBtn.textContent = '+ Create New Configuration';
        createBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showCreateConfigModal();
        });

        container.appendChild(createBtn);
    }

    initializeToolbarListeners() {
        const selectedButton = document.getElementById('config-selected-button');
        const manageBtn = document.getElementById('config-manage-btn');
        const dropdown = document.getElementById('config-dropdown');

        if (selectedButton) {
            selectedButton.addEventListener('click', (e) => {
                e.stopPropagation();
                const dropdownEl = document.getElementById('config-dropdown');
                if (dropdownEl) {
                    // Rebuild dropdown to ensure it's up to date
                    this.buildConfigDropdown();
                    dropdownEl.classList.toggle('visible');
                }
            });
        }

        if (manageBtn) {
            manageBtn.addEventListener('click', () => {
                this.showConfigBreakdown();
            });
        }

        // Close dropdown when clicking outside
        const handleClickOutside = (e) => {
            const dropdownEl = document.getElementById('config-dropdown');
            const buttonEl = document.getElementById('config-selected-button');
            if (dropdownEl && 
                !dropdownEl.contains(e.target) && 
                buttonEl && 
                !buttonEl.contains(e.target)) {
                dropdownEl.classList.remove('visible');
            }
        };
        
        // Use capture phase to ensure we catch the click
        document.addEventListener('click', handleClickOutside, true);
    }

    showCreateConfigModal() {
        // Close dropdown
        const dropdown = document.getElementById('config-dropdown');
        if (dropdown) {
            dropdown.classList.remove('visible');
        }
        
        // For now, open duplicate modal with the first built-in config as template
        // In a full implementation, this would open a dedicated create modal
        if (this.availableConfigs.length > 0) {
            const templateConfig = this.availableConfigs.find(c => c.category === 'built-in') || this.availableConfigs[0];
            this.openDuplicateModal(templateConfig.id);
        } else {
            this.app.showToast('No configuration templates available', 'info');
        }
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

