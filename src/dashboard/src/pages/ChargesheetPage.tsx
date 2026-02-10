import { useState } from 'react';
import { chargesheetAPI } from '../lib/api';
import {
  AlertCircle,
  FileCheck,
  Loader2,
  Upload,
  CheckCircle2,
  XCircle,
  BookOpen,
} from 'lucide-react';
import { cn } from '../lib/utils';

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

  const getScoreColor = (score: number) => {
    if (score >= 80) return { ring: 'text-emerald-400', bg: 'bg-emerald-500', label: 'Strong' };
    if (score >= 60) return { ring: 'text-gold-400', bg: 'bg-gold-500', label: 'Fair' };
    return { ring: 'text-red-400', bg: 'bg-red-500', label: 'Needs Work' };
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-2xl font-display font-bold text-white">
          Chargesheet Review
        </h1>
        <p className="text-sm text-white/40 mt-0.5">
          AI-powered completeness analysis against successful precedent cases
        </p>
      </div>

      {/* Input form */}
      <div className="glass rounded-2xl p-6 animate-slide-up">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-medium text-white/50 uppercase tracking-wider mb-2">
              Chargesheet Text
            </label>
            <textarea
              value={chargesheetText}
              onChange={(e) => setChargesheetText(e.target.value)}
              required
              rows={10}
              className="input-dark font-mono text-sm resize-none"
              placeholder="Paste the full chargesheet text here for AI analysis…"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-white/50 uppercase tracking-wider mb-2">
                Case Number
              </label>
              <input
                type="text"
                value={caseNumber}
                onChange={(e) => setCaseNumber(e.target.value)}
                className="input-dark"
                placeholder="e.g., CR-445/2024"
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading || !chargesheetText.trim()}
                className="btn-primary w-full flex items-center justify-center gap-2 py-3"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing…
                  </>
                ) : (
                  <>
                    <FileCheck className="w-4 h-4" />
                    Review Chargesheet
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-red-500/10 border border-red-500/15 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6 animate-slide-up">
          {/* Score Card */}
          <div className="glass rounded-2xl p-8">
            <div className="flex flex-col sm:flex-row items-center gap-8">
              {/* Circular Score */}
              <div className="relative flex-shrink-0">
                <svg className="w-32 h-32 -rotate-90" viewBox="0 0 120 120">
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    fill="none"
                    stroke="rgba(255,255,255,0.05)"
                    strokeWidth="8"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${(result.completeness_score / 100) * 327} 327`}
                    className={cn(
                      'transition-all duration-1000',
                      getScoreColor(result.completeness_score).ring
                    )}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-display font-bold text-white">
                    {result.completeness_score.toFixed(0)}
                  </span>
                  <span className="text-xs text-white/40">/ 100</span>
                </div>
              </div>

              {/* Score details */}
              <div className="flex-1 text-center sm:text-left">
                <div className="flex items-center justify-center sm:justify-start gap-2 mb-2">
                  <h2 className="text-xl font-display font-bold text-white">
                    Completeness Score
                  </h2>
                  <span
                    className={cn(
                      'badge',
                      result.completeness_score >= 80
                        ? 'badge-green'
                        : result.completeness_score >= 60
                        ? 'badge-gold'
                        : 'badge-red'
                    )}
                  >
                    {getScoreColor(result.completeness_score).label}
                  </span>
                </div>
                <p className="text-sm text-white/40 leading-relaxed max-w-lg">
                  {result.completeness_score >= 80
                    ? 'The chargesheet appears well-prepared with strong coverage of required elements.'
                    : result.completeness_score >= 60
                    ? 'Some areas need attention. Review the detailed analysis below.'
                    : 'Significant gaps detected. Please address the issues identified below.'}
                </p>
              </div>
            </div>
          </div>

          {/* Detailed Analysis */}
          <div className="glass rounded-2xl p-6">
            <h3 className="text-lg font-display font-semibold text-white/80 mb-4">
              Detailed Analysis
            </h3>
            <div className="prose prose-invert max-w-none">
              <pre className="whitespace-pre-wrap text-sm text-white/60 bg-surface-2/50 p-5 rounded-xl border border-white/5 font-mono leading-relaxed">
                {result.response}
              </pre>
            </div>
          </div>

          {/* Reference Cases */}
          {result.citations && result.citations.length > 0 && (
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-display font-semibold text-white/80 mb-4 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-white/30" />
                Reference Cases ({result.citations.length})
              </h3>
              <div className="space-y-2">
                {result.citations.map((c: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.03] hover:bg-white/[0.04] transition-colors"
                  >
                    <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-xs text-white/30 font-mono">
                      {i + 1}
                    </div>
                    <span className="text-sm text-white/60 flex-1 truncate">
                      {c.source}
                    </span>
                    {c.score && (
                      <span className="badge-blue text-[10px]">
                        {(c.score * 100).toFixed(0)}%
                      </span>
                    )}
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
