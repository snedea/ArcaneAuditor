import React, { useState } from 'react';
import { Download, RotateCcw, Filter, AlertTriangle, Info, CheckCircle, ChevronDown, ChevronRight, FileText } from 'lucide-react';
import { AnalysisResult, Finding } from '../types/analysis';

interface ResultsDisplayProps {
  result: AnalysisResult;
  onReset: () => void;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ result, onReset }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterFileType, setFilterFileType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'severity' | 'line' | 'rule'>('severity');
  const [sortFilesBy, setSortFilesBy] = useState<'alphabetical' | 'issue-count'>('alphabetical');
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'SEVERE':
        return <AlertTriangle className="inline-icon text-red-400" />;
      case 'WARNING':
        return <AlertTriangle className="inline-icon text-yellow-400" />;
      case 'INFO':
        return <Info className="inline-icon text-blue-400" />;
      case 'HINT':
        return <CheckCircle className="inline-icon text-green-400" />;
      default:
        return <Info className="inline-icon text-gray-400" />;
    }
  };

  const getSeverityCounts = (findings: Finding[]) => {
    return findings.reduce((acc, finding) => {
      acc[finding.severity] = (acc[finding.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  };

  const getFileTypeFromPath = (filePath: string): string => {
    const extension = filePath.split('.').pop()?.toLowerCase() || '';
    switch (extension) {
      case 'pmd':
        return 'PMD Files';
      case 'pod':
        return 'POD Files';
      case 'script':
        return 'Script Files';
      case 'json':
        return 'JSON Files';
      case 'xml':
        return 'XML Files';
      default:
        return 'Other Files';
    }
  };

  const getFileTypeCounts = (findings: Finding[]) => {
    return findings.reduce((acc, finding) => {
      const fileType = getFileTypeFromPath(finding.file_path);
      acc[fileType] = (acc[fileType] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  };

  const groupFindingsByFile = (findings: Finding[]) => {
    const grouped = findings.reduce((acc, finding) => {
      const filePath = finding.file_path || 'Unknown';
      if (!acc[filePath]) {
        acc[filePath] = [];
      }
      acc[filePath].push(finding);
      return acc;
    }, {} as Record<string, Finding[]>);

    // Sort file groups based on user preference
    const sortedEntries = Object.entries(grouped).sort(([fileA, findingsA], [fileB, findingsB]) => {
      switch (sortFilesBy) {
        case 'alphabetical':
          return fileA.localeCompare(fileB);
        case 'issue-count':
          return findingsB.length - findingsA.length; // Most issues first
        default:
          return 0;
      }
    });

    return Object.fromEntries(sortedEntries);
  };

  const toggleFileExpansion = (filePath: string) => {
    const newExpanded = new Set(expandedFiles);
    if (newExpanded.has(filePath)) {
      newExpanded.delete(filePath);
    } else {
      newExpanded.add(filePath);
    }
    setExpandedFiles(newExpanded);
  };

  const expandAllFiles = () => {
    const allFiles = Object.keys(groupFindingsByFile(filteredFindings));
    setExpandedFiles(new Set(allFiles));
  };

  const collapseAllFiles = () => {
    setExpandedFiles(new Set());
  };

  const filteredFindings = result.findings.filter(finding => {
    const severityMatch = filterSeverity === 'all' || finding.severity === filterSeverity;
    const fileTypeMatch = filterFileType === 'all' || getFileTypeFromPath(finding.file_path) === filterFileType;
    return severityMatch && fileTypeMatch;
  });

  // Sort findings within each file group instead of globally
  const sortFindingsInGroup = (findings: Finding[]) => {
    return [...findings].sort((a, b) => {
      switch (sortBy) {
        case 'severity':
          const severityOrder = { SEVERE: 0, WARNING: 1, INFO: 2, HINT: 3 };
          return severityOrder[a.severity] - severityOrder[b.severity];
        case 'line':
          return a.line - b.line;
        case 'rule':
          return a.rule_id.localeCompare(b.rule_id);
        default:
          return 0;
      }
    });
  };

  const severityCounts = getSeverityCounts(result.findings);
  const fileTypeCounts = getFileTypeCounts(result.findings);

  const downloadResults = async () => {
    try {
      const response = await fetch('/api/download/excel', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          findings: result.findings
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `extend-reviewer-results-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <div className="results">
      <div className="flex justify-between items-center mb-4">
        <h3>📊 Analysis Results</h3>
        <div className="flex gap-2">
          <button onClick={downloadResults} className="secondary">
            <Download className="inline-icon" />
            Download Excel
          </button>
          <button onClick={onReset}>
            <RotateCcw className="inline-icon" />
            Analyze Another
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="summary">
        <h4>📈 Summary</h4>
        <div className="summary-grid">
          <div className="summary-item">
            <div className="summary-number summary-number-blue">{result.total_files}</div>
            <div className="summary-label">Files Analyzed</div>
          </div>
          <div className="summary-item">
            <div className="summary-number summary-number-purple">{result.total_rules}</div>
            <div className="summary-label">Rules Executed</div>
          </div>
          <div className="summary-item">
            <div className="summary-number summary-number-orange">{result.findings.length}</div>
            <div className="summary-label">Issues Found</div>
          </div>
          <div className="summary-item">
            <div className="summary-filename">{result.zip_filename}</div>
            <div className="summary-label">Application</div>
          </div>
        </div>

        {Object.keys(severityCounts).length > 0 && (
          <div className="severity-section">
            <h5>Issues by Severity:</h5>
            <div className="severity-badges">
              {Object.entries(severityCounts).map(([severity, count]) => (
                <div key={severity} className="severity-badge">
                  {getSeverityIcon(severity)}
                  <span className="severity-count">{count}</span>
                  <span className="severity-name">{severity.toLowerCase()}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {Object.keys(fileTypeCounts).length > 0 && (
          <div className="severity-section">
            <h5>Issues by File Type:</h5>
            <div className="severity-badges">
              {Object.entries(fileTypeCounts).map(([fileType, count]) => (
                <div key={fileType} className="severity-badge">
                  <FileText className="inline-icon" />
                  <span className="severity-count">{count}</span>
                  <span className="severity-name">{fileType.toLowerCase()}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {result.findings.length === 0 ? (
        <div className="no-issues">
          <CheckCircle className="inline-icon" />
          <strong>No issues found!</strong> Your code looks great!
        </div>
      ) : (
        <>
          {/* Filters */}
          <div className="flex flex-wrap gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Filter className="inline-icon" />
              <label htmlFor="severity-filter">Filter by severity:</label>
              <select
                id="severity-filter"
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="border rounded px-2 py-1"
              >
                <option value="all">All ({result.findings.length})</option>
                {Object.entries(severityCounts).map(([severity, count]) => (
                  <option key={severity} value={severity}>
                    {severity} ({count})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor="file-type-filter">Filter by file type:</label>
              <select
                id="file-type-filter"
                value={filterFileType}
                onChange={(e) => setFilterFileType(e.target.value)}
                className="border rounded px-2 py-1"
              >
                <option value="all">All File Types ({result.findings.length})</option>
                {Object.entries(fileTypeCounts).map(([fileType, count]) => (
                  <option key={fileType} value={fileType}>
                    {fileType} ({count})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor="sort-by">Sort issues by:</label>
              <select
                id="sort-by"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="border rounded px-2 py-1"
              >
                <option value="severity">Severity</option>
                <option value="line">Line Number</option>
                <option value="rule">Rule ID</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor="sort-files-by">Sort files by:</label>
              <select
                id="sort-files-by"
                value={sortFilesBy}
                onChange={(e) => setSortFilesBy(e.target.value as any)}
                className="border rounded px-2 py-1"
              >
                <option value="alphabetical">Alphabetical</option>
                <option value="issue-count">Issue Count</option>
              </select>
            </div>
          </div>

          {/* File Controls */}
          <div className="flex justify-between items-center mb-4">
            <h4>🚨 Issues Found ({filteredFindings.length})</h4>
            <div className="flex gap-2">
              <button onClick={expandAllFiles} className="secondary" style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                Expand All
              </button>
              <button onClick={collapseAllFiles} className="secondary" style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}>
                Collapse All
              </button>
            </div>
          </div>

          {/* Findings grouped by file */}
          <div className="findings-by-file">
            {Object.entries(groupFindingsByFile(filteredFindings)).map(([filePath, fileFindings]) => {
              const isExpanded = expandedFiles.has(filePath);
              const fileName = filePath.split(/[/\\]/).pop() || filePath;
              const severityCounts = getSeverityCounts(fileFindings);
              
              return (
                <div key={filePath} className="file-group">
                  <div 
                    className="file-header" 
                    onClick={() => toggleFileExpansion(filePath)}
                  >
                    <div className="file-header-left">
                      {isExpanded ? <ChevronDown className="inline-icon" /> : <ChevronRight className="inline-icon" />}
                      <FileText className="inline-icon" />
                      <span className="file-name">{fileName}</span>
                      <span className="file-path">{filePath}</span>
                    </div>
                    <div className="file-header-right">
                      <span className="file-count">{fileFindings.length} issue{fileFindings.length !== 1 ? 's' : ''}</span>
                      {Object.entries(severityCounts).map(([severity, count]) => (
                        <span key={severity} className={`severity-count-badge ${severity.toLowerCase()}`}>
                          {count} {severity.toLowerCase()}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <div className="file-findings">
                      {sortFindingsInGroup(fileFindings)
                        .map((finding, index) => (
                          <div key={index} className={`finding ${finding.severity.toLowerCase()}`}>
                            <div className="finding-header">
                              {getSeverityIcon(finding.severity)}
                              <strong>[{finding.rule_id}:{finding.line}]</strong> {finding.message}
                            </div>
                            <div className="finding-details">
                              {finding.column && (
                                <span><strong>Position:</strong> Line {finding.line}, Column {finding.column}</span>
                              )}
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};

export default ResultsDisplay;
