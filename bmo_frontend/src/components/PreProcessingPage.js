import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
function PreProcessingPage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [fileUrl, setFileUrl] = useState(""); // This will store the URL of the processed file
  const [processedData, setProcessedData] = useState([]); // State to store processed test cases data
  const [showResults, setShowResults] = useState(false); // State to control showing results
  const [currentPage, setCurrentPage] = useState(1); // Current page number
  const [resultsPerPage] = useState(5); // Number of results to show per page
  const navigate = useNavigate();

  // Function to process the mapped or unmapped transactions
  const handleProcess = async (transactionType) => {
    try {
      const response = await fetch("http://localhost:8000/api/pre-process-test-cases/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transaction_type: transactionType }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to process test cases.");

      setMessage(data.message);
      setFileUrl(data.processed_file_url); // The URL of the processed file
    } catch (err) {
      setError(err.message);
    }
  };

  // Function to fetch processed data when the button is clicked
  const fetchProcessedData = async () => {
    if (!fileUrl) return;

    try {
      // Request the file contents from the backend
      const data = await (await fetch(`http://localhost:8000/api/get-processed-test-cases/?file_url=${fileUrl}`)).json();

      // Ensure the correct structure and data format from backend
      if (data && data.processed_data) {
        setProcessedData(data.processed_data); // Store the processed data in state
      } else {
        setError("No processed data found.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  // Pagination Logic
  const indexOfLastResult = currentPage * resultsPerPage;
  const indexOfFirstResult = indexOfLastResult - resultsPerPage;
  const currentResults = processedData.slice(indexOfFirstResult, indexOfLastResult);
  const totalPages = Math.ceil(processedData.length / resultsPerPage);

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };
  const handleCompareTestCases = () => {
    if (fileUrl) {  
      navigate("/compare-test-cases", { state: { fileUrl: fileUrl } });
    }
  };

  return (
    <div style={{ margin: "2rem" }}>
      <h2>Pre-Processing Test Cases</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {message && <p style={{ color: "green" }}>{message}</p>}

      <button onClick={() => handleProcess("mapped")}>Process Mapped Transactions</button>
      <button onClick={() => handleProcess("unmapped")}>Process Unmapped Transactions</button>

      {fileUrl && (
        <div style={{ marginTop: "1rem" }}>
          <p>Download Processed File:</p>
          <a href={`http://localhost:8000${fileUrl}`} download target="_blank" rel="noopener noreferrer">
            <button>Download Processed Test Cases</button>
          </a>
        </div>
      )}

      {/* Show Results Button */}
      {fileUrl && (
        <div style={{ marginTop: "1rem" }}>
          <button onClick={() => { setShowResults(true); fetchProcessedData(); }}>Show Results</button>
        </div>
      )}

      {/* Display the processed test cases data */}
      {showResults && processedData.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Processed Test Cases</h3>
          <table style={{ width: "100%", borderCollapse: "collapse" }} border="1">
            <thead>
              <tr>
                <th>Test ID</th>
                <th>Description</th>
                <th>Transaction</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(currentResults) && currentResults.map((item, index) => (
                <tr key={index}>
                  <td>{item.test_case_id}</td>
                  <td>{item.Description}</td>
                  <td>{item.Transactions}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination Controls */}
          <div style={{ marginTop: "1rem" }}>
            <button onClick={handlePrevPage} disabled={currentPage === 1}>
              Previous
            </button>
            <span style={{ margin: "0 1rem" }}>
              Page {currentPage} of {totalPages}
            </span>
            <button onClick={handleNextPage} disabled={currentPage === totalPages}>
              Next
            </button>
          </div>
        </div>
      )}

      {/* Compare Test Cases Button: Trigger navigation */}
      {fileUrl && (
        <button onClick={handleCompareTestCases} style={{ marginTop: "1rem" }}>
          Compare Test Cases
        </button>
      )}
    </div>
  );
}

export default PreProcessingPage;
