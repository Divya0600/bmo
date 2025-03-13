import React, { useState, useEffect } from "react";
import axios from "axios";
import { useLocation } from "react-router-dom";

function TestCaseComparisonPage() {
  const [comparisonResults, setComparisonResults] = useState([]); // Store JSON results
  const [excelFileUrl, setExcelFileUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const location = useLocation();
  const { fileUrl } = location.state || {};

  // Fetch comparison results from CompareTestCasesAPI
  const compareTestCases = async () => {
    if (!fileUrl) return; // Ensure file URL is valid

    setLoading(true);
    setError(null);

    try {
      // API call: adjust URL/params as needed
      const response = await axios.get(`http://localhost:8000/api/compare-test-cases/?file_url=${fileUrl}`);
      // Expecting keys: comparison_results, comparison_results_file, and excel_output_path
      const { comparison_results, comparison_results_file, excel_output_path } = response.data;

      if (comparison_results) {
        setComparisonResults(comparison_results);
        setExcelFileUrl(excel_output_path);
      } else {
        throw new Error("Comparison results not found.");
      }
    } catch (err) {
      setError("Failed to fetch comparison results.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!fileUrl) return; // Prevent unnecessary API calls
    compareTestCases();
  }, [fileUrl]);

  // Dynamically get table columns (keys) if comparison results exist
  const tableHeaders = comparisonResults.length > 0 ? Object.keys(comparisonResults[0]) : [];

  return (
    <div>
      <h3>Test Case Comparison Results</h3>

      {loading && <p>Loading comparison results...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {comparisonResults.length > 0 ? (
        <table border="1" cellPadding="5" style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              {tableHeaders.map((header, index) => (
                <th key={index}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {comparisonResults.map((result, index) => (
              <tr key={index}>
                {tableHeaders.map((header, idx) => (
                  <td key={idx}>{result[header]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        !loading && <p>No comparison results found.</p>
      )}

      {/* Show downloadable links if available */}
      <div style={{ marginTop: "20px" }}>
        {excelFileUrl && (
          <p>
            <a href={`http://localhost:8000/media/${excelFileUrl}`} download>
              <button type="button">Download Excel File</button>
            </a>
          </p>
        )}
      </div>
    </div>
  );
}

export default TestCaseComparisonPage;
