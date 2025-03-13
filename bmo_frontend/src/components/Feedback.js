// import React, { useState } from "react";
// import axios from "axios";

// function Feedback() {
//   const [feedbackFile, setFeedbackFile] = useState(null);
//   const [uploadStatus, setUploadStatus] = useState(null);

//   // Handle file selection
//   const handleFileChange = (event) => {
//     setFeedbackFile(event.target.files[0]);
//   };

//   // Upload feedback file to the backend
//   const uploadFeedbackFile = async () => {
//     if (!feedbackFile) {
//       setUploadStatus("Please select a file first.");
//       return;
//     }

//     const formData = new FormData();
//     formData.append("feedback_file", feedbackFile);

//     try {
//       setUploadStatus("Uploading...");
//       await axios.post("http://localhost:8000/api/upload-feedback/", formData, {
//         headers: { "Content-Type": "multipart/form-data" },
//       });
//       setUploadStatus("Feedback file uploaded successfully.");
//     } catch (err) {
//       setUploadStatus("Failed to upload feedback file.");
//     }
//   };

//   return (
//     <div style={{ marginTop: "20px" }}>
//       <h4>Upload Feedback File</h4>
//       <input type="file" accept=".csv, .xlsx" onChange={handleFileChange} />
//       <button type="button" onClick={uploadFeedbackFile} style={{ marginLeft: "10px" }}>
//         Upload Feedback
//       </button>
//       {uploadStatus && <p>{uploadStatus}</p>}
//     </div>
//   );
// }

// export default Feedback;
import React, { useState } from "react";
import axios from "axios";

function Feedback() {
  const [feedbackFile, setFeedbackFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [feedbackResponse, setFeedbackResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null); // Save feedback status

  // Handle file selection
  const handleFileChange = (event) => {
    setFeedbackFile(event.target.files[0]);
  };

  // Upload feedback file and get response
  const uploadFeedbackFile = async () => {
    if (!feedbackFile) {
      setUploadStatus("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("feedback_file", feedbackFile);

    try {
      setUploadStatus("Uploading...");
      setLoading(true);

      const response = await axios.post("http://localhost:8000/api/upload-feedback/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("API Response:", response.data);

      if (response.data.feedback_json) {
        setFeedbackResponse(response.data.feedback_json);
        setUploadStatus("Feedback file uploaded successfully.");
      } else {
        setUploadStatus("No feedback data found in the uploaded file.");
      }
    } catch (err) {
      setUploadStatus("Failed to upload feedback file.");
    } finally {
      setLoading(false);
    }
  };

  // Handle table cell edit
  const handleInputChange = (rowIndex, columnKey, newValue) => {
    const updatedFeedback = [...feedbackResponse];
    updatedFeedback[rowIndex][columnKey] = newValue; // Update the specific cell
    setFeedbackResponse(updatedFeedback);
  };

  // Save updated feedback
  const saveFeedback = async () => {
    if (!feedbackResponse) {
      setSaveStatus("No data to save.");
      return;
    }

    try {
      setSaveStatus("Saving...");
      const response = await axios.post("http://localhost:8000/api/save-feedback/", {
        feedback_json: feedbackResponse,
      });

      setSaveStatus("Feedback saved successfully.");
      console.log("Save Response:", response.data);
    } catch (err) {
      setSaveStatus("Failed to save feedback.");
    }
  };

  return (
    <div style={{ marginTop: "20px" }}>
      <h4>Upload Feedback File</h4>
      <input type="file" accept=".csv, .xlsx" onChange={handleFileChange} />
      <button type="button" onClick={uploadFeedbackFile} style={{ marginLeft: "10px" }}>
        Upload Feedback
      </button>
      {uploadStatus && <p>{uploadStatus}</p>}
      
      {loading && <p>Loading feedback data...</p>}

      {/* Editable Table */}
      {feedbackResponse && feedbackResponse.length > 0 ? (
        <div style={{ marginTop: "20px", border: "1px solid #ddd", padding: "10px" }}>
          <h4>Feedback Response</h4>
          <table border="1" cellPadding="5" style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                {Object.keys(feedbackResponse[0]).map((key, index) => (
                  <th key={index}>{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {feedbackResponse.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {Object.entries(row).map(([columnKey, value], colIndex) => (
                    <td key={colIndex}>
                      <input
                        type="text"
                        value={value}
                        onChange={(e) => handleInputChange(rowIndex, columnKey, e.target.value)}
                        style={{ width: "100%" }}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          {/* Save Button */}
          <button type="button" onClick={saveFeedback} style={{ marginTop: "10px" }}>
            Save Feedback
          </button>
          {saveStatus && <p>{saveStatus}</p>}
        </div>
      ) : (
        !loading && uploadStatus && <p>No feedback data found.</p>
      )}
    </div>
  );
}

export default Feedback;
