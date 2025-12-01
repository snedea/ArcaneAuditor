// ui-main.js
export class ConfigMainUI {
    constructor(manager) {
        this.manager = manager;
        this.app = manager.app;
        
        // State for the popups
        this.activeCardMenuCleanup = null;
        this.activeCardMenuTrigger = null;
        this.toolbarListenersInitialized = false;
        this.toolbarClickHandler = null;
        this.toolbarManageHandler = null;
        this.toolbarClickOutsideHandler = null;
    }

    /**
     * Master render method to update everything
     */
    refreshAll() {
        this.renderCards();
        this.updateToolbar();
        this.buildDropdown();
        this.updateMetadataLine();
    }

    // --- CARD RENDERING ---
    
    renderCards() {
        const container = document.getElementById('config-card-container');
        const columns = {
            builtIn: document.getElementById('config-column-built-in'),
            team: document.getElementById('config-column-team'),
            personal: document.getElementById('config-column-personal')
        };

        if (!container || !columns.builtIn) return;

        this.closeActiveCardMenu();
        Object.values(columns).forEach(col => { if(col) col.innerHTML = ''; });

        if (!this.manager.availableConfigs.length) return;

        // Sort: Selected first, then others
        const sortedConfigs = [...this.manager.availableConfigs];
        if (this.manager.selectedConfig) {
            sortedConfigs.sort((a, b) => {
                if (a.id === this.manager.selectedConfig) return -1;
                if (b.id === this.manager.selectedConfig) return 1;
                return 0;
            });
        }

        sortedConfigs.forEach(config => {
            const card = this.createCardElement(config);
            
            const typeKey = (config.type || 'built-in').toLowerCase();
            const targetColumn =
                typeKey === 'team' ? columns.team :
                typeKey === 'personal' ? columns.personal :
                columns.builtIn;

            if (targetColumn) targetColumn.appendChild(card);
        });

        this.attachColumnButtons();
    }

    createCardElement(config) {
        const card = document.createElement('div');
        card.className = 'config-option config-card';
        card.dataset.configId = config.id;

        if (config.id === this.manager.selectedConfig) {
            card.classList.add('selected');
        }

        // Menu Button (⋮)
        const menuBtn = document.createElement('div');
        menuBtn.className = 'card-menu';
        menuBtn.textContent = '⋮';
        menuBtn.onclick = (e) => {
            e.stopPropagation();
            this.showCardMenu(config.id, menuBtn);
        };

        // Content
        const nameDiv = document.createElement('div');
        nameDiv.className = 'config-name';
        nameDiv.textContent = config.name;

        const metaDiv = document.createElement('div');
        metaDiv.className = 'config-meta';
        const counts = this.getRuleCounts(config);
        metaDiv.textContent = `${counts.enabled} enabled • ${counts.disabled} disabled`;

        card.append(menuBtn, nameDiv, metaDiv);

        // Click Selection
        card.onclick = (e) => {
            if (!e.target.closest('.card-menu')) {
                this.manager.selectConfiguration(config.id);
            }
        };

        return card;
    }

    attachColumnButtons() {
        document.querySelectorAll('.column-action-btn').forEach(btn => {
            btn.onclick = () => this.manager.openCreateFromTemplate(btn.dataset.category);
        });
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

    updateCardSelection() {
        document.querySelectorAll('.config-card').forEach(card => {
            card.classList.toggle('selected', card.dataset.configId === this.manager.selectedConfig);
        });
    }

    // --- CONTEXT MENUS ---

    showCardMenu(configId, trigger) {
        this.closeActiveCardMenu();
        const config = this.manager.availableConfigs.find(c => c.id === configId);
        if (!config) return;

        const isBuiltIn = ['built-in', 'builtin'].includes((config.type||'').toLowerCase());
        
        // Build Menu
        const menu = document.createElement('div');
        menu.className = 'config-card-menu-popover';
        menu.style.position = 'absolute';
        
        const addItem = (label, action, danger = false) => {
            const item = document.createElement('div');
            item.className = `menu-item ${danger ? 'danger' : ''}`;
            item.textContent = label;
            item.onclick = () => {
                this.closeActiveCardMenu();
                if(action === 'view') this.manager.showConfigBreakdown();
                if(action === 'edit') this.manager.editConfiguration(configId);
                if(action === 'copy') this.manager.openDuplicateModal(configId);
                if(action === 'delete') this.manager.requestDeleteConfiguration(config);
            };
            menu.appendChild(item);
        };

        addItem('View Details', 'view');
        if (!isBuiltIn) addItem('Edit', 'edit');
        addItem('Copy', 'copy');
        if (!isBuiltIn) addItem('Delete', 'delete', true);

        // Position & Show
        document.body.appendChild(menu);
        const rect = trigger.getBoundingClientRect();
        menu.style.top = `${rect.bottom + window.scrollY + 5}px`;
        menu.style.left = `${rect.right + window.scrollX - 150}px`; // Align right-ish

        // Cleanup Logic
        const close = () => {
            menu.remove();
            document.removeEventListener('click', close);
            this.activeCardMenuCleanup = null;
        };
        
        // Defer listener so immediate click doesn't close it
        setTimeout(() => document.addEventListener('click', close), 0);
        this.activeCardMenuCleanup = close;
    }

    closeActiveCardMenu() {
        if (this.activeCardMenuCleanup) this.activeCardMenuCleanup();
    }

    
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