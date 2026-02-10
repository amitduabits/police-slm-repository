import { useState } from 'react';
import { searchAPI } from '../lib/api';
import { Search, Loader2, AlertCircle } from 'lucide-react';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setResults(null);

    try {
      const response = await searchAPI.query({
        query,
        top_k: 10,
      });

      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Case Search</h1>
        <p className="text-gray-600 mt-2">
          Search through legal documents and court rulings
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1B3A5C] focus:border-transparent outline-none"
            placeholder="Search for cases, sections, or legal topics..."
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-[#1B3A5C] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#0F2338] transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Search className="w-5 h-5" />
            )}
            Search
          </button>
        </form>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-900">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {results && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">
              Search Results ({results.total_results})
            </h2>
            {results.processing_time_ms && (
              <span className="text-sm text-gray-500">
                {results.processing_time_ms}ms
              </span>
            )}
          </div>

          {results.results && results.results.length > 0 ? (
            <div className="space-y-4">
              {results.results.map((result: any, index: number) => (
                <div
                  key={index}
                  className="bg-white rounded-lg shadow p-6 border border-gray-200"
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-semibold text-lg text-gray-900">
                      {result.title}
                    </h3>
                    <span className="text-sm font-medium text-[#1B3A5C]">
                      {(result.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mb-3">{result.snippet}</p>
                  <div className="flex gap-4 text-xs text-gray-500">
                    <span>Type: {result.document_type}</span>
                    <span>Source: {result.source}</span>
                    {result.court && <span>Court: {result.court}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <p className="text-gray-600">No results found</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
