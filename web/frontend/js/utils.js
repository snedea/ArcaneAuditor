// Utility functions and helpers for Arcane Auditor web interface

export function getSeverityIcon(severity) {
    const icons = {
        'ACTION': '🚨',
        'ADVICE': 'ℹ️',
        'ISSUES': '🟡'
    };
    return icons[severity] || '⚪';
}

export function getSeverityCounts(findings) {
    const counts = findings.reduce((acc, finding) => {
        const severity = finding.severity || 'unknown';
        acc[severity] = (acc[severity] || 0) + 1;
        return acc;
    }, {});
    
    // Define severity order: ISSUES, ACTION, ADVICE (uppercase to match backend)
    const severityOrder = ['ISSUES', 'ACTION', 'ADVICE'];
    
    // Create ordered object
    const orderedCounts = {};
    severityOrder.forEach(severity => {
        if (counts[severity]) {
            orderedCounts[severity] = counts[severity];
        }
    });
    
    // Add any other severities not in the predefined order
    Object.keys(counts).forEach(severity => {
        if (!severityOrder.includes(severity)) {
            orderedCounts[severity] = counts[severity];
        }
    });
    
    return orderedCounts;
}

export function getOrderedSeverityEntries(severityCounts) {
    // Define severity order: ISSUES, ACTION, ADVICE (uppercase to match backend)
    const severityOrder = ['ISSUES', 'ACTION', 'ADVICE'];
    
    // Create ordered array of entries
    const orderedEntries = [];
    severityOrder.forEach(severity => {
        if (severityCounts[severity]) {
            orderedEntries.push([severity, severityCounts[severity]]);
        }
    });
    
    // Add any other severities not in the predefined order
    Object.entries(severityCounts).forEach(([severity, count]) => {
        if (!severityOrder.includes(severity)) {
            orderedEntries.push([severity, count]);
        }
    });
    
    return orderedEntries;
}

export function getFileTypeFromPath(filePath) {
    if (!filePath) return 'unknown';
    const extension = filePath.split('.').pop()?.toLowerCase();
    return extension || 'unknown';
}

export function groupFindingsByFile(findings) {
    const groups = {};
    findings.forEach(finding => {
        const filePath = finding.file_path || 'unknown';
        if (!groups[filePath]) {
            groups[filePath] = [];
        }
        groups[filePath].push(finding);
    });
    return groups;
}

export function sortFindingsInGroup(findings, sortBy = 'severity') {
    const severityOrder = { 'ACTION': 0, 'ADVICE': 1, 'ISSUES': 2 };
    
    return [...findings].sort((a, b) => {
        switch (sortBy) {
            case 'severity':
                const aSeverity = severityOrder[a.severity] ?? 999;
                const bSeverity = severityOrder[b.severity] ?? 999;
                if (aSeverity !== bSeverity) return aSeverity - bSeverity;
                return a.line - b.line;
            case 'line':
                return a.line - b.line;
            case 'rule':
                return a.rule_id.localeCompare(b.rule_id);
            default:
                return 0;
        }
    });
}

export function sortFileGroups(fileGroups, sortFilesBy = 'alphabetical') {
    const entries = Object.entries(fileGroups);
    
    entries.sort(([pathA, findingsA], [pathB, findingsB]) => {
        switch (sortFilesBy) {
            case 'alphabetical':
                // Extract just the filename (without job ID prefix) for sorting
                const fileNameA = (pathA.split(/[/\\]/).pop() || pathA).replace(/^[a-f0-9-]+_/, '');
                const fileNameB = (pathB.split(/[/\\]/).pop() || pathB).replace(/^[a-f0-9-]+_/, '');
                return fileNameA.localeCompare(fileNameB);
            case 'issue-count':
                return findingsB.length - findingsA.length;
            default:
                return 0;
        }
    });
    
    return Object.fromEntries(entries);
}

export async function downloadResults(result, options = {}) {
    // Auto-enable silent mode for desktop app unless explicitly overridden
    const defaultOptions = {
        silent: window.pywebview ? true : false,
        ...options
    };

    if (!result) {
        console.error('No results to download');
        if (!defaultOptions.silent) {
            alert('No results to download');
        }
        return { success: false, error: 'No results to download' };
    }
    
    try {
        // Get the current job ID from the results
        const jobId = result?.job_id;
        if (!jobId) {
            throw new Error('No job ID available for download');
        }

        // Check if running in pywebview (desktop app)
        if (window.pywebview) {
            // Desktop app - auto-save to Downloads folder
            const downloadResult = await window.pywebview.api.download_file(jobId);
            if (downloadResult.success) {
                console.log(`File auto-saved to: ${downloadResult.path}`);
                // Only show alert if not in silent mode
                if (!defaultOptions.silent) {
                    alert(`File saved successfully to:\n${downloadResult.path}`);
                }
                return { success: true, path: downloadResult.path, filename: downloadResult.filename };
            } else {
                throw new Error(downloadResult.error || 'Download failed');
            }
        } else {
            // Web browser - use normal download mechanism
            const response = await fetch(`/api/download/${jobId}`);

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `arcane-auditor-results-${new Date().toISOString().split('T')[0]}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                console.log('File downloaded successfully');
                return { success: true };
            } else {
                throw new Error('Download failed');
            }
        }
    } catch (error) {
        console.error('Download failed:', error);
        if (!defaultOptions.silent) {
            alert('Download failed. Please try again.');
        }
        return { success: false, error: error.message };
    }
}

// LocalStorage helpers
export function getLastSelectedConfig() {
    return localStorage.getItem('arcane-auditor-selected-config') || null;
}

export function saveSelectedConfig(configId) {
    localStorage.setItem('arcane-auditor-selected-config', configId);
}

export function getLastSortBy() {
    return localStorage.getItem('arcane-auditor-sort-by') || 'severity';
}

export function getLastSortFilesBy() {
    return localStorage.getItem('arcane-auditor-sort-files-by') || 'alphabetical';
}

export function saveSortBy(sortBy) {
    localStorage.setItem('arcane-auditor-sort-by', sortBy);
}

export function saveSortFilesBy(sortFilesBy) {
    localStorage.setItem('arcane-auditor-sort-files-by', sortFilesBy);
}

/**
 * Compute a side-by-side line diff between two strings using LCS.
 * Returns an array of row objects:
 *   { type: 'unchanged'|'removed'|'added'|'modified',
 *     oldLineNo, oldText, newLineNo, newText }
 */
export function computeLineDiff(original, fixed) {
    const oldLines = original.split('\n');
    const newLines = fixed.split('\n');
    const m = oldLines.length;
    const n = newLines.length;

    // Build LCS length table
    const dp = Array.from({ length: m + 1 }, () => new Uint16Array(n + 1));
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (oldLines[i - 1] === newLines[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1] + 1;
            } else {
                dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
    }

    // Backtrack to produce edit ops
    const ops = [];
    let i = m, j = n;
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
            ops.push({ op: 'equal', oldIdx: i - 1, newIdx: j - 1 });
            i--; j--;
        } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
            ops.push({ op: 'add', newIdx: j - 1 });
            j--;
        } else {
            ops.push({ op: 'remove', oldIdx: i - 1 });
            i--;
        }
    }
    ops.reverse();

    // Merge consecutive remove+add pairs into 'modified' rows
    const rows = [];
    let k = 0;
    while (k < ops.length) {
        const curr = ops[k];
        if (curr.op === 'equal') {
            rows.push({
                type: 'unchanged',
                oldLineNo: curr.oldIdx + 1,
                oldText: oldLines[curr.oldIdx],
                newLineNo: curr.newIdx + 1,
                newText: newLines[curr.newIdx],
            });
            k++;
        } else if (curr.op === 'remove') {
            // Collect consecutive removes
            const removes = [];
            while (k < ops.length && ops[k].op === 'remove') {
                removes.push(ops[k]);
                k++;
            }
            // Collect consecutive adds
            const adds = [];
            while (k < ops.length && ops[k].op === 'add') {
                adds.push(ops[k]);
                k++;
            }
            // Pair them up as 'modified', leftover as pure remove/add
            const paired = Math.min(removes.length, adds.length);
            for (let p = 0; p < paired; p++) {
                rows.push({
                    type: 'modified',
                    oldLineNo: removes[p].oldIdx + 1,
                    oldText: oldLines[removes[p].oldIdx],
                    newLineNo: adds[p].newIdx + 1,
                    newText: newLines[adds[p].newIdx],
                });
            }
            for (let p = paired; p < removes.length; p++) {
                rows.push({
                    type: 'removed',
                    oldLineNo: removes[p].oldIdx + 1,
                    oldText: oldLines[removes[p].oldIdx],
                    newLineNo: null,
                    newText: '',
                });
            }
            for (let p = paired; p < adds.length; p++) {
                rows.push({
                    type: 'added',
                    oldLineNo: null,
                    oldText: '',
                    newLineNo: adds[p].newIdx + 1,
                    newText: newLines[adds[p].newIdx],
                });
            }
        } else {
            // standalone add
            rows.push({
                type: 'added',
                oldLineNo: null,
                oldText: '',
                newLineNo: curr.newIdx + 1,
                newText: newLines[curr.newIdx],
            });
            k++;
        }
    }
    return rows;
}