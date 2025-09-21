import React, { useState } from 'react';
import { FileText, Settings } from 'lucide-react';
import { AnalysisResult, Finding } from './types/analysis';
import FileUpload from './components/FileUpload';
import ResultsDisplay from './components/ResultsDisplay';
import ConfigurationPanel from './components/ConfigurationPanel';

function App() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result);
    setIsAnalyzing(false);
    setError(null);
  };

  const handleAnalysisStart = () => {
    setIsAnalyzing(true);
    setError(null);
    setAnalysisResult(null);
  };

  const handleAnalysisError = (errorMessage: string) => {
    setError(errorMessage);
    setIsAnalyzing(false);
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setError(null);
    setIsAnalyzing(false);
  };

  const getSeverityCounts = (findings: Finding[]) => {
    return findings.reduce((acc, finding) => {
      acc[finding.severity] = (acc[finding.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  };

  return (
    <div className="app">
      <header>
        <h1>
          <FileText className="inline-icon" />
          Arcane Auditor 🔮
        </h1>
        <p>Cast mystical spells to reveal code quality issues in your Workday Extend applications</p>
      </header>

      {!analysisResult && !isAnalyzing && !error && (
        <div>
          <FileUpload
            onAnalysisStart={handleAnalysisStart}
            onAnalysisComplete={handleAnalysisComplete}
            onAnalysisError={handleAnalysisError}
          />
          
          <div className="mt-4">
            <button 
              className="secondary"
              onClick={() => setShowConfig(!showConfig)}
            >
              <Settings className="inline-icon" />
              {showConfig ? 'Hide' : 'Show'} Configuration
            </button>
          </div>

          {showConfig && (
            <ConfigurationPanel />
          )}
        </div>
      )}

      {isAnalyzing && (
        <div className="upload-area uploading">
          <div className="loading">
            <div className="spinner"></div>
            <p>🔄 Analyzing your application... Please wait</p>
          </div>
        </div>
      )}

      {error && (
        <div className="results">
          <h3>❌ Analysis Error</h3>
          <p>{error}</p>
          <button onClick={handleReset}>Try Again</button>
        </div>
      )}

      {analysisResult && (
        <ResultsDisplay 
          result={analysisResult}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App;
