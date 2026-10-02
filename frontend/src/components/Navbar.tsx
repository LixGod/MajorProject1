import React from 'react';
import { Activity, MapPin, Sliders, BarChart3, Image as ImageIcon, AlertTriangle } from 'lucide-react';

interface NavbarProps {
  activeTab: 'map' | 'detail' | 'override' | 'analytics' | 'image_upload';
  setActiveTab: (tab: 'map' | 'detail' | 'override' | 'analytics' | 'image_upload') => void;
  isConnected: boolean;
  activeAlertsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  isConnected,
  activeAlertsCount
}) => {
  return (
    <header className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-lg">
      <div className="flex items-center space-x-4">
        <div className="bg-gradient-to-tr from-cyan-500 to-blue-600 p-2.5 rounded-xl shadow-md shadow-cyan-500/20">
          <Activity className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-100 tracking-wide flex items-center gap-2">
            MUMBAI SMART TRAFFIC CONTROL
            <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono">
              MAX-PRESSURE V1.0
            </span>
          </h1>
          <p className="text-xs text-slate-400">Adaptive Multi-Junction Real-Time Autonomous Signal Control</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center space-x-1 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
        <button
          onClick={() => setActiveTab('map')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'map'
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <MapPin className="w-4 h-4" />
          <span>Junction Map</span>
        </button>

        <button
          onClick={() => setActiveTab('detail')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'detail'
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Live Monitor</span>
        </button>

        <button
          onClick={() => setActiveTab('image_upload')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'image_upload'
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <ImageIcon className="w-4 h-4" />
          <span>Upload & Test Image</span>
        </button>

        <button
          onClick={() => setActiveTab('override')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'override'
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>Manual Override</span>
        </button>

        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'analytics'
              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>Paper Analytics</span>
        </button>
      </nav>

      {/* System Status Indicators */}
      <div className="flex items-center space-x-4">
        {activeAlertsCount > 0 && (
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-xs font-semibold animate-pulse">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>{activeAlertsCount} ALERT{activeAlertsCount > 1 ? 'S' : ''}</span>
          </div>
        )}

        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-medium">
          <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-ping' : 'bg-rose-500'}`} />
          <span className={isConnected ? 'text-emerald-400' : 'text-rose-400'}>
            {isConnected ? 'LIVE WEBSOCKET' : 'DISCONNECTED'}
          </span>
        </div>
      </div>
    </header>
  );
};
