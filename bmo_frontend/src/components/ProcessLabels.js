// src/components/ProcessLabels.js
import React, { useState } from 'react';
import DownloadLink from './DownloadLink';

function ProcessLabels({ fileUrl, metadataUrl }) {
  const [message, setMessage] = useState('');
  const [processedFileUrl, setProcessedFileUrl] = useState('');
  const [error, setError] = useState('');

  const handleProcess = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/process-labels/?file_url=${encodeURIComponent(fileUrl)}&metadata_url=${encodeURIComponent(metadataUrl)}`
      );
      const json = await response.json();
      if (response.ok) {
        setMessage(json.message);
        setProcessedFileUrl(json.processed_file_url);
      } else {
        setError(json.error || 'Error processing labels');
      }
    } catch (err) {
      setError('Error: ' + err.message);
    }
  };

  return (
    <div style={{ margin: '2rem' }}>
      <h2>Analyse Transactions</h2>
      <button onClick={handleProcess}>Continue to Analyse Transaction</button>
      {message && <p>{message}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {processedFileUrl && (
        <div>
          <p>Download the processed summary:</p>
          <DownloadLink fileUrl={processedFileUrl} />
        </div>
      )}
    </div>
  );
}

export default ProcessLabels;
