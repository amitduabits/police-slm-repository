import { useState, useRef, useEffect } from 'react';
import { sopAPI } from '../lib/api';
import {
  Send,
  Loader2,
  AlertCircle,
  FileText,
  BookOpen,
  Sparkles,
  ChevronDown,
} from 'lucide-react';
import { cn, formatScore } from '../lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
  timestamp: Date;
  loading?: boolean;
}

export default function SOPPage() {
  const [firDetails, setFirDetails] = useState('');
  const [caseCategory, setCaseCategory] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firDetails.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: firDetails,
      timestamp: new Date(),
    };

    const loadingMsg: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      loading: true,
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    const query = firDetails;
    setFirDetails('');
    setLoading(true);

    try {
      const response = await sopAPI.suggest({
        fir_details: query,
        case_category: caseCategory || undefined,
        top_k: 5,
      });

      setMessages((prev) =>
        prev.map((m) =>
          m.loading
            ? {
                ...m,
                content: response.data.response,
                citations: response.data.citations,
                loading: false,
              }
            : m
        )
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.loading
            ? {
                ...m,
                content: `Error: ${err.response?.data?.detail || 'Failed to generate guidance'}`,
                loading: false,
              }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div>
          <h1 className="text-2xl font-display font-bold text-white">SOP Assistant</h1>
          <p className="text-sm text-white/40 mt-0.5">
            AI investigation guidance powered by 12,000+ court rulings
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="btn-ghost flex items-center gap-2 text-sm"
        >
          Filters
          <ChevronDown
            className={cn('w-4 h-4 transition-transform', showFilters && 'rotate-180')}
          />
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="glass rounded-xl p-4 mb-4 flex-shrink-0 animate-slide-up">
          <label className="block text-xs font-medium text-white/50 uppercase tracking-wider mb-2">
            Case Category
          </label>
          <input
            type="text"
            value={caseCategory}
            onChange={(e) => setCaseCategory(e.target.value)}
            className="input-dark"
            placeholder="e.g., murder, theft, assault, cybercrime…"
          />
        </div>
      )}

      {/* Chat area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pb-4 min-h-0">
        {/* Empty state */}
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/15 mb-5">
                <Sparkles className="w-7 h-7 text-blue-400" />
              </div>
              <h3 className="text-lg font-display font-semibold text-white/80 mb-2">
                Describe your case
              </h3>
              <p className="text-sm text-white/35 leading-relaxed mb-6">
                Paste FIR details or describe your investigation scenario. The AI will
                analyze similar cases and provide step-by-step guidance.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {['Murder under IPC 302', 'Dowry death investigation', 'Cyber fraud case', 'Drug trafficking'].map(
                  (ex) => (
                    <button
                      key={ex}
                      onClick={() => setFirDetails(ex)}
                      className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-xs text-white/50 hover:text-white/70 hover:bg-white/[0.07] transition-colors"
                    >
                      {ex}
                    </button>
                  )
                )}
              </div>
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              'flex gap-3 animate-fade-in',
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/15 flex items-center justify-center flex-shrink-0 mt-1">
                <Sparkles className="w-4 h-4 text-blue-400" />
              </div>
            )}

            <div
              className={cn(
                'max-w-[85%] rounded-2xl',
                msg.role === 'user'
                  ? 'bg-gold-500/10 border border-gold-500/15 px-5 py-3.5'
                  : 'glass px-5 py-4'
              )}
            >
              {msg.loading ? (
                <div className="flex items-center gap-2 text-white/40">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Analyzing case and generating guidance…</span>
                </div>
              ) : (
                <>
                  <div
                    className={cn(
                      'text-sm leading-relaxed whitespace-pre-wrap',
                      msg.role === 'user' ? 'text-gold-200' : 'text-white/70'
                    )}
                  >
                    {msg.content}
                  </div>

                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-white/5 space-y-2">
                      <p className="text-xs font-medium text-white/30 uppercase tracking-wider flex items-center gap-1.5">
                        <BookOpen className="w-3 h-3" />
                        Sources ({msg.citations.length})
                      </p>
                      {msg.citations.map((c: any, i: number) => (
                        <div
                          key={i}
                          className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/[0.03]"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <FileText className="w-3.5 h-3.5 text-white/20 flex-shrink-0" />
                            <span className="text-xs text-white/50 truncate">
                              {c.source}
                              {c.court && ` · ${c.court}`}
                            </span>
                          </div>
                          <span className="badge-blue text-[10px] flex-shrink-0">
                            {formatScore(c.score)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-gold-500/10 border border-gold-500/15 flex items-center justify-center flex-shrink-0 mt-1">
                <FileText className="w-4 h-4 text-gold-400" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex-shrink-0 pt-2">
        <div className="glass rounded-2xl p-3 flex items-end gap-3">
          <textarea
            ref={inputRef}
            value={firDetails}
            onChange={(e) => setFirDetails(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            className="flex-1 bg-transparent text-sm text-white placeholder-white/25 outline-none resize-none py-1.5 px-2"
            placeholder="Describe FIR details or investigation scenario…"
          />
          <button
            type="submit"
            disabled={loading || !firDetails.trim()}
            className="p-3 rounded-xl gradient-gold text-surface-0 hover:shadow-lg hover:shadow-gold-500/20 disabled:opacity-30 disabled:shadow-none transition-all flex-shrink-0"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <p className="text-center text-[10px] text-white/15 mt-2">
          AI guidance is advisory only · Always verify with legal experts
        </p>
      </form>
    </div>
  );
}
