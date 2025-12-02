import { getLastSelectedConfig, saveSelectedConfig } from '../utils.js';
import { ConfigAPI } from './api.js';
import { ConfigBreakdownUI } from './ui-breakdown.js';
import { ConfigMainUI } from './ui-main.js'; 

export class ConfigManager {
    constructor(app) {
        this.app = app;
        this.availableConfigs = [];
        this.selectedConfig = null;
        this.productionTemplateId = null;

        // Initialize UI components
        this.mainUI = new ConfigMainUI(this);
        this.breakdownUI = new ConfigBreakdownUI(this);

        this.bindGlobalConfigControls();
    }

    /**
     * Entry point called by App
     */
    async loadConfigurations() {
        try {
            const data = await ConfigAPI.getAll();
            this.availableConfigs = data.configs;
            
            this.restoreSelection(); // Helper extracted below
            this.findProductionTemplate(); // Helper extracted below
            
            // Render UI
            this.mainUI.refreshAll();
            this.mainUI.initializeToolbarListeners();

        } catch (error) {
            console.error('Failed to load configurations:', error);
            this.app.showError('Failed to load configurations.');
        }
    }

    selectConfiguration(configId) {
        if (!this.availableConfigs.some(c => c.id === configId)) return;
        
        this.selectedConfig = configId;
        saveSelectedConfig(configId);
        
        // Update UI partials
        //this.mainUI.updateCardSelection();
        this.mainUI.updateToolbar();
        this.mainUI.updateMetadataLine();
    }
    
    // --- ACTIONS ---

    showConfigBreakdown() {
        if (!this.selectedConfig) return;
        this.breakdownUI.show(this.selectedConfig);
    }
    
    showCreateConfigModal() {
        if (this.availableConfigs.length > 0) {
            // Default to Production-Ready template
            if (this.productionTemplateId) {
                this.openDuplicateModal(this.productionTemplateId);
            } else {
                // Fallback to first built-in if Production-Ready not found
                const tpl = this.availableConfigs.find(c => {
                    const cat = (c.category || c.type || '').toLowerCase();
                    return ['built-in', 'builtin'].includes(cat);
                }) || this.availableConfigs[0];
                this.openDuplicateModal(tpl.id);
            }
        }
    }

    openCreateFromTemplate(categoryLabel) {
        if (!this.productionTemplateId) {
            this.app.showToast('Production template not available.', 'error');
            return;
        }
        this.openDuplicateModal(this.productionTemplateId, categoryLabel);
    }

    async duplicateConfiguration(configId, newName, category) {
        try {
            const response = await ConfigAPI.duplicate(configId, newName, category);
            this.app.showToast("Configuration duplicated!", "success");
            
            // Reload configurations to get the new one
            await this.loadConfigurations();
            
            // Find and select the newly created config
            // The response should contain the new config ID
            const newConfigId = response?.id || response?.config?.id;
            if (newConfigId) {
                // Select the new configuration
                this.selectConfiguration(newConfigId);
                
                // Open the config editor immediately
                this.showConfigBreakdown();
            } else {
                // Fallback: try to find by name if ID not in response
                const newConfig = this.availableConfigs.find(c => 
                    c.name === newName && 
                    ((c.category || c.type || '').toLowerCase() === category.toLowerCase())
                );
                if (newConfig) {
                    this.selectConfiguration(newConfig.id);
                    this.showConfigBreakdown();
                }
            }
        } catch (err) {
            this.app.showToast(err.message, "error");
        }
    }


    async requestDeleteConfiguration(config) {
        // You can leave this small modal logic here or move to UI. 
        // For 20 lines, it's fine here for now.
        const modal = document.getElementById('config-delete-modal');
        const message = document.getElementById('config-delete-message');
        const confirmBtn = document.getElementById('config-delete-confirm');
        
        // Setup simple confirm for now:
        this.mainUI.showDeleteConfigurationModal(config, async () => {
            try {
                await ConfigAPI.delete(config.id);
                this.app.showToast('🗑️ Configuration deleted', 'success');
                await this.loadConfigurations();
            } catch (err) {
                this.app.showToast(err.message, 'error');
            }
        });
    }

    // --- MODALS (Duplicate) ---
    // These are simple enough to stay or move to a tiny `config-modals.js` 
    // but for now, keep them to avoid over-engineering.
    
    openDuplicateModal(defaultSourceId = null, defaultCategory = 'Personal') {
        const modal = document.getElementById("duplicate-config-modal");
        const sourceSelect = document.getElementById("duplicate-source-select");
        const nameInput = document.getElementById("duplicate-config-name");
        
        // 1. Populate Source Dropdown
        if (sourceSelect) {
            sourceSelect.innerHTML = '';
            
            // Helper to add groups
            const addGroup = (label, configs) => {
                if (configs.length === 0) return;
                const group = document.createElement('optgroup');
                group.label = label;
                configs.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.textContent = c.name;
                    group.appendChild(opt);
                });
                sourceSelect.appendChild(group);
            };
            
            // Group configs for clarity (check both category and type)
            const builtIn = this.availableConfigs.filter(c => {
                const cat = (c.category || c.type || '').toLowerCase();
                return ['built-in', 'builtin'].includes(cat);
            });
            const team = this.availableConfigs.filter(c => {
                const cat = (c.category || c.type || '').toLowerCase();
                return cat === 'team';
            });
            const personal = this.availableConfigs.filter(c => {
                const cat = (c.category || c.type || '').toLowerCase();
                return cat === 'personal';
            });
            
            addGroup('Built-In Templates', builtIn);
            addGroup('Team Configurations', team);
            addGroup('Personal Configurations', personal);
            
            // 2. Set Default Selection
            let selectedSourceId = null;
            if (defaultSourceId && this.availableConfigs.some(c => c.id === defaultSourceId)) {
                selectedSourceId = defaultSourceId;
                sourceSelect.value = defaultSourceId;
            } else if (this.productionTemplateId) {
                selectedSourceId = this.productionTemplateId; // Fallback
                sourceSelect.value = this.productionTemplateId;
            }
            
            // Update title, icon, and button based on selected source
            const updateModalTitle = () => {
                const selectedId = sourceSelect.value;
                const selectedConfig = this.availableConfigs.find(c => c.id === selectedId);
                const sourceName = selectedConfig?.name || '';
                const titleEl = document.getElementById('duplicate-modal-title');
                const iconEl = document.getElementById('duplicate-modal-icon');
                const confirmBtn = document.getElementById('duplicate-confirm-btn');
                
                if (sourceName.toLowerCase() === 'production-ready') {
                    if (titleEl) titleEl.textContent = "New Configuration";
                    if (iconEl) iconEl.textContent = "🪄";
                    if (confirmBtn) confirmBtn.textContent = "Create Configuration";
                } else {
                    if (titleEl) titleEl.textContent = "Duplicate Configuration";
                    if (iconEl) iconEl.textContent = "📋";
                    if (confirmBtn) confirmBtn.textContent = "Clone Configuration";
                }
            };
            
            // Set initial title/icon based on default selection
            updateModalTitle();
            
            // Update title/icon when dropdown changes
            // Only add listener if not already added (check data attribute)
            if (!sourceSelect.dataset.titleUpdaterBound) {
                sourceSelect.addEventListener('change', updateModalTitle);
                sourceSelect.dataset.titleUpdaterBound = 'true';
            }
        }
        
        // 3. Reset Name Input
        if (nameInput) {
            nameInput.value = "";
            nameInput.classList.remove('input-error');
        }
        
        // 4. Set Category Radio
        const cat = (defaultCategory || 'Personal').toLowerCase();
        document.querySelectorAll("input[name='duplicate-category']").forEach(i => 
            i.checked = i.value.toLowerCase() === cat
        );
        
        // 5. Show Modal
        if (modal) {
            modal.classList.remove("hidden");
            setTimeout(() => nameInput?.focus(), 50);
        }
    }

    closeDuplicateModal() {
        document.getElementById("duplicate-config-modal")?.classList.add("hidden");
    }

    bindGlobalConfigControls() {
        // Simple bindings for the Duplicate Modal buttons
        const confirmBtn = document.getElementById("duplicate-confirm-btn");
        if(confirmBtn) confirmBtn.onclick = () => {
            const name = document.getElementById("duplicate-config-name").value.trim();
            const category = document.querySelector("input[name='duplicate-category']:checked")?.value || 'Personal';
            
            // Get source from dropdown
            const sourceId = document.getElementById("duplicate-source-select").value;
            
            if (!name) {
                this.app.showToast("Please enter a name.", "info");
                return;
            }
            
            // Pass sourceId directly
            this.duplicateConfiguration(sourceId, name, category);
            this.closeDuplicateModal();
        };
        
        const closeBtn = document.getElementById("duplicate-close-btn");
        if(closeBtn) closeBtn.onclick = () => this.closeDuplicateModal();

        // Global Grimoire button
        const grimoireBtn = document.getElementById("global-grimoire-btn");
        if (grimoireBtn) {
            grimoireBtn.onclick = () => {
                this.openGrimoireIndex();
            };
        }
    }

    /**
     * Open the Grimoire Index view
     */
    async openGrimoireIndex() {
        try {
            // Get the current selected config or use the first available
            let configId = this.selectedConfig;
            if (!configId && this.availableConfigs.length > 0) {
                configId = this.availableConfigs[0].id;
            }

            if (!configId) {
                this.app.showToast('No configuration available', 'error');
                return;
            }

            // Fetch the full config data (with rules and documentation)
            const data = await ConfigAPI.getAll();
            const config = data.configs.find(c => c.id === configId);
            
            if (!config) {
                this.app.showToast('Configuration not found', 'error');
                return;
            }

            // Open the index view (not from config modal)
            this.breakdownUI.grimoire.showIndex(config, false);
        } catch (error) {
            console.error('Failed to open Grimoire:', error);
            this.app.showToast('Failed to open Rules Grimoire', 'error');
        }
    }

    // --- HELPERS ---
    
    restoreSelection() {
        if (!this.selectedConfig) {
            try { this.selectedConfig = getLastSelectedConfig(); } catch (e) {}
        }
        if (this.selectedConfig && !this.availableConfigs.some(c => c.id === this.selectedConfig)) {
            this.selectedConfig = null;
        }
        if (!this.selectedConfig && this.availableConfigs.length > 0) {
            this.selectedConfig = this.availableConfigs[0].id;
        }
    }

    findProductionTemplate() {
        const prod = this.availableConfigs.find(c => (c.name||'').toLowerCase() === 'production-ready');
        this.productionTemplateId = prod ? prod.id : (this.availableConfigs[0]?.id || null);
    }

    async saveCurrentConfigChanges(config) {
        try {
            // Create a payload with ONLY the rules data
            // We need 'id' for the API route
            const payload = {
                id: config.id,
                rules: config.rules
            };

            // This will send: { config: { id: "...", rules: { ... } } }
            await ConfigAPI.save(payload); 
            
            this.app.showToast('Rules saved successfully!', 'success');
            
            // Reload to ensure the UI reflects the server state
            await this.loadConfigurations();
            this.showConfigBreakdown(config.id);
            
        } catch (error) {
            console.error('Save failed:', error);
            this.app.showToast(`Failed to save: ${error.message}`, 'error');
        }
    }
}