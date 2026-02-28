// results/manager.js - Controller that coordinates Results UI

import { FindingsUI } from './ui-findings.js';
import { ContextUI } from './ui-context.js';
import { 
    getFileTypeFromPath,
    getLastSortBy,
    getLastSortFilesBy,
    saveSortBy,
    saveSortFilesBy
} from '../utils.js';

export class ResultsManager {
    constructor(app) {
        this.app = app;
        
        // Initialize UI components
        this.findingsUI = new FindingsUI(this);
        this.contextUI = new ContextUI(this);
    }

    /**
     * Render all results (summary and findings)
     */
    renderResults() {
        this.findingsUI.renderSummary();
        this.findingsUI.renderFindings();
    }

    /**
     * Display context data
     * @param {Object} contextData - The context data to display
     */
    displayContext(contextData) {
        this.contextUI.displayContext(contextData);
    }

    /**
     * Toggle context panel
     */
    toggleContextPanel() {
        this.contextUI.toggleContextPanel();
    }

    /**
     * Reset for new upload
     */
    resetForNewUpload() {
        // Reset app-level state
        if (this.app) {
            this.app.filteredFindings = [];
            if (this.app.expandedFiles) {
                this.app.expandedFiles.clear();
            }
            this.app.currentFilters = {
                severity: 'all',
                fileType: 'all',
                sortBy: getLastSortBy(),
                sortFilesBy: getLastSortFilesBy()
            };
        }
        // Reset UI state
        this.contextUI.reset();
    }

    /**
     * Update severity filter
     * @param {string} severity - The severity to filter by
     */
    updateSeverityFilter(severity) {
        this.app.currentFilters.severity = severity;
        this.findingsUI.updateFilterOptions();
        this.applyFilters();
    }

    /**
     * Update file type filter
     * @param {string} fileType - The file type to filter by
     */
    updateFileTypeFilter(fileType) {
        this.app.currentFilters.fileType = fileType;
        this.findingsUI.updateFilterOptions();
        this.applyFilters();
    }

    /**
     * Update sort by option
     * @param {string} sortBy - The sort option
     */
    updateSortBy(sortBy) {
        this.app.currentFilters.sortBy = sortBy;
        saveSortBy(sortBy);
        this.findingsUI.renderFindings();
    }

    /**
     * Update sort files by option
     * @param {string} sortFilesBy - The file sort option
     */
    updateSortFilesBy(sortFilesBy) {
        this.app.currentFilters.sortFilesBy = sortFilesBy;
        saveSortFilesBy(sortFilesBy);
        this.findingsUI.renderFindings();
    }

    /**
     * Apply filters to findings
     */
    applyFilters() {
        this.app.filteredFindings = this.app.currentResult.findings.filter(finding => {
            const severityMatch = this.app.currentFilters.severity === 'all' || finding.severity === this.app.currentFilters.severity;
            const fileTypeMatch = this.app.currentFilters.fileType === 'all' || getFileTypeFromPath(finding.file_path) === this.app.currentFilters.fileType;
            return severityMatch && fileTypeMatch;
        });
        this.findingsUI.renderFindings();
    }

    /**
     * Expand all files
     */
    expandAllFiles() {
        this.findingsUI.expandAllFiles();
    }

    /**
     * Collapse all files
     */
    collapseAllFiles() {
        this.findingsUI.collapseAllFiles();
    }

    /**
     * Toggle file expansion
     * @param {string} filePath - The file path to toggle
     */
    toggleFileExpansion(filePath) {
        if (this.app.expandedFiles.has(filePath)) {
            this.app.expandedFiles.delete(filePath);
        } else {
            this.app.expandedFiles.add(filePath);
        }
        this.findingsUI.renderFindings();
    }
}

