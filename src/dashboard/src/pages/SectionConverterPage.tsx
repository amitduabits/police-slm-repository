import { useState } from 'react';
import { utilsAPI } from '../lib/api';
import {
  ArrowRightLeft,
  Loader2,
  AlertCircle,
  AlertTriangle,
  ChevronRight,
  Repeat,
} from 'lucide-react';
import { cn } from '../lib/utils';

const codePairs = [
  { from: 'IPC', to: 'BNS', label: 'IPC → BNS' },
  { from: 'BNS', to: 'IPC', label: 'BNS → IPC' },
  { from: 'CrPC', to: 'BNSS', label: 'CrPC → BNSS' },
  { from: 'BNSS', to: 'CrPC', label: 'BNSS → CrPC' },
  { from: 'IEA', to: 'BSA', label: 'IEA → BSA' },
  { from: 'BSA', to: 'IEA', label: 'BSA → IEA' },
];

const popularConversions = [
  { section: '302', from: 'IPC', to: 'BNS', label: 'IPC 302 (Murder)' },
  { section: '420', from: 'IPC', to: 'BNS', label: 'IPC 420 (Cheating)' },
  { section: '376', from: 'IPC', to: 'BNS', label: 'IPC 376 (Rape)' },
  { section: '304B', from: 'IPC', to: 'BNS', label: 'IPC 304B (Dowry Death)' },
  { section: '498A', from: 'IPC', to: 'BNS', label: 'IPC 498A (Cruelty)' },
  { section: '307', from: 'IPC', to: 'BNS', label: 'IPC 307 (Attempt Murder)' },
];

export default function SectionConverterPage() {
  const [section, setSection] = useState('');
  const [fromCode, setFromCode] = useState('IPC');
  const [toCode, setToCode] = useState('BNS');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleConvert = async (e?: React.FormEvent, overrideSection?: string, overrideFrom?: string, overrideTo?: string) => {
    e?.preventDefault();
    const sec = overrideSection || section;
    const from = overrideFrom || fromCode;
    const to = overrideTo || toCode;
    if (!sec.trim()) return;

    setError('');
    setLoading(true);
    setResult(null);

    try {
      const response = await utilsAPI.convertSection(sec, from, to);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Conversion failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSwap = () => {
    setFromCode(toCode);
    setToCode(fromCode);
    setResult(null);
  };

  const handleQuickConvert = (item: typeof popularConversions[0]) => {
    setSection(item.section);
    setFromCode(item.from);
    setToCode(item.to);
    handleConvert(undefined, item.section, item.from, item.to);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-2xl font-display font-bold text-white">Section Converter</h1>
        <p className="text-sm text-white/40 mt-0.5">
          Convert between IPC↔BNS, CrPC↔BNSS, and IEA↔BSA codes instantly
        </p>
      </div>

      {/* Converter Card */}
      <div className="glass rounded-2xl p-6 animate-slide-up">
        <form onSubmit={handleConvert} className="space-y-5">
          {/* From / Section / To row */}
          <div className="flex items-end gap-3">
            {/* From */}
            <div className="flex-1">
              <label className="block text-xs font-medium text-white/50 uppercase tracking-wider mb-2">
                From
              </label>
              <select
                value={fromCode}
                onChange={(e) => { setFromCode(e.target.value); setResult(null); }}
                className="input-dark"
              >
                {['IPC', 'BNS', 'CrPC', 'BNSS', 'IEA', 'BSA'].map((c) => (
                  <option key={c} value={c} className="bg-surface-2">{c}</option>
                ))}
              </select>
            </div>

            {/* Swap button */}
            <button
              type="button"
              onClick={handleSwap}
              className="p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/10 transition-all mb-0.5"
              title="Swap codes"
            >
              <Repeat className="w-4 h-4 text-white/40" />
            </button>

            {/* To */}
            <div className="flex-1">
              <label className="block text-xs font-medium text-white/50 uppercase tracking-wider mb-2">
                To
              </label>
              <select
                value={toCode}
                onChange={(e) => { setToCode(e.target.value); setResult(null); }}
                className="input-dark"
              >
                {['IPC', 'BNS', 'CrPC', 'BNSS', 'IEA', 'BSA'].map((c) => (
                  <option key={c} value={c} className="bg-surface-2">{c}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Section input */}
          <div>
            <label className="block text-xs font-medium text-white/50 uppercase tracking-wider mb-2">
              Section Number
            </label>
            <input
              type="text"
              value={section}
              onChange={(e) => { setSection(e.target.value); setResult(null); }}
              required
              className="input-dark text-center text-lg font-mono font-semibold tracking-wider"
              placeholder="e.g. 302"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !section.trim()}
            className="btn-primary w-full flex items-center justify-center gap-2 py-3.5"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Converting…
              </>
            ) : (
              <>
                <ArrowRightLeft className="w-4 h-4" />
                Convert Section
              </>
            )}
          </button>
        </form>
      </div>

      {/* Popular conversions */}
      {!result && !loading && (
        <div className="animate-fade-in">
          <p className="text-xs font-medium text-white/30 uppercase tracking-wider mb-3">
            Popular Conversions
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {popularConversions.map((item) => (
              <button
                key={item.label}
                onClick={() => handleQuickConvert(item)}
                className="px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.05] text-sm text-white/45 hover:text-white/70 hover:bg-white/[0.06] transition-all text-left"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-red-500/10 border border-red-500/15 animate-fade-in">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && result.mapping && (
        <div className="glass rounded-2xl p-8 animate-slide-up">
          <h2 className="text-lg font-display font-semibold text-white/80 mb-6 text-center">
            Conversion Result
          </h2>

          {/* Visual conversion display */}
          <div className="flex items-center justify-center gap-6 mb-6">
            {/* Old section */}
            <div className="text-center flex-1">
              <div className="inline-block px-6 py-4 rounded-2xl bg-white/5 border border-white/10">
                <p className="text-xs text-white/30 uppercase tracking-wider mb-1">
                  {result.mapping.old_code}
                </p>
                <p className="text-3xl font-display font-bold text-white">
                  §{result.mapping.old_section}
                </p>
                {result.mapping.old_title && (
                  <p className="text-xs text-white/40 mt-2 max-w-[180px] leading-relaxed">
                    {result.mapping.old_title}
                  </p>
                )}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex-shrink-0">
              <div className="w-12 h-12 rounded-full gradient-gold flex items-center justify-center shadow-lg shadow-gold-500/20">
                <ChevronRight className="w-5 h-5 text-surface-0" />
              </div>
            </div>

            {/* New section */}
            <div className="text-center flex-1">
              <div className="inline-block px-6 py-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/15 glow-blue">
                <p className="text-xs text-emerald-400/60 uppercase tracking-wider mb-1">
                  {result.mapping.new_code}
                </p>
                <p className="text-3xl font-display font-bold text-emerald-400">
                  §{result.mapping.new_section || 'N/A'}
                </p>
                {result.mapping.new_title && (
                  <p className="text-xs text-emerald-400/40 mt-2 max-w-[180px] leading-relaxed">
                    {result.mapping.new_title}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Description */}
          {result.mapping.description && (
            <div className="px-5 py-4 rounded-xl bg-blue-500/5 border border-blue-500/10 mb-4">
              <p className="text-sm text-blue-300/70 leading-relaxed">
                {result.mapping.description}
              </p>
            </div>
          )}

          {/* Decriminalized warning */}
          {result.mapping.is_decriminalized && (
            <div className="flex items-center gap-3 px-5 py-4 rounded-xl bg-gold-500/10 border border-gold-500/15">
              <AlertTriangle className="w-5 h-5 text-gold-400 flex-shrink-0" />
              <p className="text-sm text-gold-300">
                This section has been <strong>decriminalized</strong> in the new code
              </p>
            </div>
          )}
        </div>
      )}

      {/* No mapping found */}
      {result && !result.mapping && (
        <div className="glass rounded-2xl p-8 text-center animate-fade-in">
          <AlertCircle className="w-8 h-8 text-white/15 mx-auto mb-3" />
          <p className="text-white/50 text-sm">{result.message || 'No mapping found'}</p>
        </div>
      )}
    </div>
  );
}
