import { useState } from 'react';
import { utilsAPI } from '../lib/api';
import { ArrowRightLeft, Loader2, AlertCircle } from 'lucide-react';

export default function SectionConverterPage() {
  const [section, setSection] = useState('');
  const [fromCode, setFromCode] = useState('IPC');
  const [toCode, setToCode] = useState('BNS');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const codes = ['IPC', 'BNS', 'CrPC', 'BNSS', 'IEA', 'BSA'];

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setResult(null);

    try {
      const response = await utilsAPI.convertSection(section, fromCode, toCode);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Conversion failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Section Converter</h1>
        <p className="text-gray-600 mt-2">
          Convert sections between IPC/BNS, CrPC/BNSS, and IEA/BSA
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <form onSubmit={handleConvert} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From Code
              </label>
              <select
                value={fromCode}
                onChange={(e) => setFromCode(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1B3A5C] focus:border-transparent outline-none"
              >
                {codes.map((code) => (
                  <option key={code} value={code}>
                    {code}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Section Number
              </label>
              <input
                type="text"
                value={section}
                onChange={(e) => setSection(e.target.value)}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1B3A5C] focus:border-transparent outline-none"
                placeholder="e.g., 302"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                To Code
              </label>
              <select
                value={toCode}
                onChange={(e) => setToCode(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#1B3A5C] focus:border-transparent outline-none"
              >
                {codes.map((code) => (
                  <option key={code} value={code}>
                    {code}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#1B3A5C] text-white py-3 rounded-lg font-medium hover:bg-[#0F2338] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Converting...
              </>
            ) : (
              <>
                <ArrowRightLeft className="w-5 h-5" />
                Convert Section
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
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Conversion Result</h2>

          {result.mapping ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-6 p-6 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="text-sm text-gray-600 mb-1">{result.mapping.old_code}</div>
                  <div className="text-2xl font-bold text-[#1B3A5C]">
                    Section {result.mapping.old_section}
                  </div>
                  {result.mapping.old_title && (
                    <div className="text-sm text-gray-600 mt-2 max-w-xs">
                      {result.mapping.old_title}
                    </div>
                  )}
                </div>

                <ArrowRightLeft className="w-8 h-8 text-gray-400" />

                <div className="text-center">
                  <div className="text-sm text-gray-600 mb-1">{result.mapping.new_code}</div>
                  <div className="text-2xl font-bold text-green-600">
                    Section {result.mapping.new_section || 'N/A'}
                  </div>
                  {result.mapping.new_title && (
                    <div className="text-sm text-gray-600 mt-2 max-w-xs">
                      {result.mapping.new_title}
                    </div>
                  )}
                </div>
              </div>

              {result.mapping.description && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-700">{result.mapping.description}</p>
                </div>
              )}

              {result.mapping.is_decriminalized && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800 font-medium">
                    ⚠️ This section has been decriminalized in the new code
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-600">
              {result.message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
