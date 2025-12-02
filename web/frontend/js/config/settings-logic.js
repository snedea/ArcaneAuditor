// settings-logic.js
/**
 * SettingsHandler - Handles schema-driven settings form logic
 */
export class SettingsHandler {
    constructor() {
        // Store reference to currentConfig (will be set by caller)
        this.currentConfig = null;
    }
    
    /**
     * Set the current config reference (called by ConfigBreakdownUI)
     * @param {Object} config - The configuration object
     */
    setCurrentConfig(config) {
        this.currentConfig = config;
    }
    /**
     * Bind event listeners for schema-driven settings form inputs
     * @param {HTMLElement} container - The container element containing the form inputs
     * @param {Object} config - The configuration object (optional, will use currentConfig if not provided)
     */
    bindSettingsFormEvents(container, config) {
        const activeConfig = config || this.currentConfig;
        if (!activeConfig) return;
        
        // Text inputs
        container.querySelectorAll('.setting-input:not([data-events-bound])').forEach(input => {
            input.dataset.eventsBound = 'true';
            
            input.addEventListener('input', (e) => {
                this.handleSettingChange(e.target, activeConfig);
            });
        });
        
        // Checkboxes
        container.querySelectorAll('.setting-checkbox:not([data-events-bound])').forEach(checkbox => {
            checkbox.dataset.eventsBound = 'true';
            
            checkbox.addEventListener('change', (e) => {
                this.handleSettingChange(e.target, activeConfig);
            });
        });
        
        // List textareas (newline-separated)
        container.querySelectorAll('.setting-list-input:not([data-events-bound])').forEach(textarea => {
            textarea.dataset.eventsBound = 'true';
            
            textarea.addEventListener('input', (e) => {
                this.handleSettingChange(e.target, activeConfig);
            });
        });
        
        // JSON textarea fallback (for dict/object types) - still needs JSON validation
        container.querySelectorAll('.rule-settings-json:not([data-events-bound])').forEach(textarea => {
            // Mark as bound to prevent duplicate bindings
            textarea.dataset.eventsBound = 'true';
            
            textarea.addEventListener('blur', () => this.handleJsonBlur(textarea, activeConfig));
        });
    }
    
    /**
     * Handle changes to settings form inputs
     * @param {HTMLElement} input - The input element that changed
     * @param {Object} config - The configuration object
     */
    handleSettingChange(input, config) {
        const activeConfig = config || this.currentConfig;
        if (!activeConfig) return;
        
        // Find the rule item parent
        const ruleItem = input.closest('.rule-item');
        if (!ruleItem) return;
        
        const ruleName = ruleItem.dataset.rule;
        const settingKey = input.dataset.key;
        
        if (!ruleName || !settingKey) return;
        
        // Ensure custom_settings exists
        if (!activeConfig.rules[ruleName].custom_settings) {
            activeConfig.rules[ruleName].custom_settings = {};
        }
        
        // Parse value based on input type
        let value;
        if (input.classList.contains('setting-checkbox')) {
            value = input.checked;
        } else if (input.classList.contains('setting-list-input')) {
            // Split by newline, trim, remove empty
            value = input.value
                .split('\n')
                .map(s => s.trim())
                .filter(s => s !== '');
        } else if (input.type === 'number') {
            const numValue = parseInt(input.value, 10);
            if (isNaN(numValue)) {
                value = input.value === '' ? undefined : input.value;
            } else {
                // Enforce minimum value of 0 for number inputs
                value = Math.max(0, numValue);
                // Update the input field to reflect the corrected value
                if (numValue < 0) {
                    input.value = 0;
                }
            }
        } else {
            value = input.value;
        }
        
        // Update the config
        if (value === undefined || value === '') {
            // Remove the key if empty
            delete activeConfig.rules[ruleName].custom_settings[settingKey];
        } else {
            activeConfig.rules[ruleName].custom_settings[settingKey] = value;
        }
        
        // Update UI: toggle modified state on configure button
        this.updateConfigureButtonState(ruleName, activeConfig);
    }
    
    /**
     * Update the configure button's modified state based on custom_settings
     * Only toggles the 'modified' class for styling - doesn't change button text
     * @param {string} ruleName - The name of the rule
     * @param {Object} config - The configuration object
     */
    updateConfigureButtonState(ruleName, config) {
        const activeConfig = config || this.currentConfig;
        if (!activeConfig || !activeConfig.rules[ruleName]) return;
        
        const customSettings = activeConfig.rules[ruleName].custom_settings || {};
        const hasCustomSettings = Object.keys(customSettings).length > 0;
        
        const configureBtn = document.querySelector(`.rule-configure-btn[data-rule="${ruleName}"]`);
        if (!configureBtn) return;
        
        // Only toggle the modified class for styling - keep button text unchanged
        if (hasCustomSettings) {
            configureBtn.classList.add('modified');
        } else {
            configureBtn.classList.remove('modified');
        }
    }
    
    /**
     * Handle JSON textarea blur event (fallback for dict/object types)
     * @param {HTMLElement} textarea - The textarea element
     * @param {Object} config - The configuration object
     */
    handleJsonBlur(textarea, config) {
        // Use currentConfig to ensure we always edit fresh data
        const activeConfig = config || this.currentConfig;
        if (!activeConfig) return;
        
        // Find rule name from parent rule-item
        const ruleItem = textarea.closest('.rule-item');
        if (!ruleItem) return;
        
        const ruleName = ruleItem.dataset.rule;
        const settingKey = textarea.dataset.key; // For dict/object types, we have a data-key
        
        const errorDiv = document.querySelector(`.rule-settings-error[data-rule="${ruleName}"]`);
        const value = textarea.value.trim();
        const configureBtn = document.querySelector(`.rule-configure-btn[data-rule="${ruleName}"]`);
        const chevronHtml = `<span class="configure-chevron" data-rule="${ruleName}">▼</span>`;

        // Clear error
        textarea.classList.remove('json-invalid', 'json-valid');
        if (errorDiv) errorDiv.style.display = 'none';

        // Ensure custom_settings exists
        if (!activeConfig.rules[ruleName].custom_settings) {
            activeConfig.rules[ruleName].custom_settings = {};
        }

        if (!value || value === '{}') {
            // Remove the key if empty
            if (settingKey) {
                delete activeConfig.rules[ruleName].custom_settings[settingKey];
            } else {
                activeConfig.rules[ruleName].custom_settings = {};
            }
            this.updateConfigureButtonState(ruleName, activeConfig);
            return;
        }

        try {
            const parsed = JSON.parse(value);
            const isEmpty = Object.keys(parsed).length === 0;
            
            // Use activeConfig instead of config
            textarea.value = isEmpty ? '{}' : JSON.stringify(parsed, null, 2);
            
            // Update the specific key or entire custom_settings
            if (settingKey) {
                if (isEmpty) {
                    delete activeConfig.rules[ruleName].custom_settings[settingKey];
                } else {
                    activeConfig.rules[ruleName].custom_settings[settingKey] = parsed;
                }
            } else {
                activeConfig.rules[ruleName].custom_settings = isEmpty ? {} : parsed;
            }

            textarea.classList.add('json-valid');
            setTimeout(() => textarea.classList.remove('json-valid'), 1000);

            this.updateConfigureButtonState(ruleName, activeConfig);
        } catch (err) {
            textarea.classList.add('json-invalid');
            if (errorDiv) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = `Invalid JSON: ${err.message}`;
            }
        }
    }
}

