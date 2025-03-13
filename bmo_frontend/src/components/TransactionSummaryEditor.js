import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const TransactionSummaryEditor = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Get parameters from URL - matching your existing app flow
  const metadataUrl = searchParams.get('metadata_url') || '';
  const processedFileUrl = searchParams.get('processed_file_url') || '';
  const dissectedFileUrl = searchParams.get('file_url') || '';
  
  const [mapped, setMapped] = useState([]);
  const [unmapped, setUnmapped] = useState([]);
  const [baselined, setBaselined] = useState([]);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [updatedCsvUrl, setUpdatedCsvUrl] = useState('');
  const [summaryFileUrl, setSummaryFileUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Fetch summary data from your existing API
  const fetchSummary = async () => {
    if (!metadataUrl || !processedFileUrl) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const url = new URL('http://localhost:8000/api/get-transaction-summary/');
      url.searchParams.append('metadata_url', metadataUrl);
      url.searchParams.append('processed_file_url', processedFileUrl);

      const response = await fetch(url);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch transaction summary');
      }

      setMapped(data.mapped || []);
      setUnmapped(data.unmapped || []);
      setBaselined(data.baselined || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
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

  const saveUpdatedSummary = async () => {
    setIsSaving(true);
    setMessage('');
    setError('');
    
    try {
      // This matches your existing API endpoint
      const payload = {
        csv_file_url: dissectedFileUrl,
        metadata_url: metadataUrl,
        synonyms: [...mapped, ...unmapped].map(({ transaction, target }) => ({
          source_transaction: transaction,
          target_transaction: target || transaction,
        })),
      };

      const response = await fetch('http://localhost:8000/api/update-transaction-summary/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to update summary');
      }

      setMessage(data.message || 'Summary updated successfully');
      setUpdatedCsvUrl(data.updated_csv || '');
      setSummaryFileUrl(data.processed_file_url || '');
      
      // Refresh the summary data
      fetchSummary();
    } catch (err) {
      setError('Error updating transaction mappings: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleContinue = () => {
    // Navigate to the next step - matches your existing flow
    navigate('/preprocess-test-cases');
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Transaction Summary Editor</h1>
        <p className="text-gray-600 mt-1">
          Map detected transactions to standardized transaction types.
        </p>
      </div>
      
      {error && (
        <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      {message && (
        <div className="mb-6 bg-green-50 border-l-4 border-green-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-700">{message}</p>
            </div>
          </div>
        </div>
      )}
      
      {isLoading ? (
        <div className="flex justify-center py-12">
          <svg className="animate-spin h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      ) : (
        <>
          {/* Mapped Transactions Section */}
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <div className="flex items-center mb-4">
              <h2 className="text-lg font-medium text-gray-900">Mapped Transactions</h2>
              <span className="ml-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                {mapped.length}
              </span>
            </div>
            
            {mapped.length > 0 ? (
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Transaction
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Count
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Map To
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {mapped.map((item, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {item.transaction}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <select
                            value={item.target || item.transaction}
                            onChange={(e) => handleChange(index, e.target.value, 'mapped')}
                            className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
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
              </div>
            ) : (
              <div className="text-center py-6 text-gray-500 bg-gray-50 border border-gray-200 rounded-lg">
                No mapped transactions available.
              </div>
            )}
          </div>
          
          {/* Unmapped Transactions Section */}
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <div className="flex items-center mb-4">
              <h2 className="text-lg font-medium text-gray-900">Unmapped Transactions</h2>
              <span className="ml-2 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                {unmapped.length}
              </span>
            </div>
            
            {unmapped.length > 0 ? (
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Transaction
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Count
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Map To
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {unmapped.map((item, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {item.transaction}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {item.count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <select
                            value={item.target || ""}
                            onChange={(e) => handleChange(index, e.target.value, 'unmapped')}
                            className="mt-1 block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
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
              </div>
            ) : (
              <div className="text-center py-6 text-gray-500 bg-gray-50 border border-gray-200 rounded-lg">
                No unmapped transactions available.
              </div>
            )}
          </div>
          
          {/* Action Buttons */}
          <div className="flex justify-between">
            <button
              onClick={saveUpdatedSummary}
              disabled={isSaving}
              className={`inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${
                isSaving ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
              }`}
            >
              {isSaving ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Saving...
                </>
              ) : (
                'Save Updated Summary'
              )}
            </button>
            
            <button
              onClick={handleContinue}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Continue
              <svg className="ml-2 -mr-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          
          {/* Download Links */}
          {(updatedCsvUrl || summaryFileUrl) && (
            <div className="mt-6 bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Download Files</h3>
              <div className="flex flex-wrap gap-4">
                {updatedCsvUrl && (
                  <a
                    href={`http://localhost:8000/download/?file_url=${encodeURIComponent(updatedCsvUrl)}`}
                    download
                    className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <svg className="mr-2 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    Download Updated CSV
                  </a>
                )}
                
                {summaryFileUrl && (
                  <a
                    href={`http://localhost:8000/download/?file_url=${encodeURIComponent(summaryFileUrl)}`}
                    download
                    className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <svg className="mr-2 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    Download Summary File
                  </a>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default TransactionSummaryEditor;