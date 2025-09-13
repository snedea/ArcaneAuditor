import React, { useState } from 'react';
import { Download, RotateCcw, Filter, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import { AnalysisResult, Finding } from '../types/analysis';

interface ResultsDisplayProps {
  result: AnalysisResult;
  onReset: () => void;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ result, onReset }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'severity' | 'file' | 'rule'>('severity');

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

  const filteredFindings = result.findings.filter(finding => 
    filterSeverity === 'all' || finding.severity === filterSeverity
  );

  const sortedFindings = [...filteredFindings].sort((a, b) => {
    switch (sortBy) {
      case 'severity':
        const severityOrder = { SEVERE: 0, WARNING: 1, INFO: 2, HINT: 3 };
        return severityOrder[a.severity] - severityOrder[b.severity];
      case 'file':
        return a.file_path.localeCompare(b.file_path);
      case 'rule':
        return a.rule_id.localeCompare(b.rule_id);
      default:
        return 0;
    }
  });

  const severityCounts = getSeverityCounts(result.findings);

  const downloadResults = async () => {
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          findings: result.findings,
          format: 'excel'
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
              <label htmlFor="sort-by">Sort by:</label>
              <select
                id="sort-by"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="border rounded px-2 py-1"
              >
                <option value="severity">Severity</option>
                <option value="file">File</option>
                <option value="rule">Rule ID</option>
              </select>
            </div>
          </div>

          {/* Findings */}
          <div>
            <h4>🚨 Issues Found ({filteredFindings.length})</h4>
            {sortedFindings.map((finding, index) => (
              <div key={index} className={`finding ${finding.severity.toLowerCase()}`}>
                <div className="finding-header">
                  {getSeverityIcon(finding.severity)}
                  <strong>[{finding.rule_id}:{finding.line}]</strong> {finding.message}
                </div>
                <div className="finding-details">
                  <strong>File:</strong> {finding.file_path}
                  {finding.column && (
                    <>
                      <br />
                      <strong>Position:</strong> Line {finding.line}, Column {finding.column}
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default ResultsDisplay;
