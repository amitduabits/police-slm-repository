import { useState } from 'react';
import { sopAPI } from '../lib/api';
import { AlertCircle, FileText, Loader2 } from 'lucide-react';

export default function SOPPage() {
  const [firDetails, setFirDetails] = useState('');
  const [caseCategory, setCaseCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setResult(null);

    try {
      const response = await sopAPI.suggest({
        fir_details: firDetails,
        case_category: caseCategory || undefined,
        top_k: 5,
      });

      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate investigation guidance');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">SOP Assistant</h1>
        <p className="text-gray-600 mt-2">
          Get investigation guidance based on similar past cases
        </p>
      </div>

      {/* Input Form */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              FIR Details
            </label>
            <textarea
              value={firDetails}
              onChange={(e) => setFirDetails(e.target.value)}
              required
              rows={6}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1B3A5C] focus:border-transparent outline-none resize-none"
              placeholder="Enter FIR details, case description, or investigation scenario..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Case Category (Optional)
            </label>
            <input
              type="text"
              value={caseCategory}
              onChange={(e) => setCaseCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1B3A5C] focus:border-transparent outline-none"
              placeholder="e.g., theft, murder, assault"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#1B3A5C] text-white py-3 rounded-lg font-medium hover:bg-[#0F2338] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating Guidance...
              </>
            ) : (
              <>
                <FileText className="w-5 h-5" />
                Get Investigation Guidance
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-900">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200 space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Investigation Guidance
            </h2>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-lg">
                {result.response}
              </pre>
            </div>
          </div>

          {/* Citations */}
          {result.citations && result.citations.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Sources ({result.citations.length})
              </h3>
              <div className="space-y-2">
                {result.citations.map((citation: any, index: number) => (
                  <div
                    key={index}
                    className="bg-gray-50 p-4 rounded-lg border border-gray-200"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900">{citation.source}</p>
                        {citation.court && (
                          <p className="text-sm text-gray-600 mt-1">{citation.court}</p>
                        )}
                      </div>
                      <span className="text-sm font-medium text-[#1B3A5C]">
                        Score: {(citation.score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="text-xs text-gray-500 pt-4 border-t">
            Retrieved {result.num_results} relevant documents
            {result.processing_time_ms && ` in ${result.processing_time_ms}ms`}
          </div>
        </div>
      )}
    </div>
  );
}
