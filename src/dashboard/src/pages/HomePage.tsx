import { Link } from 'react-router-dom';
import {
  FileText,
  FileCheck,
  Search,
  ArrowRightLeft,
  Database,
  Layers,
  Activity,
  Cpu,
  TrendingUp,
  ArrowUpRight,
  Scale,
  Gavel,
} from 'lucide-react';

const stats = [
  {
    label: 'Documents Indexed',
    value: '12,480',
    change: '+2,340',
    icon: Database,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/15',
  },
  {
    label: 'Chunks Embedded',
    value: '48,720',
    change: '+8,100',
    icon: Layers,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/15',
  },
  {
    label: 'API Status',
    value: 'Online',
    change: '99.9% uptime',
    icon: Activity,
    color: 'text-gold-400',
    bgColor: 'bg-gold-500/10',
    borderColor: 'border-gold-500/15',
  },
  {
    label: 'RAG Pipeline',
    value: 'Ready',
    change: 'All systems go',
    icon: Cpu,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/15',
  },
];

const quickActions = [
  {
    title: 'SOP Assistant',
    description: 'Get AI-powered investigation guidance based on similar past cases and court rulings',
    icon: FileText,
    path: '/sop',
    gradient: 'from-blue-600/20 to-blue-800/20',
    iconBg: 'bg-blue-500',
    tag: 'AI-Powered',
  },
  {
    title: 'Chargesheet Review',
    description: 'Automated completeness analysis against successful precedent cases',
    icon: FileCheck,
    path: '/chargesheet',
    gradient: 'from-emerald-600/20 to-emerald-800/20',
    iconBg: 'bg-emerald-500',
    tag: 'Quality Check',
  },
  {
    title: 'Case Search',
    description: 'Semantic search across 12,000+ Supreme Court judgments and legal documents',
    icon: Search,
    path: '/search',
    gradient: 'from-purple-600/20 to-purple-800/20',
    iconBg: 'bg-purple-500',
    tag: 'RAG Search',
  },
  {
    title: 'Section Converter',
    description: 'Instantly convert between IPC↔BNS, CrPC↔BNSS, and IEA↔BSA codes',
    icon: ArrowRightLeft,
    path: '/tools/sections',
    gradient: 'from-gold-600/20 to-gold-800/20',
    iconBg: 'bg-gold-500',
    tag: 'Utility',
  },
];

const recentCases = [
  { type: 'SOP Query', detail: 'Murder investigation — FIR #GJ-2024-1847', time: '2 hours ago', icon: Scale },
  { type: 'Chargesheet', detail: 'Review CR-445/2024 — Theft under BNS 305', time: '5 hours ago', icon: Gavel },
  { type: 'Search', detail: '"dowry death section 304B precedent"', time: '1 day ago', icon: Search },
  { type: 'Conversion', detail: 'IPC 302 → BNS 103 (Murder)', time: '1 day ago', icon: ArrowRightLeft },
];

export default function HomePage() {
  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-3xl font-display font-bold text-white mb-1">
          Command Center
        </h1>
        <p className="text-white/40">
          AI-powered investigation support — Gujarat Police
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-slide-up">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className={`glass rounded-2xl p-5 ${stat.borderColor} border hover:border-white/10 transition-colors`}
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`p-2.5 rounded-xl ${stat.bgColor}`}>
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
              </div>
              <div className="flex items-center gap-1 text-emerald-400">
                <TrendingUp className="w-3 h-3" />
                <span className="text-xs font-medium">{stat.change}</span>
              </div>
            </div>
            <div className="text-2xl font-display font-bold text-white mb-0.5">
              {stat.value}
            </div>
            <div className="text-xs text-white/40">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-display font-semibold text-white/80 mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {quickActions.map((action, i) => (
            <Link
              key={action.path}
              to={action.path}
              className="group glass rounded-2xl p-6 hover:border-white/10 transition-all duration-300 hover:shadow-xl hover:shadow-black/20 relative overflow-hidden"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              {/* Gradient background on hover */}
              <div
                className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
              />

              <div className="relative z-10 flex items-start gap-4">
                <div
                  className={`${action.iconBg} p-3 rounded-xl shadow-lg flex-shrink-0 group-hover:scale-110 transition-transform duration-300`}
                >
                  <action.icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <h3 className="font-display font-semibold text-white group-hover:text-white transition-colors">
                      {action.title}
                    </h3>
                    <span className="badge-gold text-[10px]">{action.tag}</span>
                  </div>
                  <p className="text-sm text-white/40 group-hover:text-white/60 transition-colors leading-relaxed">
                    {action.description}
                  </p>
                </div>
                <ArrowUpRight className="w-4 h-4 text-white/20 group-hover:text-white/60 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all flex-shrink-0 mt-1" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="glass rounded-2xl p-6">
        <h2 className="text-lg font-display font-semibold text-white/80 mb-5">
          Recent Activity
        </h2>
        <div className="space-y-1">
          {recentCases.map((item, i) => (
            <div
              key={i}
              className="flex items-center gap-4 px-4 py-3.5 rounded-xl hover:bg-white/[0.02] transition-colors"
            >
              <div className="p-2 rounded-lg bg-white/5">
                <item.icon className="w-4 h-4 text-white/30" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gold-500/70 uppercase tracking-wider">
                    {item.type}
                  </span>
                </div>
                <p className="text-sm text-white/60 truncate mt-0.5">{item.detail}</p>
              </div>
              <span className="text-xs text-white/25 flex-shrink-0">{item.time}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Data Source Banner */}
      <div className="glass-gold rounded-2xl p-6 flex items-center gap-4">
        <div className="p-3 rounded-xl bg-gold-500/10">
          <Database className="w-5 h-5 text-gold-400" />
        </div>
        <div className="flex-1">
          <h3 className="font-display font-semibold text-gold-300 text-sm">
            Kaggle SC Judgments Dataset Integrated
          </h3>
          <p className="text-xs text-gold-500/50 mt-0.5">
            12,480 Supreme Court judgments (1950–2024) powering the RAG pipeline · 98% coverage
          </p>
        </div>
        <span className="badge-green">Active</span>
      </div>
    </div>
  );
}
