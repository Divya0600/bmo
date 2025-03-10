
import React from 'react';

function DownloadLink({ fileUrl }) {
  // Construct the full download URL (adjust the hostname and port if needed)
  const downloadUrl = `http://localhost:8000/download/?file_url=${encodeURIComponent(fileUrl)}`;
  
  return (
    <a href={downloadUrl} download>
      Download Processed File
    </a>
  );
}

export default DownloadLink;
