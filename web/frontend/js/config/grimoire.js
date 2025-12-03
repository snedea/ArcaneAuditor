// grimoire.js
/**
 * GrimoireUI - Handles displaying rule documentation in a modal
 */
export class GrimoireUI {
    constructor() {
        this.currentView = 'index'; // 'index' or 'detail'
        this.currentConfig = null;
        this.openedFromConfigModal = false; // Track if opened from config modal
        this.indexScrollPosition = 0; // Store scroll position for index view
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
            
            // Restore scroll position if we have one, otherwise start at top
            bodyEl.scrollTop = this.indexScrollPosition;

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
     * Group rules by category based on explicit categorization strategy
     * @param {Array} rules - Array of [ruleName, ruleConfig] tuples
     * @returns {Object} Grouped rules by category
     */
    groupRulesByCategory(rules) {
        const grouped = {
            'Endpoint & Data Rules': [],
            'Widget & UI Rules': [],
            'Structure & Security': [],
            'Unused Code': [],
            'Script Best Practices': []
        };

        // Helper to place rule in a bucket
        const addTo = (cat, rName, rConfig) => {
            if (!grouped[cat]) grouped[cat] = [];
            grouped[cat].push([rName, rConfig]);
        };

        for (const [ruleName, ruleConfig] of rules) {
            // 1. Unused Code (Highest Priority)
            if (ruleName.includes('Unused') || ruleName.includes('Dead') || ruleName.includes('Empty')) {
                addTo('Unused Code', ruleName, ruleConfig);
                continue;
            }

            // 2. Endpoint & Data
            if (ruleName.includes('Endpoint') || 
                ruleName.includes('WorkdayAPI') || 
                ruleName.includes('MaximumEffort') ||
                ruleName.includes('SessionVariable')) {
                addTo('Endpoint & Data Rules', ruleName, ruleConfig);
                continue;
            }

            // 3. Widget & UI
            if (ruleName.includes('Widget') || 
                ruleName.includes('Grid') || 
                ruleName.includes('Footer')) {
                addTo('Widget & UI Rules', ruleName, ruleConfig);
                continue;
            }

            // 4. Structure & Security
            if (ruleName.includes('Hardcoded') || 
                ruleName.includes('Security') || 
                ruleName.includes('Ordering') ||
                ruleName.includes('FileName') ||
                ruleName.includes('Embedded') ||
                ruleName.includes('Boolean') || 
                ruleName.includes('Interpolator')) {
                addTo('Structure & Security', ruleName, ruleConfig);
                continue;
            }

            // 5. Script (Default for remaining Script* rules)
            if (ruleName.startsWith('Script')) {
                addTo('Script Best Practices', ruleName, ruleConfig);
                continue;
            }

            // Fallback
            addTo('Structure & Security', ruleName, ruleConfig);
        }

        // Filter out empty categories and return
        const finalGrouped = {};
        const displayOrder = [
            'Endpoint & Data Rules',
            'Script Best Practices',
            'Unused Code',
            'Widget & UI Rules',
            'Structure & Security'
        ];

        displayOrder.forEach(cat => {
            if (grouped[cat] && grouped[cat].length > 0) {
                finalGrouped[cat] = grouped[cat];
            }
        });

        return finalGrouped;
    }

    /**
     * Get a short description for a rule
     * @param {Object} ruleConfig - Rule configuration object
     * @returns {string} Description text
     */
    getRuleDescription(ruleConfig) {
        const doc = ruleConfig.documentation || {};
        if (doc.why) {
            // Clean up the text: replace newlines, strip markdown formatting for card display
            let text = doc.why.replace(/\n/g, ' ').trim();
            
            // Remove markdown bold/italic markers for cleaner card text
            text = text.replace(/\*\*/g, '').replace(/\*/g, '');
            
            // Find first sentence, but skip periods:
            // 1. Inside backticks (code)
            // 2. In domain names (like .com, .org) - followed by space or end of string
            // 3. In abbreviations (like "etc.") - followed by space and lowercase
            let firstSentence = null;
            let inBackticks = false;
            
            for (let i = 0; i < text.length; i++) {
                if (text[i] === '`') {
                    inBackticks = !inBackticks;
                } else if (!inBackticks && /[.!?]/.test(text[i])) {
                    // Check if this is a real sentence ending
                    const nextChar = i + 1 < text.length ? text[i + 1] : ' ';
                    const prevChar = i > 0 ? text[i - 1] : ' ';
                    const nextTwoChars = i + 2 < text.length ? text.substring(i + 1, i + 3) : ' ';
                    
                    // Skip if period is in a domain name (like .com, .org, .net)
                    // Pattern: one or more letters/numbers + period + common TLD + space/punctuation/end
                    const domainPattern = /[a-z0-9-]+\.(com|org|net|edu|gov|io|co|uk|de|fr|jp|au|ca|us|info|biz|name|mobi|asia|jobs|museum|travel|xxx|tel|pro|aero|coop|int|mil|arpa|app|dev|tech|online|site|website|store|shop|blog|news|tv|me|cc|ws)(\s|$|[.,;:!?])/i;
                    // Look back up to 30 characters to find domain pattern
                    const beforePeriod = text.substring(Math.max(0, i - 30), i + 1);
                    if (domainPattern.test(beforePeriod)) {
                        continue; // Skip this period, it's in a domain name
                    }
                    
                    // Skip if it's an abbreviation followed by lowercase (like "etc. and")
                    // But allow if followed by space and capital letter (sentence ending)
                    if (text[i] === '.' && nextChar !== ' ' && nextChar !== undefined) {
                        // Period not followed by space - likely abbreviation or domain
                        continue;
                    }
                    
                    // This looks like a real sentence ending
                    firstSentence = text.substring(0, i + 1);
                    break;
                }
            }
            
            if (firstSentence) {
                // Return the full first sentence - let CSS handle truncation with line-clamp
                return firstSentence;
            }
            
            // If no sentence ending found, truncate at word boundary near 150 chars
            if (text.length > 150) {
                const truncated = text.substring(0, 150);
                const lastSpace = truncated.lastIndexOf(' ');
                return lastSpace > 0 ? truncated.substring(0, lastSpace) + '...' : truncated + '...';
            }
            return text;
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

        // Save current scroll position before navigating to detail (if coming from index)
        let bodyEl = document.getElementById('grimoire-body');
        if (bodyEl && this.currentView === 'index') {
            this.indexScrollPosition = bodyEl.scrollTop;
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
        // Ensure we have bodyEl reference
        if (!bodyEl) {
            bodyEl = document.getElementById('grimoire-body');
        }

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
            
            // Reset scroll position to top when showing detail view
            bodyEl.scrollTop = 0;
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

        // Convert bold (**text**)
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

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

