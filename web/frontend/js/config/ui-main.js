// ui-main.js
export class ConfigMainUI {
    constructor(manager) {
        this.manager = manager;
        this.app = manager.app;
        
        // Toolbar state
        this.toolbarListenersInitialized = false;
    }

    /**
     * Master render method to update everything
     */
    refreshAll() {
        this.updateToolbar();
        this.buildDropdown();
        this.updateMetadataLine();
    }

    getRuleCounts(config) {
        const rules = config?.rules ? Object.values(config.rules) : [];
        const enabled = rules.filter(r => r.enabled && !r._is_ghost).length;
        const disabled = rules.filter(r => !r.enabled && !r._is_ghost).length;
        return { enabled, disabled };
    }

    // --- TOOLBAR & DROPDOWN ---

    updateToolbar() {
        const config = this.manager.availableConfigs.find(c => c.id === this.manager.selectedConfig);
        if (!config) return;

        const nameEl = document.getElementById('config-selected-name');
        const categoryEl = document.getElementById('config-selected-category');
        const rulesEl = document.getElementById('config-selected-rules');
        
        if (nameEl) nameEl.textContent = config.name;
        
        // Category Badge
        if (categoryEl) {
            const cat = (config.category || config.type || 'built-in').toLowerCase();
            categoryEl.textContent = cat === 'builtin' ? 'Built-in' : (cat.charAt(0).toUpperCase() + cat.slice(1));
            categoryEl.className = `config-selected-category-text config-category-${cat === 'builtin' ? 'built-in' : cat}`;
            categoryEl.style.display = 'inline';
        }
        
        // Rules Count
        if (rulesEl) {
            const counts = this.getRuleCounts(config);
            rulesEl.innerHTML = `<span class="config-rule-active">${counts.enabled} rules active</span>`;
            if (counts.disabled > 0) {
                rulesEl.innerHTML += `<span class="config-rule-separator">|</span><span class="config-rule-disabled">${counts.disabled} Off</span>`;
            }
        }
    }

    buildDropdown() {
        const container = document.getElementById('config-dropdown');
        if (!container || !this.manager.availableConfigs.length) return;

        container.innerHTML = '';
        const groups = {
            "BUILT-IN": c => ['built-in', 'builtin'].includes((c.category||c.type||'').toLowerCase()),
            "TEAM": c => (c.category||c.type||'').toLowerCase() === 'team',
            "PERSONAL": c => (c.category||c.type||'').toLowerCase() === 'personal'
        };

        Object.entries(groups).forEach(([label, filterFn]) => {
            const list = this.manager.availableConfigs.filter(filterFn);
            if (!list.length) return;

            const h = document.createElement('h4');
            h.textContent = label;
            container.appendChild(h);

            list.forEach(cfg => {
                const div = document.createElement('div');
                const isSelected = cfg.id === this.manager.selectedConfig;
                div.className = `config-dropdown-item ${isSelected ? 'config-dropdown-item-selected' : ''}`;
                
                const counts = this.getRuleCounts(cfg);
                
                div.innerHTML = `
                    <span class="config-dropdown-name">${cfg.name}</span>
                    <div class="config-dropdown-stats">
                        <span class="config-rules-count"><span class="config-rule-active">${counts.enabled} Active</span></span>
                        ${isSelected ? '<span class="config-checkmark">✓</span>' : ''}
                    </div>
                `;
                div.onclick = (e) => {
                    e.stopPropagation();
                    this.manager.selectConfiguration(cfg.id);
                    container.classList.remove('visible');
                };
                container.appendChild(div);
            });
        });

        const createBtn = document.createElement('div');
        createBtn.className = 'config-dropdown-create';
        createBtn.textContent = '+ Create New Configuration';
        createBtn.onclick = (e) => {
            e.stopPropagation();
            this.manager.showCreateConfigModal();
        };
        container.appendChild(createBtn);
    }

    initializeToolbarListeners() {
        if (this.toolbarListenersInitialized) return;

        const toggleBtn = document.getElementById('config-selected-button');
        const manageBtn = document.getElementById('config-manage-btn');
        const dropdown = document.getElementById('config-dropdown');

        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (dropdown) {
                    this.buildDropdown(); // Refresh content
                    dropdown.classList.toggle('visible');
                }
            });
        }

        if (manageBtn) {
            manageBtn.addEventListener('click', () => this.manager.showConfigBreakdown());
        }

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (dropdown && dropdown.classList.contains('visible') && 
                !dropdown.contains(e.target) && !toggleBtn.contains(e.target)) {
                dropdown.classList.remove('visible');
            }
        });

        this.toolbarListenersInitialized = true;
    }

    // --- HELPERS ---

    updateMetadataLine() {
        const metaDiv = document.getElementById('config-meta-line');
        if (!metaDiv) return;
        const config = this.manager.availableConfigs.find(c => c.id === this.manager.selectedConfig);
        if (config) {
            const counts = this.getRuleCounts(config);
            const perf = config.performance ? ` • ${config.performance}` : '';
            metaDiv.textContent = `${counts.enabled} enabled • ${counts.disabled} disabled${perf}`;
        } else {
            metaDiv.textContent = '';
        }
    }

    // --- CONTEXT MENUS ---

    showDeleteConfigurationModal(config, onConfirm) {
        const modal = document.getElementById('config-delete-modal');
        const message = document.getElementById('config-delete-message');
        const confirmBtn = document.getElementById('config-delete-confirm');
        const cancelBtn = document.getElementById('config-delete-cancel');
        const closeBtn = document.getElementById('config-delete-close');
        
        if (!modal || !message || !confirmBtn) {
            console.error('Delete modal elements not found');
            return;
        }

        // Update text
        message.textContent = `Are you sure you want to delete "${config.name}"?`;

        // Cleanup previous listeners to prevent memory leaks/double-clicks
        const cleanup = () => {
            confirmBtn.onclick = null; // Clear old handlers
            cancelBtn.onclick = null;
            closeBtn.onclick = null;
            modal.hidden = true;
        };

        // Bind Confirm
        confirmBtn.onclick = () => {
            cleanup();
            onConfirm(); // Execute the callback passed from Manager
        };

        // Bind Cancel/Close
        cancelBtn.onclick = cleanup;
        closeBtn.onclick = cleanup;

        // Show it
        modal.hidden = false;
    }
}