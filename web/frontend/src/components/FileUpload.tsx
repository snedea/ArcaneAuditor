import React, { useRef, useState } from 'react';
import { Upload, FileArchive } from 'lucide-react';
import { AnalysisResult } from '../types/analysis';

interface FileUploadProps {
  onAnalysisStart: () => void;
  onAnalysisComplete: (result: AnalysisResult) => void;
  onAnalysisError: (error: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onAnalysisStart,
  onAnalysisComplete,
  onAnalysisError,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFileSelect = (file: File) => {
    if (!file.name.endsWith('.zip')) {
      onAnalysisError('Please select a ZIP file');
      return;
    }

    uploadFile(file);
  };

  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      onAnalysisStart();

      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        onAnalysisComplete(data);
      } else {
        throw new Error(data.detail || 'Analysis failed');
      }
    } catch (error) {
      onAnalysisError(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div
      className={`upload-area ${isDragOver ? 'dragover' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".zip"
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
      />
      
      <Upload size={48} className="mx-auto mb-4 text-gray-400" />
      
      <h3>Upload Your Extend Application</h3>
      <p>Drag and drop your ZIP file here, or click to select</p>
      
      <div className="mt-4">
        <button type="button">
          <FileArchive className="inline-icon" />
          Choose ZIP File
        </button>
      </div>
      
      <p className="text-sm text-gray-500 mt-2">
        Supported: .zip files containing Workday Extend applications
      </p>
    </div>
  );
};

export default FileUpload;
