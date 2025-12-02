// results/ui-context.js - Context panel UI logic

import { Templates } from './templates.js';

export class ContextUI {
    constructor(manager) {
        this.manager = manager;
        this.app = manager.app;
        this.contextPanelExpanded = false;
    }

    /**
     * Display context data in the context panel
     * @param {Object} contextData - The context data to display
     */
    displayContext(contextData) {
        if (!contextData) return;
        
        const contextSection = document.getElementById('context-section');
        const contextContent = document.getElementById('context-content');
        const contextIcon = document.getElementById('context-icon');
        const contextTitleText = document.getElementById('context-title-text');
        
        // Determine if analysis is complete or partial
        const isComplete = contextData.context_status === 'complete';
        
        // Update icon and title with magical flair
        if (isComplete) {
            contextIcon.textContent = '✨';
            contextTitleText.textContent = 'Evaluation ✦';
        } else {
            contextIcon.textContent = '🌙';
            contextTitleText.textContent = 'Divination Incomplete';
        }
        
        // Add status badge to the header
        const contextHeader = document.querySelector('.context-header');
        if (contextHeader) {
            // Remove any existing status badge
            const existingBadge = contextHeader.querySelector('.context-header-badge');
            if (existingBadge) {
                existingBadge.remove();
            }
            
            // Determine badge text based on context
            let badgeText = '';
            if (isComplete) {
                badgeText = '✅ Complete';
            } else {
                // Check if any rules were skipped
                const hasSkippedRules = contextData.impact && 
                    ((contextData.impact.rules_not_executed && contextData.impact.rules_not_executed.length > 0) ||
                     (contextData.impact.rules_partially_executed && contextData.impact.rules_partially_executed.length > 0));
                
                if (hasSkippedRules) {
                    badgeText = '⚠️ Partial';
                } else {
                    badgeText = '⚠️ Partial';
                }
            }
            
            // Add new status badge
            const statusBadge = document.createElement('div');
            statusBadge.className = `context-header-badge ${isComplete ? 'complete' : 'partial'}`;
            statusBadge.textContent = badgeText;
            contextHeader.appendChild(statusBadge);
        }
        
        // Build context content HTML using template
        const html = Templates.contextPanel(contextData, isComplete, this.app.currentResult);
        
        contextContent.innerHTML = html;
        contextSection.style.display = 'block';
        
        // Set initial collapsed state
        this.contextPanelExpanded = false;
        const contextToggle = document.getElementById('context-toggle');
        if (contextToggle) {
            contextToggle.classList.remove('expanded');
        }
    }

    /**
     * Toggle the context panel open/closed
     */
    toggleContextPanel() {
        const contextContent = document.getElementById('context-content');
        const contextToggle = document.getElementById('context-toggle');
        
        this.contextPanelExpanded = !this.contextPanelExpanded;
        
        if (this.contextPanelExpanded) {
            contextContent.classList.remove('collapsed');
            contextToggle.classList.add('expanded');
        } else {
            contextContent.classList.add('collapsed');
            contextToggle.classList.remove('expanded');
        }
    }

    /**
     * Reset the context panel state
     */
    reset() {
        this.contextPanelExpanded = false;
    }
}

