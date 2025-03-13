import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const FileUpload = ({ onUploadSuccess }) => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadStatus('error:Please select a file.');
      return;
    }
    
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      // This matches your existing API endpoint
      const response = await fetch('http://localhost:8000/api/upload/', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      
      if (response.ok) {
        setUploadStatus('success');
        
        // If onUploadSuccess is provided, call it, otherwise navigate
        if (onUploadSuccess) {
          onUploadSuccess(data.file_url);
        } else {
          // Wait a moment before navigating to ensure user sees success message
          setTimeout(() => {
            navigate(`/dissect-test-cases?file_url=${encodeURIComponent(data.file_url)}`);
          }, 1000);
        }
      } else {
        setUploadStatus(`error:${data.error}`);
      }
    } catch (error) {
      setUploadStatus(`error:${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Test Case File Upload</h1>
          <p className="text-gray-600">
            Upload your test case CSV file to begin analysis. The file should contain test case descriptions and steps.
          </p>
        </div>
        
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                The system will process your file to identify test cases, transaction types, and conditions.
              </p>
            </div>
          </div>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="border-2 border-dashed border-gray-300 rounded-lg px-6 py-10">
            <div className="text-center">
              <svg 
                className="mx-auto h-12 w-12 text-gray-400" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={1} 
                  d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" 
                />
              </svg>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">
                  Upload a file
                </label>
                <div className="mt-1 flex justify-center">
                  <label 
                    htmlFor="file-upload" 
                    className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none"
                  >
                    <span>Select file</span>
                    <input 
                      id="file-upload" 
                      name="file-upload" 
                      type="file" 
                      className="sr-only" 
                      onChange={handleFileChange} 
                      accept=".csv,.xlsx,.xls"
                    />
                  </label>
                  <p className="pl-1 text-gray-500">or drag and drop</p>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  CSV, Excel up to 10MB
                </p>
              </div>
              
              {file && (
                <div className="mt-4 text-sm text-gray-800 bg-gray-100 rounded-md py-2 px-3 inline-block">
                  Selected: <span className="font-medium">{file.name}</span> ({(file.size / 1024).toFixed(1)} KB)
                </div>
              )}
            </div>
          </div>
          
          <div className="mt-6">
            <button
              type="submit"
              disabled={!file || isUploading}
              className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                !file || isUploading 
                  ? 'bg-blue-300 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
              }`}
            >
              {isUploading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading...
                </>
              ) : (
                'Upload File'
              )}
            </button>
          </div>
        </form>
        
        {uploadStatus && (
          <div className={`mt-6 rounded-md p-4 ${
            uploadStatus === 'success' 
              ? 'bg-green-50 border border-green-100' 
              : uploadStatus.startsWith('error:') 
                ? 'bg-red-50 border border-red-100' 
                : 'bg-blue-50 border border-blue-100'
            }`}>
            <div className="flex">
              <div className="flex-shrink-0">
                {uploadStatus === 'success' ? (
                  <svg className="h-5 w-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                ) : uploadStatus.startsWith('error:') ? (
                  <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <h3 className={`text-sm font-medium ${
                  uploadStatus === 'success' 
                    ? 'text-green-800' 
                    : uploadStatus.startsWith('error:') 
                      ? 'text-red-800' 
                      : 'text-blue-800'
                  }`}>
                  {uploadStatus === 'success' 
                    ? 'Upload successful!' 
                    : uploadStatus.startsWith('error:') 
                      ? 'Error' 
                      : 'Information'}
                </h3>
                <div className={`mt-2 text-sm ${
                  uploadStatus === 'success' 
                    ? 'text-green-700' 
                    : uploadStatus.startsWith('error:') 
                      ? 'text-red-700' 
                      : 'text-blue-700'
                  }`}>
                  <p>
                    {uploadStatus === 'success' 
                      ? 'Your file has been uploaded successfully. You will be redirected to the analysis page shortly.' 
                      : uploadStatus.startsWith('error:') 
                        ? uploadStatus.substring(6) 
                        : uploadStatus}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;