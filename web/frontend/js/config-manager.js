// Configuration management for Arcane Auditor web interface

import { getLastSelectedConfig, saveSelectedConfig } from './utils.js';

export class ConfigManager {
    pendingDuplicateId = null;
    productionTemplateId = null;
    toolbarListenersInitialized = false;
    toolbarClickHandler = null;
    toolbarManageHandler = null;
    toolbarClickOutsideHandler = null;

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
        
        // Check if config is built-in (check both category and type, handle both 'built-in' and 'builtin')
        const category = (config.category || config.type || '').toLowerCase();
        const isBuiltIn = category === 'built-in' || category === 'builtin';
        const sourceName = isBuiltIn ? 'Built-in' : (category === 'team' ? 'Team' : 'Personal');
        
        // Update modal header with new layout
        if (header) {
            // Clear existing header content
            header.innerHTML = '';
            
            // Left side: Title + Badge
            const leftSide = document.createElement('div');
            leftSide.className = 'modal-header-left';
            leftSide.innerHTML = `
                <h3 class="modal-title">${config.name}</h3>
                <span class="config-source-badge">${sourceName}</span>
            `;
            
            // Right side: Action Bar
            const rightSide = document.createElement('div');
            rightSide.className = 'modal-header-right';
            
            let actionButtons = '';
            
            // Delete button (only for Personal/Team)
            if (!isBuiltIn) {
                actionButtons += `<button id="delete-config" class="modal-action-btn delete-btn" title="Delete configuration">🗑️</button>`;
            }
            
            // Duplicate button (always visible)
            actionButtons += `<button id="duplicate-config" class="modal-action-btn duplicate-btn" title="Duplicate configuration">📋</button>`;
            
            // Save button (only for Personal/Team)
            if (!isBuiltIn) {
                actionButtons += `<button id="save-config" class="modal-action-btn save-btn" title="Save changes">💾 Save</button>`;
            }
            
            // Separator
            actionButtons += `<div class="modal-action-separator"></div>`;
            
            // Close button
            actionButtons += `<button class="modal-close" onclick="hideConfigBreakdown()" title="Close">×</button>`;
            
            rightSide.innerHTML = actionButtons;
            
            header.appendChild(leftSide);
            header.appendChild(rightSide);
        }
        
        const rules = config.rules || {};
        const enabledRules = Object.entries(rules).filter(([_, ruleConfig]) => ruleConfig.enabled).length;
        const disabledRules = Object.entries(rules).filter(([_, ruleConfig]) => !ruleConfig.enabled).length;
        
        // Merge all rules into single list, sorted alphabetically
        const allRules = Object.entries(rules).sort(([a], [b]) => a.localeCompare(b));
        
        let html = `
            <div class="config-breakdown-section">
                <div class="config-summary-grid">
                    <div class="summary-card enabled">
                        <div class="summary-number">${enabledRules}</div>
                        <div class="summary-label">Enabled Rules</div>
                    </div>
                    <div class="summary-card disabled">
                        <div class="summary-number">${disabledRules}</div>
                        <div class="summary-label">Disabled Rules</div>
                    </div>
                    <div class="summary-card total">
                        <div class="summary-number">${Object.keys(rules).length}</div>
                        <div class="summary-label">Total Rules</div>
                    </div>
                </div>
            </div>
            <div class="config-breakdown-section">
                <h4>📋 Rules</h4>
                <div class="rule-breakdown">
        `;
        
        allRules.forEach(([ruleName, ruleConfig]) => {
            const isEnabled = ruleConfig.enabled;
            const severity = ruleConfig.severity_override || 'ADVICE';
            const customSettings = ruleConfig.custom_settings || {};
            const settingsText = Object.keys(customSettings).length > 0 
                ? JSON.stringify(customSettings, null, 2) 
                : '';
            const isGhost = ruleConfig._is_ghost === true;
            
            const readonlyAttr = isBuiltIn ? 'readonly' : '';
            const enabledClass = isEnabled ? 'enabled' : 'disabled';
            const ghostClass = isGhost ? 'ghost-rule' : '';
            
            // Toggle switch: show for non-built-in rules (including ghost rules, but disabled for ghosts)
            const toggleState = isGhost ? 'disabled' : (isEnabled ? 'enabled' : 'disabled');
            const toggleDisabled = isGhost ? 'disabled' : '';
            
            // Check if rule has custom settings (not empty object)
            const hasCustomSettings = Object.keys(customSettings).length > 0;
            const configureIcon = hasCustomSettings ? '🛠️' : '⚙️';
            const configureText = hasCustomSettings ? 'Customized' : 'Configure';
            
            html += `
                <div class="rule-item ${enabledClass} ${ghostClass}" data-rule="${ruleName}">
                    <div class="rule-row-header">
                        <div class="rule-name-container">
                            <div class="rule-name">
                                ${ruleName}
                                ${isGhost ? '<span class="ghost-warning-badge-inline">⚠️ Rule not found in runtime</span>' : ''}
                            </div>
                        </div>
                        <div class="rule-controls-container">
                            ${!isBuiltIn && !isGhost ? `
                                <select class="rule-severity-select rule-severity-${severity.toLowerCase()}" data-rule="${ruleName}" data-severity="${severity}">
                                    <option value="ADVICE" ${severity === 'ADVICE' ? 'selected' : ''}>ADVICE</option>
                                    <option value="ACTION" ${severity === 'ACTION' ? 'selected' : ''}>ACTION</option>
                                </select>
                                <button class="rule-configure-btn ${hasCustomSettings ? 'modified' : ''}" data-rule="${ruleName}" type="button">
                                    ${configureIcon} ${configureText}
                                    <span class="configure-chevron" data-rule="${ruleName}">▼</span>
                                </button>
                            ` : ''}
                            ${!isBuiltIn && isGhost ? `
                                <button class="rule-delete-btn" data-rule="${ruleName}" type="button" title="Remove ghost rule">
                                    🗑️ Remove
                                </button>
                            ` : ''}
                            ${!isBuiltIn ? `
                                <div class="rule-toggle-switch ${toggleState}" data-rule="${ruleName}" ${toggleDisabled}>
                                    <div class="toggle-track">
                                        <span class="toggle-thumb"></span>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    ${!isBuiltIn && !isGhost ? `
                        <div class="rule-settings-panel" data-rule="${ruleName}">
                            <textarea class="rule-settings-json" data-rule="${ruleName}" placeholder='{ "mode": "strict" }' ${readonlyAttr}>${settingsText}</textarea>
                            <div class="rule-settings-error" data-rule="${ruleName}">Invalid JSON format</div>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
        
        content.innerHTML = html;
        
        // Wire up toggle switches for non-built-in configs
        if (!isBuiltIn) {
            const toggleSwitches = content.querySelectorAll('.rule-toggle-switch:not([disabled])');
            toggleSwitches.forEach(toggle => {
                toggle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const ruleName = toggle.dataset.rule;
                    const ruleItem = toggle.closest('.rule-item');
                    const isCurrentlyEnabled = ruleItem.classList.contains('enabled');
                    
                    // Toggle the state
                    if (isCurrentlyEnabled) {
                        ruleItem.classList.remove('enabled');
                        ruleItem.classList.add('disabled');
                        toggle.classList.remove('enabled');
                        toggle.classList.add('disabled');
                        if (config.rules[ruleName]) {
                            config.rules[ruleName].enabled = false;
                        }
                    } else {
                        ruleItem.classList.remove('disabled');
                        ruleItem.classList.add('enabled');
                        toggle.classList.remove('disabled');
                        toggle.classList.add('enabled');
                        if (config.rules[ruleName]) {
                            config.rules[ruleName].enabled = true;
                        }
                    }
                });
            });
            
            // Wire up delete buttons for ghost rules
            const deleteButtons = content.querySelectorAll('.rule-delete-btn');
            deleteButtons.forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const ruleName = btn.dataset.rule;
                    const ruleItem = btn.closest('.rule-item');
                    
                    if (confirm(`Remove ghost rule "${ruleName}" from this configuration?`)) {
                        try {
                            // Remove from config
                            if (config.rules && config.rules[ruleName]) {
                                delete config.rules[ruleName];
                            }
                            
                            // Save the config via API
                            const response = await fetch(`/api/config/${config.id}/save`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ config: config })
                            });
                            
                            if (!response.ok) {
                                throw new Error('Failed to save configuration');
                            }
                            
                            // Remove from DOM
                            ruleItem.remove();
                            
                            // Refresh configs and breakdown
                            await this.loadConfigurations();
                            this.showConfigBreakdown();
                            
                            this.app.showToast('Ghost rule removed', 'success');
                        } catch (error) {
                            console.error('Error removing ghost rule:', error);
                            this.app.showToast('Failed to remove ghost rule', 'error');
                        }
                    }
                });
            });
            
            // Wire up severity dropdowns
            const severitySelects = content.querySelectorAll('.rule-severity-select');
            severitySelects.forEach(select => {
                select.addEventListener('change', (e) => {
                    e.stopPropagation();
                    const ruleName = select.dataset.rule;
                    const newSeverity = select.value;
                    
                    // Update config
                    if (config.rules[ruleName]) {
                        config.rules[ruleName].severity_override = newSeverity;
                    }
                    
                    // Update the select's data attribute and class for color
                    select.dataset.severity = newSeverity;
                    select.classList.remove('rule-severity-advice', 'rule-severity-action');
                    select.classList.add(`rule-severity-${newSeverity.toLowerCase()}`);
                });
            });
            
            // Wire up configure buttons
            const configureButtons = content.querySelectorAll('.rule-configure-btn');
            configureButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const ruleName = btn.dataset.rule;
                    const settingsPanel = content.querySelector(`.rule-settings-panel[data-rule="${ruleName}"]`);
                    const chevron = btn.querySelector('.configure-chevron');
                    
                    if (settingsPanel) {
                        const isExpanded = settingsPanel.classList.contains('expanded');
                        
                        if (isExpanded) {
                            // Collapse
                            settingsPanel.classList.remove('expanded');
                            if (chevron) chevron.textContent = '▼';
                        } else {
                            // Expand
                            settingsPanel.classList.add('expanded');
                            if (chevron) chevron.textContent = '▲';
                        }
                    }
                });
            });
            
            // Wire up JSON validation on textarea blur
            const settingsTextareas = content.querySelectorAll('.rule-settings-json');
            settingsTextareas.forEach(textarea => {
                textarea.addEventListener('blur', (e) => {
                    const ruleName = textarea.dataset.rule;
                    const errorDiv = content.querySelector(`.rule-settings-error[data-rule="${ruleName}"]`);
                    const value = textarea.value.trim();
                    
                    // Clear previous error state
                    textarea.classList.remove('json-invalid', 'json-valid');
                    if (errorDiv) {
                        errorDiv.style.display = 'none';
                    }
                    
                    // If empty, that's valid (no custom settings)
                    if (!value) {
                        if (config.rules[ruleName]) {
                            config.rules[ruleName].custom_settings = {};
                        }
                        // Update modified indicator (change icon and text)
                        const configureBtn = content.querySelector(`.rule-configure-btn[data-rule="${ruleName}"]`);
                        if (configureBtn) {
                            configureBtn.classList.remove('modified');
                            const chevron = configureBtn.querySelector('.configure-chevron');
                            const chevronHtml = chevron ? chevron.outerHTML : `<span class="configure-chevron" data-rule="${ruleName}">▼</span>`;
                            configureBtn.innerHTML = `⚙️ Configure ${chevronHtml}`;
                        }
                        return;
                    }
                    
                    // Try to parse JSON
                    try {
                        const parsed = JSON.parse(value);
                        
                        // Check if it's an empty object
                        const isEmpty = Object.keys(parsed).length === 0;
                        
                        // Format it nicely (prettify)
                        const formatted = isEmpty ? '{}' : JSON.stringify(parsed, null, 2);
                        textarea.value = formatted;
                        
                        // Update config
                        if (config.rules[ruleName]) {
                            config.rules[ruleName].custom_settings = isEmpty ? {} : parsed;
                        }
                        
                        // Show valid state (brief green border)
                        textarea.classList.add('json-valid');
                        setTimeout(() => {
                            textarea.classList.remove('json-valid');
                        }, 1000);
                        
                        // Update modified indicator (change icon and text)
                        const configureBtn = content.querySelector(`.rule-configure-btn[data-rule="${ruleName}"]`);
                        if (configureBtn) {
                            const chevron = configureBtn.querySelector('.configure-chevron');
                            const chevronHtml = chevron ? chevron.outerHTML : `<span class="configure-chevron" data-rule="${ruleName}">▼</span>`;
                            
                            if (isEmpty) {
                                configureBtn.classList.remove('modified');
                                configureBtn.innerHTML = `⚙️ Configure ${chevronHtml}`;
                                configureBtn.classList.remove('modified');
                            } else {
                                configureBtn.classList.add('modified');
                                configureBtn.innerHTML = `🛠️ Customized ${chevronHtml}`;
                            }
                        }
                    } catch (err) {
                        // Invalid JSON - show red border and error message
                        textarea.classList.add('json-invalid');
                        if (errorDiv) {
                            errorDiv.style.display = 'block';
                            errorDiv.textContent = `Invalid JSON: ${err.message}`;
                        }
                    }
                });
            });
        }
        
        // Event handlers are now wired up in the header generation code above
        
        modal.style.display = 'flex';
    }

    showModalMenu(config, triggerElement) {
        // Close any existing menu
        const existingMenu = document.querySelector('.config-modal-menu-popover');
        if (existingMenu) {
            existingMenu.remove();
        }

        const menu = document.createElement('div');
        menu.className = 'config-modal-menu-popover';
        menu.style.position = 'absolute';
        menu.style.visibility = 'hidden';

        // Check if config is built-in (check both category and type, handle both 'built-in' and 'builtin')
        const category = (config.category || config.type || '').toLowerCase();
        const isBuiltIn = category === 'built-in' || category === 'builtin';
        
        // Safety check: This function should never be called for built-in configs
        if (isBuiltIn) {
            return;
        }
        
        const actions = [
            { action: 'duplicate', label: 'Duplicate' },
            { action: 'delete', label: 'Delete', danger: true }
        ];

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
        menu.style.zIndex = '1001'; // Above modal

        const handleAction = (action) => {
            switch (action) {
                case 'duplicate':
                    // Close the breakdown modal
                    const modal = document.getElementById('config-breakdown-modal');
                    if (modal) {
                        modal.style.display = 'none';
                    }
                    // Open the duplicate modal so user can name the new config
                    this.openDuplicateModal(config.id, 'Personal');
                    break;
                case 'delete':
                    this.requestDeleteConfiguration(config);
                    // Close modal after delete
                    const deleteModal = document.getElementById('config-breakdown-modal');
                    if (deleteModal) {
                        deleteModal.style.display = 'none';
                    }
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
        };

        menu.addEventListener('click', handleMenuClick);
        setTimeout(() => {
            document.addEventListener('click', handleClickOutside);
        }, 0);
        document.addEventListener('keydown', handleEscape);
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
                categoryEl.className = 'config-selected-category-text config-category-built-in';
            } else if (category === 'personal') {
                categoryText = 'Personal';
                categoryEl.className = 'config-selected-category-text config-category-personal';
            } else if (category === 'team') {
                categoryText = 'Team';
                categoryEl.className = 'config-selected-category-text config-category-team';
            }
            
            if (categoryText) {
                categoryEl.textContent = categoryText;
                categoryEl.style.display = 'inline';
            } else {
                categoryEl.style.display = 'none';
            }
        }
        
        // Update rule count
        if (rulesEl && config.rules) {
            const enabledRules = Object.values(config.rules).filter(r => r.enabled).length;
            const disabledRules = Object.values(config.rules).filter(r => !r.enabled).length;
            
            if (disabledRules > 0) {
                rulesEl.innerHTML = `
                    <span class="config-rule-active">${enabledRules} rules active</span>
                    <span class="config-rule-separator config-rule-separator-button">|</span>
                    <span class="config-rule-disabled">${disabledRules} Off</span>
                `;
            } else {
                rulesEl.innerHTML = `
                    <span class="config-rule-active">${enabledRules} rules active</span>
                `;
            }
            rulesEl.className = 'config-rules-count bg-transparent';
        } else if (rulesEl) {
            rulesEl.innerHTML = '';
            rulesEl.className = 'config-rules-count bg-transparent';
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
                const disabledRules = cfg.rules ? Object.values(cfg.rules).filter(r => !r.enabled).length : 0;
                const hasRules = cfg.rules && Object.keys(cfg.rules).length > 0;
                
                let rulesHtml = '';
                if (hasRules) {
                    rulesHtml = `
                        <div class="config-rule-active-container">
                            <span class="config-rule-active">${enabledRules} Active</span>
                        </div>
                        <div class="config-rule-off-container">
                            ${disabledRules > 0 ? `
                                <span class="config-rule-separator">|</span>
                                <span class="config-rule-disabled">${disabledRules} Off</span>
                            ` : ''}
                        </div>
                    `;
                } else {
                    rulesHtml = `
                        <div class="config-rule-active-container"></div>
                        <div class="config-rule-off-container"></div>
                    `;
                }

                div.innerHTML = `
                    <span class="config-dropdown-name">${cfg.name}</span>
                    <div class="config-dropdown-stats">
                        ${hasRules ? `<span class="config-rules-count bg-transparent">${rulesHtml}</span>` : '<span class="config-rules-count bg-transparent"></span>'}
                        <span class="config-checkmark-slot" style="width: 24px; display: flex; align-items: center; justify-content: flex-end; flex-shrink: 0;">
                            ${isSelected ? '<span class="config-checkmark">✓</span>' : ''}
                        </span>
                    </div>
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
        // Remove old listeners if they exist
        if (this.toolbarListenersInitialized) {
            this.removeToolbarListeners();
        }

        const selectedButton = document.getElementById('config-selected-button');
        const manageBtn = document.getElementById('config-manage-btn');
        const dropdown = document.getElementById('config-dropdown');

        if (selectedButton) {
            this.toolbarClickHandler = (e) => {
                e.stopPropagation();
                const dropdownEl = document.getElementById('config-dropdown');
                if (dropdownEl) {
                    // Rebuild dropdown to ensure it's up to date
                    this.buildConfigDropdown();
                    dropdownEl.classList.toggle('visible');
                }
            };
            selectedButton.addEventListener('click', this.toolbarClickHandler);
        }

        if (manageBtn) {
            this.toolbarManageHandler = () => {
                this.showConfigBreakdown();
            };
            manageBtn.addEventListener('click', this.toolbarManageHandler);
        }

        // Close dropdown when clicking outside
        this.toolbarClickOutsideHandler = (e) => {
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
        document.addEventListener('click', this.toolbarClickOutsideHandler, true);
        
        this.toolbarListenersInitialized = true;
    }

    removeToolbarListeners() {
        const selectedButton = document.getElementById('config-selected-button');
        const manageBtn = document.getElementById('config-manage-btn');

        if (selectedButton && this.toolbarClickHandler) {
            selectedButton.removeEventListener('click', this.toolbarClickHandler);
            this.toolbarClickHandler = null;
        }

        if (manageBtn && this.toolbarManageHandler) {
            manageBtn.removeEventListener('click', this.toolbarManageHandler);
            this.toolbarManageHandler = null;
        }

        if (this.toolbarClickOutsideHandler) {
            document.removeEventListener('click', this.toolbarClickOutsideHandler, true);
            this.toolbarClickOutsideHandler = null;
        }

        this.toolbarListenersInitialized = false;
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

// Disabled: Close modal when clicking outside
// Removed to prevent accidental data loss - modal now only closes via X button or Escape key

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        window.hideConfigBreakdown();
    }
});

