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
                        <textarea class="rule-settings-json" data-rule="${ruleName}" placeholder='{ "mode": "strict" }'>${settingsText}</textarea>
                        <div class="rule-settings-error" data-rule="${ruleName}">Invalid JSON format</div>
                    </div>
                ` : ''}
            </div>
        `;
    }
};