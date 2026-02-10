import { useState } from 'react';
import { searchAPI } from '../lib/api';
import { Search, Loader2, AlertCircle, FileText, Clock, Scale, Filter } from 'lucide-react';
import { cn, formatScore } from '../lib/utils';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setError('');
    setLoading(true);
    setResults(null);

    try {
      const response = await searchAPI.query({ query, top_k: 10 });
      setResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    'IPC 302 murder conviction precedent',
    'Dowry death evidence requirements',
    'Bail conditions under BNSS',
    'Cybercrime jurisdiction Supreme Court',
    'Section 498A cruelty case law',
    'POCSO Act conviction rate',
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-2xl font-display font-bold text-white">Case Search</h1>
        <p className="text-sm text-white/40 mt-0.5">
          Semantic search across 12,000+ Supreme Court judgments and legal documents
        </p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="animate-slide-up">
        <div className="glass rounded-2xl p-2 flex items-center gap-2">
          <div className="p-2.5 ml-1">
            <Search className="w-5 h-5 text-white/30" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
            className="flex-1 bg-transparent text-white placeholder-white/25 outline-none text-sm py-2"
            placeholder="Search cases, sections, legal topics, or paste a query…"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary flex items-center gap-2 py-2.5 px-5 text-sm"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              'Search'
            )}
          </button>
        </div>
      </form>

      {/* Suggestions (shown when no results) */}
      {!results && !loading && !error && (
        <div className="animate-fade-in">
          <p className="text-xs font-medium text-white/30 uppercase tracking-wider mb-3">
            Try searching for
          </p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => {
                  setQuery(s);
                }}
                className="px-3.5 py-2 rounded-xl bg-white/[0.03] border border-white/[0.05] text-xs text-white/45 hover:text-white/70 hover:bg-white/[0.06] transition-all"
              >
                {s}
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

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-16 gap-4 animate-fade-in">
          <div className="w-10 h-10 border-2 border-gold-500/30 border-t-gold-500 rounded-full animate-spin" />
          <p className="text-sm text-white/40">Searching across legal corpus…</p>
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <div className="space-y-4 animate-slide-up">
          {/* Results header */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-white/50">
              <span className="text-white font-semibold">{results.total_results || results.results?.length || 0}</span>{' '}
              results found
            </p>
            {results.processing_time_ms && (
              <div className="flex items-center gap-1.5 text-xs text-white/25">
                <Clock className="w-3 h-3" />
                {results.processing_time_ms}ms
              </div>
            )}
          </div>

          {/* Result cards */}
          {results.results && results.results.length > 0 ? (
            <div className="space-y-3">
              {results.results.map((result: any, index: number) => (
                <div
                  key={index}
                  className="glass rounded-2xl p-5 hover:border-white/10 transition-all duration-200 group"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
                        <Scale className="w-4 h-4 text-white/25" />
                      </div>
                      <h3 className="font-display font-semibold text-white/90 truncate group-hover:text-gold-300 transition-colors">
                        {result.title || `Result ${index + 1}`}
                      </h3>
                    </div>
                    <span className="badge-blue flex-shrink-0">
                      {formatScore(result.score)}
                    </span>
                  </div>

                  <p className="text-sm text-white/45 leading-relaxed mb-4 line-clamp-3">
                    {result.snippet || result.text}
                  </p>

                  <div className="flex flex-wrap items-center gap-3">
                    {result.document_type && (
                      <span className="flex items-center gap-1 text-[11px] text-white/25">
                        <FileText className="w-3 h-3" />
                        {result.document_type}
                      </span>
                    )}
                    {result.source && (
                      <span className="text-[11px] text-white/25">
                        Source: {result.source}
                      </span>
                    )}
                    {result.court && (
                      <span className="text-[11px] text-white/25">
                        Court: {result.court}
                      </span>
                    )}
                    {result.judgment_date && (
                      <span className="text-[11px] text-white/25">
                        Date: {result.judgment_date}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass rounded-2xl p-12 text-center">
              <Search className="w-8 h-8 text-white/15 mx-auto mb-3" />
              <p className="text-white/40 text-sm">No results found for this query</p>
              <p className="text-white/20 text-xs mt-1">Try different keywords or broader terms</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
