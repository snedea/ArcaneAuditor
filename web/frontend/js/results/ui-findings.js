// results/ui-findings.js - Findings UI (Summary, Filters, File Tree)

import { Templates } from './templates.js';
import { 
    getFileTypeFromPath,
    groupFindingsByFile,
    sortFindingsInGroup,
    sortFileGroups
} from '../utils.js';

export class FindingsUI {
    constructor(manager) {
        this.manager = manager;
        this.app = manager.app;
    }

    /**
     * Render the summary section
     */
    renderSummary() {
        const summary = document.getElementById('summary');
        const result = this.app.currentResult;
        
        summary.innerHTML = Templates.summary(result, this.app.uploadedFileName, this.app);
    }

    /**
     * Render the findings section with filters and file groups
     */
    renderFindings() {
        const findings = document.getElementById('findings');
        
        if (this.app.filteredFindings.length === 0) {
            findings.innerHTML = Templates.noIssues();
            return;
        }

        const groupedFindings = groupFindingsByFile(this.app.filteredFindings);
        const sortedGroupedFindings = sortFileGroups(groupedFindings, this.app.currentFilters.sortFilesBy);
        
        // Render the container with filters
        findings.innerHTML = Templates.findingsContainer(this.app.currentFilters, {
            sortBy: this.app.currentFilters.sortBy,
            sortFilesBy: this.app.currentFilters.sortFilesBy
        });
        
        // Get the findings-content container
        const findingsContent = findings.querySelector('.findings-content');
        if (!findingsContent) return;
        
        // Check if all findings are resolved for export bar
        const totalFindings = this.app.currentResult ? this.app.currentResult.findings.length : 0;
        const allOriginalResolved = totalFindings > 0 && this.app.resolvedFindings.size === totalFindings;
        const revalClean = this.app.lastRevalidationFindingCount === 0;
        const allGlobalResolved = allOriginalResolved && revalClean;
        const hasAnyEdited = this.app.editedFileContents.size > 0;

        // Insert export ZIP bar before findings content if all fixed
        if (allGlobalResolved && hasAnyEdited) {
            const exportBar = document.createElement('div');
            exportBar.className = 'export-zip-bar';
            exportBar.innerHTML = `
                <span class="export-zip-message">All findings fixed!</span>
                <button class="export-zip-btn" onclick="exportAllZip()">
                    Export Fixed Files (.zip)
                </button>
            `;
            findingsContent.parentElement.insertBefore(exportBar, findingsContent);
        }

        // Render file groups
        const fileGroupsHtml = Object.entries(sortedGroupedFindings).map(([filePath, fileFindings]) => {
            const isExpanded = this.app.expandedFiles.has(filePath);
            return Templates.fileGroup(
                filePath,
                fileFindings,
                isExpanded,
                this.app.currentFilters,
                this.app.currentFilters.sortBy,
                this.app
            );
        }).join('');

        findingsContent.innerHTML = fileGroupsHtml;
        
        // Update filter options after HTML is rendered
        // Note: File header clicks are handled by delegated event listener in app.js
        this.updateFilterOptions();
    }

    /**
     * Update filter dropdown options based on current findings
     */
    updateFilterOptions() {
        // Get all available severities and file types from current findings
        const availableSeverities = new Set(['all']);
        const availableFileTypes = new Set(['all']);
        
        this.app.currentResult.findings.forEach(finding => {
            availableSeverities.add(finding.severity);
            availableFileTypes.add(getFileTypeFromPath(finding.file_path));
        });

        // Update severity filter options
        const severitySelect = document.getElementById('severity-filter');
        if (severitySelect) {
            const currentSeverity = this.app.currentFilters.severity;
            const currentFileType = this.app.currentFilters.fileType;
            
            // If file type is selected, only show severities that exist for that file type
            let filteredSeverities = availableSeverities;
            if (currentFileType !== 'all') {
                filteredSeverities = new Set(['all']);
                this.app.currentResult.findings.forEach(finding => {
                    if (getFileTypeFromPath(finding.file_path) === currentFileType) {
                        filteredSeverities.add(finding.severity);
                    }
                });
            }
            
            // Update options
            severitySelect.innerHTML = '';
            
            // Sort with 'all' first, then alphabetically
            const sortedSeverities = Array.from(filteredSeverities).sort((a, b) => {
                if (a === 'all') return -1;
                if (b === 'all') return 1;
                return a.localeCompare(b);
            });
            
            sortedSeverities.forEach(severity => {
                const option = document.createElement('option');
                option.value = severity;
                
                // Calculate count for this severity
                let count = 0;
                if (severity === 'all') {
                    count = this.app.currentResult.findings.length;
                } else {
                    count = this.app.currentResult.findings.filter(finding => {
                        const severityMatch = finding.severity === severity;
                        const fileTypeMatch = currentFileType === 'all' || getFileTypeFromPath(finding.file_path) === currentFileType;
                        return severityMatch && fileTypeMatch;
                    }).length;
                }
                
                option.textContent = severity === 'all' ? `All Severities (${count})` : `${severity} (${count})`;
                if (severity === currentSeverity) {
                    option.selected = true;
                }
                severitySelect.appendChild(option);
            });
            
            // If current severity is not available, reset to 'all'
            if (!filteredSeverities.has(currentSeverity)) {
                this.app.currentFilters.severity = 'all';
                severitySelect.value = 'all';
            }
        }

        // Update file type filter options
        const fileTypeSelect = document.getElementById('file-type-filter');
        if (fileTypeSelect) {
            const currentFileType = this.app.currentFilters.fileType;
            const currentSeverity = this.app.currentFilters.severity;
            
            // If severity is selected, only show file types that have that severity
            let filteredFileTypes = availableFileTypes;
            if (currentSeverity !== 'all') {
                filteredFileTypes = new Set(['all']);
                this.app.currentResult.findings.forEach(finding => {
                    if (finding.severity === currentSeverity) {
                        filteredFileTypes.add(getFileTypeFromPath(finding.file_path));
                    }
                });
            }
            
            // Update options
            fileTypeSelect.innerHTML = '';
            
            // Sort with 'all' first, then alphabetically
            const sortedFileTypes = Array.from(filteredFileTypes).sort((a, b) => {
                if (a === 'all') return -1;
                if (b === 'all') return 1;
                return a.localeCompare(b);
            });
            
            sortedFileTypes.forEach(fileType => {
                const option = document.createElement('option');
                option.value = fileType;
                
                // Calculate count for this file type
                let count = 0;
                if (fileType === 'all') {
                    count = this.app.currentResult.findings.length;
                } else {
                    count = this.app.currentResult.findings.filter(finding => {
                        const fileTypeMatch = getFileTypeFromPath(finding.file_path) === fileType;
                        const severityMatch = currentSeverity === 'all' || finding.severity === currentSeverity;
                        return fileTypeMatch && severityMatch;
                    }).length;
                }
                
                option.textContent = fileType === 'all' ? `All File Types (${count})` : `${fileType} (${count})`;
                if (fileType === currentFileType) {
                    option.selected = true;
                }
                fileTypeSelect.appendChild(option);
            });
            
            // If current file type is not available, reset to 'all'
            if (!filteredFileTypes.has(currentFileType)) {
                this.app.currentFilters.fileType = 'all';
                fileTypeSelect.value = 'all';
            }
        }
    }

    /**
     * Expand all files
     */
    expandAllFiles() {
        const fileHeaders = document.querySelectorAll('.file-header');
        fileHeaders.forEach(header => {
            const filePath = header.dataset.filePath;
            this.app.expandedFiles.add(filePath);
        });
        this.renderFindings();
    }

    /**
     * Collapse all files
     */
    collapseAllFiles() {
        this.app.expandedFiles.clear();
        this.renderFindings();
    }
}

