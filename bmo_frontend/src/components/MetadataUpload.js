// src/components/MetadataUpload.js
import React, { useState } from 'react';

function MetadataUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadStatus('Please select a metadata file.');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Assuming you have a separate endpoint for metadata upload
      const response = await fetch('http://localhost:8000/api/upload-metadata/', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setUploadStatus('Metadata file uploaded successfully!');
        onUploadSuccess(data.file_url);
      } else {
        setUploadStatus(`Upload failed: ${data.error}`);
      }
    } catch (error) {
      setUploadStatus('Upload error: ' + error.message);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '2rem auto' }}>
      <h2>Upload Metadata File</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleFileChange} />
        <button type="submit" style={{ marginLeft: '1rem' }}>Upload Metadata</button>
      </form>
      {uploadStatus && <p>{uploadStatus}</p>}
    </div>
  );
}

export default MetadataUpload;