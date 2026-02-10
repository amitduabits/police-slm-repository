import { useState } from 'react';
import { chargesheetAPI } from '../lib/api';
import { AlertCircle, FileCheck, Loader2 } from 'lucide-react';

export default function ChargesheetPage() {
  const [chargesheetText, setChargesheetText] = useState('');
  const [caseNumber, setCaseNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setResult(null);

    try {
      const response = await chargesheetAPI.review({
        chargesheet_text: chargesheetText,
        case_number: caseNumber || undefined,
        top_k: 5,
      });

      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to review chargesheet');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Chargesheet Review</h1>
        <p className="text-gray-600 mt-2">
          Review chargesheet completeness against successful similar cases
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Chargesheet Text
            </label>
            <textarea
              value={chargesheetText}
              onChange={(e) => setChargesheetText(e.target.value)}
              required
              rows={8}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1B3A5C] focus:border-transparent outline-none resize-none"
              placeholder="Paste chargesheet text here..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Case Number (Optional)
            </label>
            <input
              type="text"
              value={caseNumber}
              onChange={(e) => setCaseNumber(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1B3A5C] focus:border-transparent outline-none"
              placeholder="e.g., CR-123/2024"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#1B3A5C] text-white py-3 rounded-lg font-medium hover:bg-[#0F2338] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Reviewing...
              </>
            ) : (
              <>
                <FileCheck className="w-5 h-5" />
                Review Chargesheet
              </>
            )}
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

      {result && (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Review Results</h2>
            <div className="text-right">
              <div className="text-3xl font-bold text-[#1B3A5C]">
                {result.completeness_score.toFixed(0)}
              </div>
              <div className="text-sm text-gray-600">Completeness Score</div>
            </div>
          </div>

          <div className="prose max-w-none">
            <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded-lg">
              {result.response}
            </pre>
          </div>

          {result.citations && result.citations.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                Reference Cases ({result.citations.length})
              </h3>
              <div className="space-y-2">
                {result.citations.map((citation: any, index: number) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <p className="font-medium text-gray-900">{citation.source}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
