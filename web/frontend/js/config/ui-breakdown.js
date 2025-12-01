// ui-breakdown.js
import { ConfigAPI } from './api.js';

export class ConfigBreakdownUI {
    constructor(manager) {
        this.manager = manager;
        this.app = manager.app;

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
            actionButtons += `<button id="duplicate-config" class="modal-action-btn duplicate-btn" title="Duplicate configuration">📋</button>`;
            
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
                this.manager.saveCurrentConfigChanges(config);
            };
            if (closeBtn) closeBtn.onclick = () => this.hide();
        }
        
        // --- 2. RENDER BODY (Rules) ---
        this.renderBody(config, isBuiltIn, content);
        
        // --- 3. BIND EVENTS (Only if not built-in) ---
        if (!isBuiltIn) {
            this.bindRuleEvents(content, config);
        }
        
        modal.style.display = 'flex';
    }

    renderBody(config, isBuiltIn, content) {
        const rules = config.rules || {};
        const enabledRules = Object.entries(rules).filter(([_, r]) => r.enabled && !r._is_ghost).length;
        const disabledRules = Object.entries(rules).filter(([_, r]) => !r.enabled && !r._is_ghost).length;
        const allRules = Object.entries(rules).sort(([a], [b]) => a.localeCompare(b));

        let html = `
            <div class="config-breakdown-section">
                <div class="config-summary-grid">
                    <div class="summary-card enabled"><div class="summary-number">${enabledRules}</div><div class="summary-label">Enabled Rules</div></div>
                    <div class="summary-card disabled"><div class="summary-number">${disabledRules}</div><div class="summary-label">Disabled Rules</div></div>
                    <div class="summary-card total"><div class="summary-number">${Object.keys(rules).length}</div><div class="summary-label">Total Rules</div></div>
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
            const settingsText = Object.keys(customSettings).length > 0 ? JSON.stringify(customSettings, null, 2) : '';
            const isGhost = ruleConfig._is_ghost === true;

            const enabledClass = isEnabled ? 'enabled' : 'disabled';
            const ghostClass = isGhost ? 'ghost-rule' : '';

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
        });

        html += `</div></div>`;
        content.innerHTML = html;
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