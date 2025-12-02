// templates.js
export const Templates = {
    /**
     * Generates HTML for the Filter Toolbar
     */
    filterToolbar() {
        return `
            <div class="config-filter-group">
                <input type="text" id="config-modal-search" class="config-filter-input" placeholder="Search rule names..." autocomplete="off" />
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
    },

    /**
     * Generates HTML for the Summary Cards
     */
    summary(enabled, disabled, total) {
        return `
            <div class="config-summary-grid">
                <div class="summary-card enabled"><div class="summary-number">${enabled}</div><div class="summary-label">Enabled Rules</div></div>
                <div class="summary-card disabled"><div class="summary-number">${disabled}</div><div class="summary-label">Disabled Rules</div></div>
                <div class="summary-card total"><div class="summary-number">${total}</div><div class="summary-label">Total Rules</div></div>
            </div>
        `;
    },

    /**
     * Generates HTML for a schema-driven settings form
     * @param {Object} schema - The settings_schema from the rule (AVAILABLE_SETTINGS)
     * @param {Object} currentValues - The current custom_settings values
     * @returns {string} HTML for the settings form
     */
    generateSettingsForm(schema, currentValues) {
        if (!schema || Object.keys(schema).length === 0) {
            // Fallback: return empty form or raw JSON textarea
            return '<div class="settings-form"><p class="text-slate-400 text-sm">No settings available</p></div>';
        }

        let formHtml = '<div class="settings-form">';
        
        for (const [key, meta] of Object.entries(schema)) {
            const type = meta.type || 'string';
            const description = meta.description || '';
            const currentValue = currentValues[key];
            
            // Title case the key for display
            const label = key.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
            ).join(' ');
            
            formHtml += '<div class="setting-group">';
            formHtml += `<div class="setting-label">${label}</div>`;
            if (description) {
                formHtml += `<div class="setting-description">${description}</div>`;
            }
            
            // Render input based on type
            if (type === 'bool') {
                const checked = currentValue === true ? 'checked' : '';
                formHtml += `<input type="checkbox" class="setting-checkbox" data-key="${key}" ${checked} />`;
            } else if (type === 'int') {
                const value = currentValue !== undefined ? currentValue : (meta.default || '');
                formHtml += `<input type="number" class="setting-input" data-key="${key}" value="${value}" min="0" />`;
            } else if (type === 'list') {
                // Join array values with newlines for display
                const listValue = Array.isArray(currentValue) 
                    ? currentValue.join('\n') 
                    : (Array.isArray(meta.default) ? meta.default.join('\n') : '');
                formHtml += `<textarea class="setting-list-input" rows="4" data-key="${key}">${listValue}</textarea>`;
            } else if (type === 'dict' || type === 'object') {
                // Fallback: raw JSON textarea for complex types
                const jsonValue = currentValue !== undefined 
                    ? JSON.stringify(currentValue, null, 2) 
                    : (meta.default ? JSON.stringify(meta.default, null, 2) : '{}');
                formHtml += `<textarea class="rule-settings-json" data-key="${key}" rows="6">${jsonValue}</textarea>`;
                formHtml += `<div class="setting-description">Raw JSON (complex type)</div>`;
            } else {
                // Default: string or unknown type
                const value = currentValue !== undefined ? String(currentValue) : (meta.default || '');
                formHtml += `<input type="text" class="setting-input" data-key="${key}" value="${value}" />`;
            }
            
            formHtml += '</div>';
        }
        
        formHtml += '</div>';
        return formHtml;
    },

    /**
     * Generates HTML for a single Rule Row
     */
    ruleRow({ ruleName, ruleConfig, isBuiltIn, supportsConfig }) {
        const isEnabled = ruleConfig.enabled;
        // Use helper logic passed in or calculated here. 
        // For simplicity, we assume severity override logic is handled before passing data or simple check here
        const severity = ruleConfig.severity_override || 'ADVICE'; 
        
        const customSettings = ruleConfig.custom_settings || {};
        const settingsText = Object.keys(customSettings).length > 0 ? JSON.stringify(customSettings, null, 2) : '';
        const isGhost = ruleConfig._is_ghost === true;

        const enabledClass = isEnabled ? 'enabled' : 'disabled';
        const ghostClass = isGhost ? 'ghost-rule' : '';

        const hasCustomSettings = Object.keys(customSettings).length > 0;
        const configureIcon = '🛠️';
        const configureText = 'Customize';

        return `
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
                            ${supportsConfig ? `
                                <button class="rule-configure-btn ${hasCustomSettings ? 'modified' : ''}" data-rule="${ruleName}" type="button">
                                    ${configureIcon} ${configureText} <span class="configure-chevron" data-rule="${ruleName}">▼</span>
                                </button>
                            ` : ''}
                            <select class="rule-severity-select rule-severity-${severity.toLowerCase()}" data-rule="${ruleName}" data-severity="${severity}">
                                <option value="ADVICE" ${severity === 'ADVICE' ? 'selected' : ''}>ADVICE</option>
                                <option value="ACTION" ${severity === 'ACTION' ? 'selected' : ''}>ACTION</option>
                            </select>
                        ` : ''}
                        ${!isBuiltIn && isGhost ? `<button class="rule-delete-btn" data-rule="${ruleName}" type="button" title="Remove ghost rule">🗑️ Remove</button>` : ''}
                        ${!isBuiltIn ? `
                            <div class="rule-toggle-switch ${isGhost ? 'disabled' : (isEnabled ? 'enabled' : 'disabled')}" data-rule="${ruleName}" ${isGhost ? 'disabled' : ''}>
                                <div class="toggle-track"><span class="toggle-thumb"></span></div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                ${!isBuiltIn && !isGhost && supportsConfig ? `
                    <div class="rule-settings-panel" data-rule="${ruleName}">
                        ${this.generateSettingsForm(ruleConfig.settings_schema, customSettings)}
                        <div class="rule-settings-error" data-rule="${ruleName}" style="display: none;">Invalid JSON format</div>
                    </div>
                ` : ''}
            </div>
        `;
    }
};