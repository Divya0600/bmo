// src/components/TestCasesPagination.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DownloadLink from './DownloadLink';

function TestCasesPagination({ fileUrl }) {
  const [data, setData] = useState([]);
  const [processedFileUrl, setProcessedFileUrl] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState('');
  const [showAll, setShowAll] = useState(false);
  const navigate = useNavigate();

  const fetchData = async (page = 1) => {
    try {
      let url = `http://localhost:8000/api/dissect-test-cases/?file_url=${encodeURIComponent(fileUrl)}`;
      if (showAll) {
        url += "&all=true";
      } else {
        url += `&page=${page}`;
      }
      const response = await fetch(url);
      const json = await response.json();
      if (response.ok) {
        setData(json.data);
        if (!showAll) {
          // Only update totalPages if changed to avoid triggering loops.
          if (json.total_pages !== totalPages) {
            setTotalPages(json.total_pages);
          }
        }
        if (json.processed_file_url) {
          setProcessedFileUrl(json.processed_file_url);
        }
      } else {
        setError(json.error || 'Error fetching data');
      }
    } catch (err) {
      setError('Error: ' + err.message);
    }
  };

  // Run fetchData only when fileUrl or showAll changes.
  useEffect(() => {
    // Reset to first page when fileUrl or showAll changes.
    setCurrentPage(1);
    fetchData(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileUrl, showAll]);

  const goToPage = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      fetchData(page);
    }
  };

  const handleContinue = () => {
    // Pass the processed file URL (or fallback to original fileUrl if needed)
    const urlToPass = processedFileUrl || fileUrl;
    navigate(`/analyse-transaction?file_url=${encodeURIComponent(urlToPass)}`);
  };

  return (
    <div style={{ margin: '2rem' }}>
      <h2>Processed Test Cases</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div>
        <button onClick={() => setShowAll((prev) => !prev)}>
          {showAll ? 'Show Paginated' : 'Show All'}
        </button>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem' }}>
        <thead>
          <tr>
            <th>Test ID</th>
            <th>Description</th>
            <th>Transaction</th>
          </tr>
        </thead>
        <tbody>
          {data.length > 0 ? data.map((record, index) => (
            <tr key={index}>
              <td>{record.test_case_id}</td>
              <td>{record.Description}</td>
              <td>{record.Transactions}</td>
            </tr>
          )) : (
            <tr>
              <td colSpan="3">No records found.</td>
            </tr>
          )}
        </tbody>
      </table>
      {!showAll && (
        <div style={{ marginTop: '1rem' }}>
          <button onClick={() => goToPage(1)} disabled={currentPage === 1}>First</button>
          <button onClick={() => goToPage(currentPage - 1)} disabled={currentPage === 1}>Previous</button>
          <span style={{ margin: '0 1rem' }}>Page {currentPage} of {totalPages}</span>
          <button onClick={() => goToPage(currentPage + 1)} disabled={currentPage === totalPages}>Next</button>
          <button onClick={() => goToPage(totalPages)} disabled={currentPage === totalPages}>Last</button>
        </div>
      )}
      {/* Render download link for the processed (dissected) file */}
      {processedFileUrl && <DownloadLink fileUrl={processedFileUrl} />}
      <div style={{ marginTop: '1rem' }}>
        <button onClick={handleContinue}>Continue to Analyse Transaction</button>
      </div>
    </div>
  );
}

export default TestCasesPagination;
