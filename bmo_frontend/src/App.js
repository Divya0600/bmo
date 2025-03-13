// src/App.js
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import FileUpload from './components/FileUpload';
import TestCasesPagination from './components/TestCasesPagination';
import AnalyseTransactionPage from './components/AnalyseTransactionPage';
import PreProcessingPage from "./components/PreProcessingPage";
import TestCaseComparisonPage from './components/TestCaseComparisonPage';
import Feedback from './components/Feedback';

function App() {
  const [fileUrl, setFileUrl] = useState('');

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            fileUrl ? (
              <TestCasesPagination fileUrl={fileUrl} />
            ) : (
              <FileUpload onUploadSuccess={setFileUrl} />
            )
          }
        />
        <Route path="/analyse-transaction" element={<AnalyseTransactionPage />} />
        <Route path="/preprocess-test-cases" element={<PreProcessingPage />} />
        <Route path="/compare-test-cases" element={<TestCaseComparisonPage />} />
        <Route path="/feedback" element={<Feedback />} />
      </Routes>
    </Router>
  );
}

export default App;
