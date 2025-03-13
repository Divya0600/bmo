// src/components/AnalyseTransactionPage.js
import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import MetadataUpload from './MetadataUpload';
import FileUpload from './FileUpload';
import DownloadLink from './DownloadLink';
import TransactionSummaryEditor from './TransactionSummaryEditor';

function AnalyseTransactionPage() {
  const [searchParams] = useSearchParams();
  // Auto-populated dissected file URL passed via query parameters.
  const autoFileUrl = searchParams.get('file_url') || '';
  
  // State to control whether to use the auto file or a manually uploaded file.
  const [useAutoFile, setUseAutoFile] = useState(true);
  // This state will hold the dissected file URL, either auto or uploaded.
  const [dissectedFileUrl, setDissectedFileUrl] = useState(autoFileUrl);
  
  const [metadataUrl, setMetadataUrl] = useState('');
  const [message, setMessage] = useState('');
  const [processedSummaryUrl, setProcessedSummaryUrl] = useState('');
  const [error, setError] = useState('');

  // Handler when metadata file is uploaded.
  const handleMetadataUploadSuccess = (url) => {
    setMetadataUrl(url);
  };

  // Handler when a new dissected file is uploaded manually.
  const handleDissectedFileUploadSuccess = (url) => {
    setDissectedFileUrl(url);
  };

  const handleProcess = async () => {
    // Ensure both a dissected file and metadata file URL are provided.
    if (!metadataUrl) {
      setError('Please upload or enter a metadata file URL.');
      return;
    }
    if (!dissectedFileUrl) {
      setError('Please upload a dissected file or use the auto-populated file.');
      return;
    }
    
    // Debugging: Print the URLs being sent in the request
    console.log('Sending request with:', {
      csv_file_url: dissectedFileUrl,
      metadata_url: metadataUrl
    });

    try {
      const response = await fetch('http://localhost:8000/api/process-labels/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          csv_file_url: dissectedFileUrl,
          metadata_url: metadataUrl
        })
      });
      const json = await response.json();
      console.log('API Response:', json);
      if (response.ok) {
        setMessage(json.message);
        setProcessedSummaryUrl(json.processed_file_url);
      } else {
        setError(json.error || 'Error processing labels.');
      }
    } catch (err) {
      setError('Error: ' + err.message);
    }
  };

  return (
    <div style={{ margin: '2rem' }}>
      <h2>Analyse Transaction</h2>
      
      <div>
        <p><strong>Dissected File:</strong></p>
        <div>
          <label>
            <input
              type="radio"
              name="dissectedFileOption"
              value="auto"
              checked={useAutoFile}
              onChange={() => {
                setUseAutoFile(true);
                setDissectedFileUrl(autoFileUrl);
              }}
            />
            Use Auto-populated File ({autoFileUrl})
          </label>
        </div>
        <div>
          <label>
            <input
              type="radio"
              name="dissectedFileOption"
              value="manual"
              checked={!useAutoFile}
              onChange={() => {
                setUseAutoFile(false);
                setDissectedFileUrl('');
              }}
            />
            Upload New Dissected File
          </label>
        </div>
        {!useAutoFile && (
          <div style={{ marginTop: '1rem' }}>
            <FileUpload onUploadSuccess={handleDissectedFileUploadSuccess} />
          </div>
        )}
      </div>
      
      <div style={{ marginTop: '1rem' }}>
        <p>Upload a metadata file:</p>
        <MetadataUpload onUploadSuccess={handleMetadataUploadSuccess} />
      </div>
      
      <div style={{ marginTop: '1rem' }}>
        <button onClick={handleProcess}>Process Labels</button>
      </div>
      
      {message && <p>{message}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      {processedSummaryUrl && (
        <div>
          <p>Download the processed summary:</p>
          <DownloadLink fileUrl={processedSummaryUrl} />
        </div>
      )}

      {/* Render TransactionSummaryEditor and pass metadataUrl and processedSummaryUrl */}
      {processedSummaryUrl && (
        <div style={{ marginTop: '2rem' }}>
          <TransactionSummaryEditor metadataUrl={metadataUrl} processedFileUrl={processedSummaryUrl} dissectedFileUrl={dissectedFileUrl} />
        </div>
      )}
    </div>
  );
}

export default AnalyseTransactionPage;
