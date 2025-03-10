import React, { useState, useEffect } from "react";
import axios from "axios";
import { useLocation } from "react-router-dom";

function TestCaseComparisonPage() {
  const [comparisonResults, setComparisonResults] = useState([]);  // Store JSON directly
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
      // Step 1: Call CompareTestCasesAPI (returns both JSON + file path)
      const response = await axios.get(`http://localhost:8000/api/compare-test-cases/?file_url=${fileUrl}`);
      const { comparison_results, comparison_results_file } = response.data;

      if (comparison_results) {
        setComparisonResults(comparison_results);  // Store JSON directly
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
    if (!fileUrl) return;  // Prevent unnecessary API calls
    compareTestCases();
  }, [fileUrl]);

  return (
    <div>
      <h3>Test Case Comparison Results</h3>

      {loading && <p>Loading comparison results...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {comparisonResults.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Transaction Type</th>
              <th>Test Case 1</th>
              <th>Test Case 2</th>
              <th>Differences</th>
            </tr>
          </thead>
          <tbody>
            {comparisonResults.map((result, index) => (
              <tr key={index}>
                <td>{result.Transaction_Type}</td>
                <td>{result.Test_Case_1}</td>
                <td>{result.Test_Case_2}</td>
                <td>{result.Differences}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        !loading && <p>No comparison results found.</p>
      )}
    </div>
  );
}

export default TestCaseComparisonPage;
