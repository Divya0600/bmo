import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

// Import your actual MetadataUpload component
// This component should use your existing API endpoint
const MetadataUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/api/upload-metadata/', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      if (response.ok) {
        onUploadSuccess(data.file_url);
      } else {
        setUploadStatus(`Upload failed: ${data.error}`);
      }
    } catch (error) {
      setUploadStatus('Upload error: ' + error.message);
    }
  };
  
  return (
    <div className="flex items-center space-x-4">
      <div className="relative flex-1">
        <input
          type="file"
          id="metadata-file"
          className="hidden"
          onChange={handleFileChange}
          accept=".csv,.xlsx,.xls"
        />
        <label
          htmlFor="metadata-file"
          className="block w-full bg-white border border-gray-300 rounded-md py-2 px-3 text-sm text-gray-700 cursor-pointer hover:bg-gray-50"
        >
          {file ? file.name : 'Choose file...'}
        </label>
      </div>
      <button
        onClick={handleSubmit}
        disabled={!file}
        className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm ${
          file ? 'text-white bg-blue-600 hover:bg-blue-700' : 'text-gray-400 bg-gray-200 cursor-not-allowed'
        }`}
      >
        Upload
      </button>
    </div>
  );
};

const AnalyzeTransactionPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Get the file_url from the URL parameter - this matches your existing flow
  const autoFileUrl = searchParams.get('file_url') || '';
  
  const [metadataUrl, setMetadataUrl] = useState('');
  const [dissectedFileUrl, setDissectedFileUrl] = useState(autoFileUrl);
  const [useAutoFile, setUseAutoFile] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [processedFileUrl, setProcessedFileUrl] = useState('');

  const handleMetadataUpload = (url) => {
    setMetadataUrl(url);
    setError('');
  };

  const handleDissectedFileUpload = (url) => {
    setDissectedFileUrl(url);
    setError('');
    setUseAutoFile(false);
  };

  const handleProcessLabels = async () => {
    if (!metadataUrl) {
      setError('Please upload a metadata file first.');
      return;
    }
    
    setIsProcessing(true);
    setError('');
    setMessage('');
    
    try {
      // This matches your existing API endpoint for processing labels
      const response = await fetch('http://localhost:8000/api/process-labels/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          csv_file_url: useAutoFile ? autoFileUrl : dissectedFileUrl,
          metadata_url: metadataUrl
        })
      });
      
      const data = await response.json();
      if (response.ok) {
        setMessage(data.message || 'Labels processed successfully');
        setProcessedFileUrl(data.processed_file_url || '');
      } else {
        setError(data.error || 'Failed to process labels');
      }
    } catch (err) {
      setError('Error: ' + err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleContinue = () => {
    // Navigate to transaction summary editor - matches your existing flow
    navigate(`/preprocess-test-cases?file_url=${encodeURIComponent(processedFileUrl)}`);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Analyze Transaction</h1>
        <p className="text-gray-600 mt-1">
          Upload metadata and analyze transactions from your dissected test cases.
        </p>
      </div>
      
      {error && (
        <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Dissected File</h2>
        
        <div className="space-y-4">
          <div className="flex items-center">
            <input
              id="use-auto"
              name="file-option"
              type="radio"
              className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              checked={useAutoFile}
              onChange={() => setUseAutoFile(true)}
            />
            <label htmlFor="use-auto" className="ml-3 block text-sm font-medium text-gray-700">
              Use Auto-populated File 
              <span className="ml-2 text-xs text-blue-600 font-normal">({autoFileUrl})</span>
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              id="upload-new"
              name="file-option"
              type="radio"
              className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              checked={!useAutoFile}
              onChange={() => setUseAutoFile(false)}
            />
            <label htmlFor="upload-new" className="ml-3 block text-sm font-medium text-gray-700">
              Upload New Dissected File
            </label>
          </div>
          
          {!useAutoFile && (
            <div className="ml-7 mt-2">
              <input
                type="file"
                id="dissected-file"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    const formData = new FormData();
                    formData.append('file', e.target.files[0]);
                    
                    fetch('http://localhost:8000/api/upload/', {
                      method: 'POST',
                      body: formData,
                    })
                    .then(response => response.json())
                    .then(data => {
                      if (data.file_url) {
                        handleDissectedFileUpload(data.file_url);
                      }
                    })
                    .catch(error => {
                      setError('Upload error: ' + error.message);
                    });
                  }
                }}
                accept=".csv,.xlsx,.xls"
              />
              <label
                htmlFor="dissected-file"
                className="block w-full bg-white border border-gray-300 rounded-md py-2 px-3 text-sm text-gray-700 cursor-pointer hover:bg-gray-50"
              >
                {!useAutoFile && dissectedFileUrl !== autoFileUrl 
                  ? dissectedFileUrl 
                  : 'Choose file...'}
              </label>
            </div>
          )}
        </div>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Metadata File</h2>
        <MetadataUpload onUploadSuccess={handleMetadataUpload} />
        
        {metadataUrl && (
          <div className="mt-3 flex items-center text-sm text-green-600">
            <svg className="h-5 w-5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
            Metadata file uploaded successfully
          </div>
        )}
      </div>
      
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <button
          onClick={handleProcessLabels}
          disabled={!metadataUrl || isProcessing}
          className={`w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
            !metadataUrl || isProcessing
              ? 'bg-blue-300 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
          }`}
        >
          {isProcessing ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing Labels...
            </>
          ) : (
            'Process Labels'
          )}
        </button>
      </div>
      
      {message && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-700">{message}</p>
            </div>
          </div>
        </div>
      )}
      
      {processedFileUrl && (
        <div className="mt-6 flex justify-between">
          <a 
            href={`http://localhost:8000/download/?file_url=${encodeURIComponent(processedFileUrl)}`} 
            download 
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg className="-ml-1 mr-2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
            Download Results
          </a>
          <button 
            onClick={handleContinue}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Continue
            <svg className="ml-2 -mr-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};

export default AnalyzeTransactionPage;