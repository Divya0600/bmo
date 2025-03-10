// src/components/TransactionSummaryEditor.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from "react-router-dom";

function TransactionSummaryEditor({ metadataUrl, processedFileUrl, dissectedFileUrl }) {
  const [mapped, setMapped] = useState([]);
  const [unmapped, setUnmapped] = useState([]);
  const [baselined, setBaselined] = useState([]);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [updatedCsvUrl, setUpdatedCsvUrl] = useState('');
  const [summaryFileUrl, setSummaryFileUrl] = useState('');
  const [summaryData, setSummaryData] = useState([]); // Store summary table data
  const navigate = useNavigate();
  const fetchSummary = async () => {
    setError('');
    try {
      const url = new URL('http://localhost:8000/api/get-transaction-summary/');
      url.searchParams.append('metadata_url', metadataUrl);
      url.searchParams.append('processed_file_url', processedFileUrl);

      console.log('Fetching transaction summary from:', url);

      const response = await fetch(url);
      const data = await response.json();

      if (!response.ok) throw new Error(data.error || 'Failed to fetch transaction summary.');

      setMapped(data.mapped || []);
      setUnmapped(data.unmapped || []);
      setBaselined(data.baselined || []);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [metadataUrl, processedFileUrl]);

  const handleChange = (index, newValue, type) => {
    const setter = type === 'mapped' ? setMapped : setUnmapped;
    setter(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], target: newValue };
      return updated;
    });
  };

  const fetchSummaryTable = async (fileUrl) => {
    try {
      const response = await fetch(`http://localhost:8000${fileUrl}`);
      const text = await response.text();
      
      // Parse CSV format (assuming "Transaction,Count,Target" structure)
      const rows = text.split("\n").map(row => row.split(","));
      if (rows.length > 1) {
        const headers = rows[0]; // First row as headers
        const data = rows.slice(1).map(row => ({
          transaction: row[0] || '',
          count: row[1] || '0',
          target: row[2] || '',
        }));
        setSummaryData(data);
      }
    } catch (err) {
      setError('Error fetching summary content: ' + err.message);
    }
  };

  const saveUpdatedSummary = async () => {
    const payload = {
      csv_file_url: dissectedFileUrl,
      metadata_url: metadataUrl,
      synonyms: [...mapped, ...unmapped].map(({ transaction, target }) => ({
        source_transaction: transaction,
        target_transaction: target || transaction,
      })),
    };

    console.log('Saving updated summary:', payload);

    try {
      const response = await fetch('http://localhost:8000/api/update-transaction-summary/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to update summary.');

      setMessage(data.message || 'Summary updated successfully.');
      setUpdatedCsvUrl(data.updated_csv);
      setSummaryFileUrl(data.processed_file_url);

      // Fetch and display summary table
      fetchSummary();
    } catch (err) {
      setError('Error: ' + err.message);
    }
  };

  return (
    <div style={{ margin: '2rem' }}>
      <h2>Transaction Summary Editor</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {message && <p style={{ color: 'green' }}>{message}</p>}

      {[{ label: 'Mapped', data: mapped }, { label: 'Unmapped', data: unmapped }].map(({ label, data }, typeIndex) => (
        <div key={typeIndex} style={{ marginBottom: '2rem' }}>
          <h3>{label} Transactions</h3>
          {data.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }} border="1">
              <thead>
                <tr>
                  <th>Transaction</th>
                  <th>Count</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item, index) => (
                  <tr key={index}>
                    <td>{item.transaction}</td>
                    <td>{item.count}</td>
                    <td>
                      <select
                        value={item.target || item.transaction}
                        onChange={(e) => handleChange(index, e.target.value, label.toLowerCase())}
                      >
                        <option value="">-- Select Transaction --</option>
                        {baselined.map((name, idx) => (
                          <option key={idx} value={name}>{name}</option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No {label.toLowerCase()} transactions available.</p>
          )}
        </div>
      ))}

      <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
        <button onClick={saveUpdatedSummary}>Save Updated Summary</button>
        <button onClick={() => navigate("/preprocess-test-cases")}>Continue</button>
      </div>

      {/* Download links for updated files */}
      {updatedCsvUrl && (
        <div style={{ marginTop: '1rem' }}>
          <p>Download Updated CSV:</p>
          <a href={`http://localhost:8000${updatedCsvUrl}`} download target="_blank" rel="noopener noreferrer">
            <button>Download Updated CSV</button>
          </a>
        </div>
      )}

      {summaryFileUrl && (
        <div style={{ marginTop: '1rem' }}>
          <p>Download Summary File:</p>
          <a href={`http://localhost:8000${summaryFileUrl}`} download target="_blank" rel="noopener noreferrer">
            <button>Download Summary File</button>
          </a>
        </div>
      )}

      {/* Display summary file content in a table */}
      {summaryData.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Summary File Transactions</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }} border="1">
            <thead>
              <tr>
                <th>Transaction</th>
                <th>Count</th>
                <th>Target</th>
              </tr>
            </thead>
            <tbody>
              {summaryData.map((item, index) => (
                <tr key={index}>
                  <td>{item.transaction}</td>
                  <td>{item.count}</td>
                  <td>{item.target}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default TransactionSummaryEditor;
