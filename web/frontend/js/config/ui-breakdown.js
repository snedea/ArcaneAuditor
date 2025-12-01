// ui-breakdown.js
import { ConfigAPI } from './api.js';

export class ConfigBreakdownUI {
    constructor(manager) {
        this.manager = manager;
        this.app = manager.app;
        
        // Store current state for filtering
        this.currentConfig = null;
        this.currentIsBuiltIn = false;
        this.allRules = [];
        
        // Store filter state to persist across refreshes
        this.savedFilterState = {
            search: '',
            status: 'all',
            severity: 'all'
        };

        // Escape key functionality
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.hide();
        });
    }

    /**
     * Helper to close the modal
     */
    hide() {
        const modal = document.getElementById('config-breakdown-modal');
        if (modal) modal.style.display = 'none';
    }

    /**
     * The main method to show the breakdown modal
     */
    show(configId) {
        const modal = document.getElementById('config-breakdown-modal');
        const content = document.getElementById('config-breakdown-content');
        const header = document.querySelector('.modal-header');
        
        // Access data from the manager
        const config = this.manager.availableConfigs.find(c => c.id === configId);
        
        if (!config) {
            this.app.showToast('Configuration not found', 'error');
            return;
        }
        
        // Check if config is built-in
        const category = (config.category || config.type || '').toLowerCase();
        const isBuiltIn = category === 'built-in' || category === 'builtin';
        const sourceName = isBuiltIn ? 'Built-in' : (category === 'team' ? 'Team' : 'Personal');
        
        // --- 1. RENDER HEADER ---
        if (header) {
            header.innerHTML = '';
            
            // Left: Title + Badge
            const leftSide = document.createElement('div');
            leftSide.className = 'modal-header-left';
            leftSide.innerHTML = `
                <h3 class="modal-title">${config.name}</h3>
                <span class="config-source-badge">${sourceName}</span>
            `;
            
            // Right: Action Bar
            const rightSide = document.createElement('div');
            rightSide.className = 'modal-header-right';
            
            let actionButtons = '';
            
            // Delete (only for Personal/Team)
            if (!isBuiltIn) {
                actionButtons += `<button id="delete-config" class="modal-action-btn delete-btn" title="Delete configuration">🗑️</button>`;
            }
            
            // Duplicate (always)
            actionButtons += `<button id="duplicate-config" class="modal-action-btn duplicate-btn" title="Duplicate configuration">📑</button>`;
            
            // Save (only for Personal/Team)
            if (!isBuiltIn) {
                actionButtons += `<button id="save-config" class="modal-action-btn save-btn" title="Save changes">💾 Save</button>`;
            }
            
            actionButtons += `<div class="modal-action-separator"></div>`;
            actionButtons += `<button id="close-config" class="modal-close" title="Close">×</button>`;
            
            rightSide.innerHTML = actionButtons;
            header.appendChild(leftSide);
            header.appendChild(rightSide);

            // Bind Header Events
            const delBtn = header.querySelector('#delete-config');
            const dupBtn = header.querySelector('#duplicate-config');
            const saveBtn = header.querySelector('#save-config');
            const closeBtn = header.querySelector('#close-config');

            if (delBtn) delBtn.onclick = () => {
                this.manager.requestDeleteConfiguration(config);
                modal.style.display = 'none';
            };
            if (dupBtn) dupBtn.onclick = () => {
                modal.style.display = 'none';
                this.manager.openDuplicateModal(config.id, 'Personal');
            };
            if (saveBtn) saveBtn.onclick = () => {
                // Save filter state before refreshing
                this.saveFilterState();
                this.manager.saveCurrentConfigChanges(config);
            };
            if (closeBtn) closeBtn.onclick = () => this.hide();
        }
        
        // Store current state for filtering
        this.currentConfig = config;
        this.currentIsBuiltIn = isBuiltIn;
        
        // --- 2. RENDER BODY (Rules) ---
        this.renderBody(config, isBuiltIn, content);
        
        // --- 3. RENDER FILTER TOOLBAR (after body so it's in the right place) ---
        this.renderFilterToolbar(content);
        
        // --- 4. RESTORE FILTER STATE (if we have saved state) ---
        this.restoreFilterState(content);
        
        // --- 5. BIND EVENTS (Only if not built-in) ---
        if (!isBuiltIn) {
            this.bindRuleEvents(content, config);
        }
        
        // --- 6. BIND FILTER EVENTS ---
        this.bindFilterEvents(content, config);
        
        modal.style.display = 'flex';
    }

    /**
     * Render the filter toolbar below the summary section
     */
    renderFilterToolbar(content) {
        // Remove existing toolbar if present
        const existingToolbar = content.querySelector('.config-filter-toolbar');
        if (existingToolbar) {
            existingToolbar.remove();
        }
        
        const toolbar = document.createElement('div');
        toolbar.className = 'config-filter-toolbar';
        toolbar.innerHTML = `
            <div class="config-filter-group">
                <input 
                    type="text" 
                    id="config-modal-search" 
                    class="config-filter-input" 
                    placeholder="Search rule names..."
                    autocomplete="off"
                />
            </div>
            <div class="config-filter-group">
                <label for="config-modal-filter-status">Status:</label>
                <select id="config-modal-filter-status" class="config-filter-select">
                    <option value="all">All</option>
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                </select>
            </div>
            <div class="config-filter-group">
                <label for="config-modal-filter-severity">Severity:</label>
                <select id="config-modal-filter-severity" class="config-filter-select">
                    <option value="all">All</option>
                    <option value="action">Action</option>
                    <option value="advice">Advice</option>
                </select>
            </div>
        `;
        
        // Insert after the summary section (first config-breakdown-section)
        const summarySection = content.querySelector('.config-breakdown-section');
        if (summarySection && summarySection.nextSibling) {
            content.insertBefore(toolbar, summarySection.nextSibling);
        } else if (summarySection) {
            summarySection.insertAdjacentElement('afterend', toolbar);
        } else {
            content.appendChild(toolbar);
        }
    }

    /**
     * Get the effective severity for a rule (checks override first, then defaults to ADVICE)
     */
    getRuleSeverity(ruleConfig) {
        // Check severity_override first
        if (ruleConfig.severity_override) {
            return ruleConfig.severity_override;
        }
        // Default to ADVICE if no override
        return 'ADVICE';
    }

    /**
     * Filter rules based on search and filter criteria
     */
    filterRules(allRules, searchTerm, statusFilter, severityFilter) {
        return allRules.filter(([ruleName, ruleConfig]) => {
            // Search filter
            if (searchTerm) {
                const searchLower = searchTerm.toLowerCase();
                if (!ruleName.toLowerCase().includes(searchLower)) {
                    return false;
                }
            }
            
            // Status filter
            if (statusFilter !== 'all') {
                const isEnabled = ruleConfig.enabled && !ruleConfig._is_ghost;
                if (statusFilter === 'enabled' && !isEnabled) return false;
                if (statusFilter === 'disabled' && isEnabled) return false;
            }
            
            // Severity filter
            if (severityFilter !== 'all') {
                const severity = this.getRuleSeverity(ruleConfig);
                if (severity.toLowerCase() !== severityFilter.toLowerCase()) {
                    return false;
                }
            }
            
            return true;
        });
    }

    renderBody(config, isBuiltIn, content) {
        const rules = config.rules || {};
        const enabledRules = Object.entries(rules).filter(([_, r]) => r.enabled && !r._is_ghost).length;
        const disabledRules = Object.entries(rules).filter(([_, r]) => !r.enabled && !r._is_ghost).length;
        const allRules = Object.entries(rules).sort(([a], [b]) => a.localeCompare(b));
        
        // Store allRules for filtering
        this.allRules = allRules;

        // Clear existing content
        content.innerHTML = '';

        // Summary section
        const summarySection = document.createElement('div');
        summarySection.className = 'config-breakdown-section';
        summarySection.innerHTML = `
            <div class="config-summary-grid">
                <div class="summary-card enabled"><div class="summary-number">${enabledRules}</div><div class="summary-label">Enabled Rules</div></div>
                <div class="summary-card disabled"><div class="summary-number">${disabledRules}</div><div class="summary-label">Disabled Rules</div></div>
                <div class="summary-card total"><div class="summary-number">${Object.keys(rules).length}</div><div class="summary-label">Total Rules</div></div>
            </div>
        `;
        content.appendChild(summarySection);

        // Filter toolbar will be inserted after summary section by renderFilterToolbar

        // Rules section
        const rulesSection = document.createElement('div');
        rulesSection.className = 'config-breakdown-section';
        rulesSection.innerHTML = `
            <h4>📋 Rules</h4>
            <div class="rule-breakdown"></div>
        `;
        content.appendChild(rulesSection);
        
        // Render the rules list
        const ruleBreakdown = rulesSection.querySelector('.rule-breakdown');
        this.renderRuleList(ruleBreakdown, allRules, isBuiltIn);
    }

    /**
     * Render the list of rules (used for initial render and filtered updates)
     * @param {HTMLElement} container - The container to render rules into
     * @param {Array} rulesToRender - Array of [ruleName, ruleConfig] tuples
     * @param {boolean} isBuiltIn - Whether this is a built-in config
     * @param {boolean} skipEventBinding - If true, skip binding events (for use during restore)
     */
    renderRuleList(container, rulesToRender, isBuiltIn, skipEventBinding = false) {
        if (!container) return;
        
        container.innerHTML = '';
        
        rulesToRender.forEach(([ruleName, ruleConfig]) => {
            const isEnabled = ruleConfig.enabled;
            const severity = this.getRuleSeverity(ruleConfig);
            const customSettings = ruleConfig.custom_settings || {};
            const settingsText = Object.keys(customSettings).length > 0 ? JSON.stringify(customSettings, null, 2) : '';
            const isGhost = ruleConfig._is_ghost === true;

            const enabledClass = isEnabled ? 'enabled' : 'disabled';
            const ghostClass = isGhost ? 'ghost-rule' : '';

            const hasCustomSettings = Object.keys(customSettings).length > 0;
            const configureIcon = hasCustomSettings ? '🛠️' : '⚙️';
            const configureText = hasCustomSettings ? 'Customized' : 'Configure';

            const ruleHtml = `
                <div class="rule-item ${enabledClass} ${ghostClass}" data-rule="${ruleName}">
                    <div class="rule-row-header">
                        <div class="rule-name-container">
                            <div class="rule-name">
                                ${ruleName}
                                ${isGhost ? '<span class="ghost-warning-badge-inline">⚠️ Rule not found in runtime (not counted or used)</span>' : ''}
                            </div>
                        </div>
                        <div class="rule-controls-container">
                            ${!isBuiltIn && !isGhost ? `
                                <select class="rule-severity-select rule-severity-${severity.toLowerCase()}" data-rule="${ruleName}" data-severity="${severity}">
                                    <option value="ADVICE" ${severity === 'ADVICE' ? 'selected' : ''}>ADVICE</option>
                                    <option value="ACTION" ${severity === 'ACTION' ? 'selected' : ''}>ACTION</option>
                                </select>
                                <button class="rule-configure-btn ${hasCustomSettings ? 'modified' : ''}" data-rule="${ruleName}" type="button">
                                    ${configureIcon} ${configureText} <span class="configure-chevron" data-rule="${ruleName}">▼</span>
                                </button>
                            ` : ''}
                            ${!isBuiltIn && isGhost ? `<button class="rule-delete-btn" data-rule="${ruleName}" type="button" title="Remove ghost rule">🗑️ Remove</button>` : ''}
                            ${!isBuiltIn ? `
                                <div class="rule-toggle-switch ${isGhost ? 'disabled' : (isEnabled ? 'enabled' : 'disabled')}" data-rule="${ruleName}" ${isGhost ? 'disabled' : ''}>
                                    <div class="toggle-track"><span class="toggle-thumb"></span></div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    ${!isBuiltIn && !isGhost ? `
                        <div class="rule-settings-panel" data-rule="${ruleName}">
                            <textarea class="rule-settings-json" data-rule="${ruleName}" placeholder='{ "mode": "strict" }'>${settingsText}</textarea>
                            <div class="rule-settings-error" data-rule="${ruleName}">Invalid JSON format</div>
                        </div>
                    ` : ''}
                </div>
            `;
            
            container.insertAdjacentHTML('beforeend', ruleHtml);
        });
        
        // Re-bind events after re-rendering (unless we're skipping for restore)
        if (!skipEventBinding && !isBuiltIn && this.currentConfig) {
            this.bindRuleEvents(container.closest('#config-breakdown-content'), this.currentConfig);
        }
    }

    bindRuleEvents(content, config) {
        // Toggle Switches
        content.querySelectorAll('.rule-toggle-switch:not([disabled])').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const ruleName = toggle.dataset.rule;
                const ruleItem = toggle.closest('.rule-item');
                const isCurrentlyEnabled = ruleItem.classList.contains('enabled');
                
                // Toggle UI state
                ruleItem.classList.toggle('enabled', !isCurrentlyEnabled);
                ruleItem.classList.toggle('disabled', isCurrentlyEnabled);
                toggle.classList.toggle('enabled', !isCurrentlyEnabled);
                toggle.classList.toggle('disabled', isCurrentlyEnabled);
                
                // Update Config Data
                if (config.rules[ruleName]) {
                    config.rules[ruleName].enabled = !isCurrentlyEnabled;
                }
            });
        });
        
        // Ghost Rule Deletion
        content.querySelectorAll('.rule-delete-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const ruleName = btn.dataset.rule;
                if (confirm(`Remove ghost rule "${ruleName}"?`)) {
                    try {
                        if (config.rules && config.rules[ruleName]) delete config.rules[ruleName];
                        
                        // Use API directly
                        await ConfigAPI.save(config);
                        
                        btn.closest('.rule-item').remove();
                        await this.manager.loadConfigurations();
                        this.show(config.id); // Refresh modal
                        this.app.showToast('Ghost rule removed', 'success');
                    } catch (error) {
                        console.error('Error removing ghost rule:', error);
                        this.app.showToast('Failed to remove ghost rule', 'error');
                    }
                }
            });
        });

        // Severity Dropdowns
        content.querySelectorAll('.rule-severity-select').forEach(select => {
            select.addEventListener('change', (e) => {
                const ruleName = select.dataset.rule;
                const newSeverity = select.value;
                if (config.rules[ruleName]) config.rules[ruleName].severity_override = newSeverity;
                select.className = `rule-severity-select rule-severity-${newSeverity.toLowerCase()}`;
            });
        });

        // Expand/Collapse Settings
        content.querySelectorAll('.rule-configure-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const ruleName = btn.dataset.rule;
                const panel = content.querySelector(`.rule-settings-panel[data-rule="${ruleName}"]`);
                const chevron = btn.querySelector('.configure-chevron');
                if (panel) {
                    panel.classList.toggle('expanded');
                    if (chevron) chevron.textContent = panel.classList.contains('expanded') ? '▲' : '▼';
                }
            });
        });

        // JSON Validation
        content.querySelectorAll('.rule-settings-json').forEach(textarea => {
            textarea.addEventListener('blur', () => this.handleJsonBlur(textarea, config));
        });
    }

    /**
     * Save current filter state
     */
    saveFilterState() {
        const content = document.getElementById('config-breakdown-content');
        if (!content) return;
        
        const searchInput = content.querySelector('#config-modal-search');
        const statusFilter = content.querySelector('#config-modal-filter-status');
        const severityFilter = content.querySelector('#config-modal-filter-severity');
        
        this.savedFilterState = {
            search: searchInput ? searchInput.value.trim() : '',
            status: statusFilter ? statusFilter.value : 'all',
            severity: severityFilter ? severityFilter.value : 'all'
        };
    }

    /**
     * Restore saved filter state and apply filters
     */
    restoreFilterState(content) {
        if (!this.savedFilterState) return;
        
        const searchInput = content.querySelector('#config-modal-search');
        const statusFilter = content.querySelector('#config-modal-filter-status');
        const severityFilter = content.querySelector('#config-modal-filter-severity');
        const ruleBreakdown = content.querySelector('.rule-breakdown');
        
        if (!ruleBreakdown) return;
        
        // Restore values
        if (searchInput && this.savedFilterState.search) {
            searchInput.value = this.savedFilterState.search;
        }
        if (statusFilter && this.savedFilterState.status !== 'all') {
            statusFilter.value = this.savedFilterState.status;
        }
        if (severityFilter && this.savedFilterState.severity !== 'all') {
            severityFilter.value = this.savedFilterState.severity;
        }
        
        // Apply filters if any are active
        if (this.savedFilterState.search || 
            this.savedFilterState.status !== 'all' || 
            this.savedFilterState.severity !== 'all') {
            const filteredRules = this.filterRules(
                this.allRules,
                this.savedFilterState.search,
                this.savedFilterState.status,
                this.savedFilterState.severity
            );
            // Skip event binding here since bindRuleEvents will be called after restoreFilterState
            this.renderRuleList(ruleBreakdown, filteredRules, this.currentIsBuiltIn, true);
        }
    }

    /**
     * Bind event listeners for search and filter controls
     */
    bindFilterEvents(content, config) {
        const searchInput = content.querySelector('#config-modal-search');
        const statusFilter = content.querySelector('#config-modal-filter-status');
        const severityFilter = content.querySelector('#config-modal-filter-severity');
        const ruleBreakdown = content.querySelector('.rule-breakdown');
        
        if (!ruleBreakdown) return;
        
        const applyFilters = () => {
            const searchTerm = searchInput ? searchInput.value.trim() : '';
            const statusValue = statusFilter ? statusFilter.value : 'all';
            const severityValue = severityFilter ? severityFilter.value : 'all';
            
            // Save filter state whenever it changes
            this.savedFilterState = {
                search: searchTerm,
                status: statusValue,
                severity: severityValue
            };
            
            const filteredRules = this.filterRules(this.allRules, searchTerm, statusValue, severityValue);
            // Re-render the list (this clears and recreates elements, so we need to rebind)
            // Don't skip event binding - we need to rebind since elements were recreated
            this.renderRuleList(ruleBreakdown, filteredRules, this.currentIsBuiltIn, false);
        };
        
        if (searchInput) {
            searchInput.addEventListener('input', applyFilters);
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', applyFilters);
        }
        
        if (severityFilter) {
            severityFilter.addEventListener('change', applyFilters);
        }
    }

    handleJsonBlur(textarea, config) {
        const ruleName = textarea.dataset.rule;
        const errorDiv = document.querySelector(`.rule-settings-error[data-rule="${ruleName}"]`);
        const value = textarea.value.trim();
        const configureBtn = document.querySelector(`.rule-configure-btn[data-rule="${ruleName}"]`);
        const chevronHtml = `<span class="configure-chevron" data-rule="${ruleName}">▼</span>`;

        // Clear error
        textarea.classList.remove('json-invalid', 'json-valid');
        if (errorDiv) errorDiv.style.display = 'none';

        if (!value) {
            if (config.rules[ruleName]) config.rules[ruleName].custom_settings = {};
            if (configureBtn) {
                configureBtn.classList.remove('modified');
                configureBtn.innerHTML = `⚙️ Configure ${chevronHtml}`;
            }
            return;
        }

        try {
            const parsed = JSON.parse(value);
            const isEmpty = Object.keys(parsed).length === 0;
            textarea.value = isEmpty ? '{}' : JSON.stringify(parsed, null, 2);
            
            if (config.rules[ruleName]) config.rules[ruleName].custom_settings = isEmpty ? {} : parsed;

            textarea.classList.add('json-valid');
            setTimeout(() => textarea.classList.remove('json-valid'), 1000);

            if (configureBtn) {
                if (isEmpty) {
                    configureBtn.classList.remove('modified');
                    configureBtn.innerHTML = `⚙️ Configure ${chevronHtml}`;
                } else {
                    configureBtn.classList.add('modified');
                    configureBtn.innerHTML = `🛠️ Customized ${chevronHtml}`;
                }
            }
        } catch (err) {
            textarea.classList.add('json-invalid');
            if (errorDiv) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = `Invalid JSON: ${err.message}`;
            }
        }
    }
}