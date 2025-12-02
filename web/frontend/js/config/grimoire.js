// grimoire.js
/**
 * GrimoireUI - Handles displaying rule documentation in a modal
 */
export class GrimoireUI {
    constructor() {
        this.currentView = 'index'; // 'index' or 'detail'
        this.currentConfig = null;
        this.openedFromConfigModal = false; // Track if opened from config modal
    }

    /**
     * Show the Index View with all rules
     * @param {Object} config - The configuration object containing all rules
     * @param {boolean} fromConfigModal - Whether this was opened from the config modal
     */
    showIndex(config, fromConfigModal = false) {
        this.currentConfig = config;
        this.currentView = 'index';
        this.openedFromConfigModal = fromConfigModal;

        const rules = config.rules || {};
        const allRules = Object.entries(rules)
            .filter(([_, ruleConfig]) => ruleConfig.documentation && Object.keys(ruleConfig.documentation).length > 0)
            .sort(([a], [b]) => a.localeCompare(b));

        // Get or create the modal
        let modal = document.getElementById('grimoire-modal');
        if (!modal) {
            modal = this.renderGrimoireModal();
        }

        const titleEl = document.getElementById('grimoire-title');
        const bodyEl = document.getElementById('grimoire-body');

        if (titleEl) {
            titleEl.innerHTML = `<span id="grimoire-back-btn" style="display: none;">← </span>📜 Rules Grimoire`;
        }

        if (bodyEl) {
            let html = `
                <div class="grimoire-index-container">
                    <div class="grimoire-search-container">
                        <input 
                            type="text" 
                            id="grimoire-search-input" 
                            class="grimoire-search-input" 
                            placeholder="Search rule names..."
                            autocomplete="off"
                        />
                    </div>
                    <div class="grimoire-rules-grid" id="grimoire-rules-grid">
                        ${this.renderRuleCards(allRules)}
                    </div>
                </div>
            `;
            bodyEl.innerHTML = html;

            // Bind search
            const searchInput = document.getElementById('grimoire-search-input');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.filterRules(e.target.value, allRules);
                });
            }

            // Bind rule card clicks
            bodyEl.querySelectorAll('.grimoire-rule-card').forEach(card => {
                card.addEventListener('click', () => {
                    const ruleName = card.dataset.rule;
                    this.showGrimoire(ruleName, config);
                });
            });
        }

        // Show the modal
        modal.style.display = 'flex';

        // Bind close button
        const closeBtn = document.getElementById('grimoire-close-btn');
        if (closeBtn) {
            closeBtn.onclick = () => this.hideGrimoire();
        }

        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                e.stopPropagation();
                this.hideGrimoire();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Close on overlay click
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.hideGrimoire();
            }
        };
    }

    /**
     * Render rule cards for the index view
     * @param {Array} rules - Array of [ruleName, ruleConfig] tuples
     * @returns {string} HTML string
     */
    renderRuleCards(rules) {
        if (rules.length === 0) {
            return '<p class="grimoire-empty-state">No rules with documentation found.</p>';
        }

        // Group rules by category (prefix-based grouping)
        const grouped = this.groupRulesByCategory(rules);

        let html = '';
        for (const [category, categoryRules] of Object.entries(grouped)) {
            html += `<div class="grimoire-category-group">
                <h3 class="grimoire-category-title">${category}</h3>
                <div class="grimoire-category-rules">
                    ${categoryRules.map(([ruleName, ruleConfig]) => {
                        const description = this.getRuleDescription(ruleConfig);
                        return `
                            <div class="grimoire-rule-card" data-rule="${ruleName}">
                                <div class="grimoire-rule-card-name">${ruleName}</div>
                                <div class="grimoire-rule-card-description">${description}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>`;
        }

        return html;
    }

    /**
     * Group rules by category based on name prefix
     * @param {Array} rules - Array of [ruleName, ruleConfig] tuples
     * @returns {Object} Grouped rules by category
     */
    groupRulesByCategory(rules) {
        const grouped = {};

        for (const [ruleName, ruleConfig] of rules) {
            let category = 'Other';
            
            if (ruleName.startsWith('Script')) {
                category = 'Script Rules';
            } else if (ruleName.includes('Endpoint') || ruleName.startsWith('Endpoint')) {
                category = 'Endpoint Rules';
            } else if (ruleName.includes('Validation') || ruleName.startsWith('Validation')) {
                category = 'Validation Rules';
            } else if (ruleName.includes('Widget') || ruleName.startsWith('Widget')) {
                category = 'Widget Rules';
            } else if (ruleName.includes('Complexity') || ruleName.includes('Complex')) {
                category = 'Complexity Rules';
            } else if (ruleName.includes('Unused') || ruleName.includes('Dead')) {
                category = 'Unused Code Rules';
            } else if (ruleName.includes('Core') || ruleName.includes('Var') || ruleName.includes('Function')) {
                category = 'Core Rules';
            }

            if (!grouped[category]) {
                grouped[category] = [];
            }
            grouped[category].push([ruleName, ruleConfig]);
        }

        // Sort categories
        const categoryOrder = [
            'Core Rules',
            'Script Rules',
            'Complexity Rules',
            'Unused Code Rules',
            'Endpoint Rules',
            'Validation Rules',
            'Widget Rules',
            'Other'
        ];

        const sorted = {};
        for (const cat of categoryOrder) {
            if (grouped[cat]) {
                sorted[cat] = grouped[cat];
            }
        }
        for (const cat of Object.keys(grouped)) {
            if (!categoryOrder.includes(cat)) {
                sorted[cat] = grouped[cat];
            }
        }

        return sorted;
    }

    /**
     * Get a short description for a rule
     * @param {Object} ruleConfig - Rule configuration object
     * @returns {string} Description text
     */
    getRuleDescription(ruleConfig) {
        const doc = ruleConfig.documentation || {};
        if (doc.why) {
            // Take first sentence or first 100 chars
            const text = doc.why.replace(/\n/g, ' ').trim();
            const firstSentence = text.match(/^[^.!?]+[.!?]/);
            if (firstSentence) {
                return firstSentence[0].substring(0, 120);
            }
            return text.substring(0, 120) + (text.length > 120 ? '...' : '');
        }
        return 'No description available.';
    }

    /**
     * Filter rules based on search term
     * @param {string} searchTerm - Search term
     * @param {Array} allRules - All rules to filter
     */
    filterRules(searchTerm, allRules) {
        const grid = document.getElementById('grimoire-rules-grid');
        if (!grid) return;

        const searchLower = searchTerm.toLowerCase().trim();
        const cards = grid.querySelectorAll('.grimoire-rule-card');

        cards.forEach(card => {
            const ruleName = card.dataset.rule.toLowerCase();
            const description = card.querySelector('.grimoire-rule-card-description')?.textContent.toLowerCase() || '';
            
            if (searchLower === '' || ruleName.includes(searchLower) || description.includes(searchLower)) {
                card.style.display = '';
                // Show parent category if any card matches
                const categoryGroup = card.closest('.grimoire-category-group');
                if (categoryGroup) {
                    categoryGroup.style.display = '';
                }
            } else {
                card.style.display = 'none';
                // Hide category if all cards are hidden
                const categoryGroup = card.closest('.grimoire-category-group');
                if (categoryGroup) {
                    const visibleCards = categoryGroup.querySelectorAll('.grimoire-rule-card:not([style*="display: none"])');
                    if (visibleCards.length === 0) {
                        categoryGroup.style.display = 'none';
                    }
                }
            }
        });
    }

    /**
     * Show the Grimoire modal with documentation for a specific rule
     * @param {string} ruleName - The name of the rule
     * @param {Object} config - The configuration object containing rule data
     */
    showGrimoire(ruleName, config) {
        if (!config || !config.rules || !config.rules[ruleName]) {
            console.warn(`No config found for rule: ${ruleName}`);
            return;
        }

        this.currentConfig = config;
        this.currentView = 'detail';

        const ruleConfig = config.rules[ruleName];
        const documentation = ruleConfig.documentation || {};

        // Get or create the modal
        let modal = document.getElementById('grimoire-modal');
        if (!modal) {
            modal = this.renderGrimoireModal();
        }

        // Populate the modal
        const titleEl = document.getElementById('grimoire-title');
        const bodyEl = document.getElementById('grimoire-body');

        if (titleEl) {
            // Update title with back button if needed
            if (this.openedFromConfigModal) {
                titleEl.textContent = `📜 ${ruleName}`;
            } else {
                // Clear existing content and rebuild
                titleEl.innerHTML = '';
                const backBtn = document.createElement('span');
                backBtn.id = 'grimoire-back-btn';
                backBtn.style.cursor = 'pointer';
                backBtn.textContent = '← ';
                backBtn.onclick = (e) => {
                    e.stopPropagation();
                    this.showIndex(config, this.openedFromConfigModal);
                };
                titleEl.appendChild(backBtn);
                titleEl.appendChild(document.createTextNode(`📜 ${ruleName}`));
            }
        }

        if (bodyEl) {
            let html = '';

            // Why This Matters
            if (documentation.why) {
                html += `
                    <div class="grimoire-section">
                        <h3 class="grimoire-section-title">✨ Why This Matters</h3>
                        <div class="grimoire-section-content">${this.formatMarkdown(documentation.why)}</div>
                    </div>
                `;
            }

            // What It Catches
            if (documentation.catches && Array.isArray(documentation.catches) && documentation.catches.length > 0) {
                html += `
                    <div class="grimoire-section">
                        <h3 class="grimoire-section-title">🎯 What It Catches</h3>
                        <ul class="grimoire-list">
                            ${documentation.catches.map(item => `<li>${this.formatMarkdown(item)}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            // Examples
            if (documentation.examples) {
                html += `
                    <div class="grimoire-section">
                        <h3 class="grimoire-section-title">📝 Examples</h3>
                        <div class="grimoire-section-content">${this.formatMarkdown(documentation.examples)}</div>
                    </div>
                `;
            }

            // Recommendation
            if (documentation.recommendation) {
                html += `
                    <div class="grimoire-section">
                        <h3 class="grimoire-section-title">💡 Recommendation</h3>
                        <div class="grimoire-section-content">${this.formatMarkdown(documentation.recommendation)}</div>
                    </div>
                `;
            }

            // If no documentation, show a message
            if (!html) {
                html = '<div class="grimoire-section"><p class="text-slate-400">No documentation available for this rule.</p></div>';
            }

            bodyEl.innerHTML = html;
        }

        // Show the modal
        modal.style.display = 'flex';

        // Bind close button
        const closeBtn = document.getElementById('grimoire-close-btn');
        if (closeBtn) {
            closeBtn.onclick = () => this.hideGrimoire();
        }

        // Close on Escape key (stop propagation so config modal doesn't also close)
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                e.stopPropagation(); // Prevent event from bubbling to config modal
                this.hideGrimoire();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Close on overlay click
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.hideGrimoire();
            }
        };
    }

    /**
     * Hide the Grimoire modal
     */
    hideGrimoire() {
        const modal = document.getElementById('grimoire-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    /**
     * Create the Grimoire modal DOM structure (if it doesn't exist)
     */
    renderGrimoireModal() {
        // Check if it already exists
        let modal = document.getElementById('grimoire-modal');
        if (modal) {
            return modal;
        }

        // Create the modal structure
        modal = document.createElement('div');
        modal.id = 'grimoire-modal';
        modal.className = 'grimoire-overlay';
        modal.style.display = 'none';

        modal.innerHTML = `
            <div class="grimoire-content">
                <div class="grimoire-header">
                    <h2 id="grimoire-title">📜 Rule Grimoire</h2>
                    <button class="grimoire-close" id="grimoire-close-btn">✖️</button>
                </div>
                <div class="grimoire-body" id="grimoire-body">
                    <!-- Content will be populated dynamically -->
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        return modal;
    }

    /**
     * Simple markdown-like formatting helper
     * Converts code blocks and inline code to HTML
     * @param {string} text - The markdown text to format
     * @returns {string} Formatted HTML
     */
    formatMarkdown(text) {
        if (!text) return '';
        
        // Escape HTML first
        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Convert code blocks (```language ... ```)
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre class="grimoire-code-block"><code>${code.trim()}</code></pre>`;
        });

        // Convert inline code (`code`)
        html = html.replace(/`([^`]+)`/g, '<code class="grimoire-inline-code">$1</code>');

        // Convert line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');
        
        // Wrap in paragraph if not already wrapped
        if (!html.startsWith('<')) {
            html = `<p>${html}</p>`;
        }

        return html;
    }
}

