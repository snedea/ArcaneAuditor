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
        this.pendingDuplicateId = null;

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
            // Default to first built-in
            const tpl = this.availableConfigs.find(c => c.category === 'built-in') || this.availableConfigs[0];
            this.openDuplicateModal(tpl.id);
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
            await ConfigAPI.duplicate(configId, newName, category);
            this.app.showToast("Configuration duplicated!", "success");
            await this.loadConfigurations();
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
    
    openDuplicateModal(configId, defaultCategory = 'Personal') {
        this.pendingDuplicateId = configId;
        const modal = document.getElementById("duplicate-config-modal");
        const nameInput = document.getElementById("duplicate-config-name");
        if(nameInput) nameInput.value = "";
        
        // Check radio
        const cat = (defaultCategory || 'Personal').toLowerCase();
        document.querySelectorAll("input[name='duplicate-category']").forEach(i => 
            i.checked = i.value.toLowerCase() === cat
        );
        
        if(modal) modal.classList.remove("hidden");
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
            if (!name) return this.app.showToast("Please enter a name.", "info");
            
            this.duplicateConfiguration(this.pendingDuplicateId, name, category);
            this.closeDuplicateModal();
        };
        
        const closeBtn = document.getElementById("duplicate-close-btn");
        if(closeBtn) closeBtn.onclick = () => this.closeDuplicateModal();
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

    saveCurrentConfigChanges(config) {
        // This was used by breakdown UI save button
        this.app.showToast('Save not implemented yet', 'info');
    }
}