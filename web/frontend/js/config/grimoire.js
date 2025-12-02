// grimoire.js
/**
 * GrimoireUI - Handles displaying rule documentation in a modal
 */
export class GrimoireUI {
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
            titleEl.textContent = `📜 ${ruleName}`;
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

        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
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

