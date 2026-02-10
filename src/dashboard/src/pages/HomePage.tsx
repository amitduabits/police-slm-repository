import { Link } from 'react-router-dom';
import { FileText, FileCheck, Search, Settings } from 'lucide-react';

const quickActions = [
  {
    title: 'SOP Assistant',
    description: 'Get investigation guidance based on similar cases',
    icon: FileText,
    path: '/sop',
    color: 'bg-blue-500',
  },
  {
    title: 'Chargesheet Review',
    description: 'Review chargesheet completeness and quality',
    icon: FileCheck,
    path: '/chargesheet',
    color: 'bg-green-500',
  },
  {
    title: 'Case Search',
    description: 'Search through case documents and rulings',
    icon: Search,
    path: '/search',
    color: 'bg-purple-500',
  },
  {
    title: 'Section Converter',
    description: 'Convert IPC to BNS sections',
    icon: Settings,
    path: '/tools/sections',
    color: 'bg-orange-500',
  },
];

export default function HomePage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Welcome to the Gujarat Police AI Investigation Support System
        </p>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.path}
                to={action.path}
                className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border border-gray-200"
              >
                <div className="flex items-start gap-4">
                  <div className={`${action.color} p-3 rounded-lg`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-gray-900 mb-1">
                      {action.title}
                    </h3>
                    <p className="text-gray-600 text-sm">
                      {action.description}
                    </p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* System Info */}
      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">System Information</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-[#1B3A5C]">1</div>
            <div className="text-sm text-gray-600 mt-1">Documents Embedded</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-[#1B3A5C]">43</div>
            <div className="text-sm text-gray-600 mt-1">Chunks Indexed</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">Online</div>
            <div className="text-sm text-gray-600 mt-1">API Status</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">Ready</div>
            <div className="text-sm text-gray-600 mt-1">RAG Pipeline</div>
          </div>
        </div>
      </div>
    </div>
  );
}
