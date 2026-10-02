import React from 'react';
import { JunctionTelemetry } from '../types';
import { Clock, ShieldAlert, AlertTriangle, Car, Gauge, Cpu, CheckCircle2, Shield } from 'lucide-react';

interface JunctionDetailViewProps {
  telemetry?: JunctionTelemetry;
  onOpenOverride: () => void;
}

export const JunctionDetailView: React.FC<JunctionDetailViewProps> = ({
  telemetry,
  onOpenOverride
}) => {
  if (!telemetry) {
    return (
      <div className="flex items-center justify-center h-96 glass-panel text-slate-400">
        Select a junction to monitor live control telemetry.
      </div>
    );
  }

  const {
    junction_name,
    current_phase,
    signal_state,
    remaining_green_sec,
    total_green_sec,
    approach_states,
    alerts,
    location
  } = telemetry;

  const isAllRed = signal_state === 'ALL_RED_CLEARANCE';

  return (
    <div className="space-y-6">
      {/* Alert Banners */}
      {alerts.preemption_active && (
        <div className="bg-rose-950/90 border border-rose-600 text-rose-200 p-4 rounded-xl shadow-lg flex items-center justify-between animate-pulse">
          <div className="flex items-center space-x-3">
            <ShieldAlert className="w-7 h-7 text-rose-400" />
            <div>
              <h4 className="font-bold text-sm text-rose-100">EMERGENCY PREEMPTION ACTIVE</h4>
              <p className="text-xs text-rose-300">
                Ambulance detected on approach <span className="font-mono font-bold">{alerts.preemption_approach}</span>. Signal held with mandatory All-Red safety clearance.
              </p>
            </div>
          </div>
          <span className="badge badge-red glow-rose">CRITICAL OVERRIDE</span>
        </div>
      )}

      {alerts.gridlock_warning && (
        <div className="bg-amber-950/90 border border-amber-600 text-amber-200 p-4 rounded-xl shadow-lg flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-7 h-7 text-amber-400" />
            <div>
              <h4 className="font-bold text-sm text-amber-100">GRIDLOCK WATCHDOG TRIGGERED</h4>
              <p className="text-xs text-amber-300">
                Downstream queue near capacity. Cross-junction pressure penalties applied to upstream feeds.
              </p>
            </div>
          </div>
          <span className="badge badge-amber glow-amber">GRIDLOCK ALERT</span>
        </div>
      )}

      {/* Top Header Card */}
      <div className="glass-panel p-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <h2 className="text-2xl font-extrabold text-white tracking-wide">{junction_name}</h2>
            <span className={`badge ${isAllRed ? 'badge-amber glow-amber' : 'badge-green glow-emerald'}`}>
              {signal_state}
            </span>
          </div>
          <p className="text-xs text-slate-400 flex items-center gap-1.5">
            <span>📍 {location?.address || 'Mumbai, MH'}</span>
            <span className="text-slate-600">•</span>
            <span className="text-cyan-400 font-mono">Geocoded via TomTom API</span>
          </p>
        </div>

        {/* Phase Timer Circle & Action */}
        <div className="flex items-center space-x-6">
          <div className="text-center">
            <div className="relative inline-flex items-center justify-center">
              <svg className="w-24 h-24 transform -rotate-90">
                <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="6" className="text-slate-800" fill="transparent" />
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="currentColor"
                  strokeWidth="6"
                  className={isAllRed ? 'text-amber-400' : 'text-emerald-400'}
                  fill="transparent"
                  strokeDasharray={2 * Math.PI * 40}
                  strokeDashoffset={2 * Math.PI * 40 * (1 - remaining_green_sec / Math.max(1, total_green_sec))}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className={`text-2xl font-black font-mono ${isAllRed ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {remaining_green_sec.toFixed(0)}s
                </span>
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">
                  {isAllRed ? 'ALL-RED' : 'GREEN'}
                </span>
              </div>
            </div>
          </div>

          <div>
            <button
              onClick={onOpenOverride}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg hover:shadow-rose-500/20 transition-all flex items-center space-x-2"
            >
              <Shield className="w-4 h-4" />
              <span>Manual Signal Override</span>
            </button>
          </div>
        </div>
      </div>

      {/* Grid: Camera Streams + Approach Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(approach_states).map(([appId, st]) => {
          const isCurrentActive = current_phase.movements.some((m) => m.startsWith(appId));

          return (
            <div
              key={appId}
              className={`glass-panel p-5 transition-all ${
                isCurrentActive
                  ? 'border-emerald-500/50 bg-emerald-950/10'
                  : 'border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <span className={`w-3 h-3 rounded-full ${isCurrentActive ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                  <h3 className="text-base font-bold text-slate-100 uppercase tracking-wide">
                    APPROACH: {appId}
                  </h3>
                </div>

                <div className="flex items-center space-x-2">
                  <span className={`badge ${isCurrentActive ? 'badge-green' : 'badge-red'}`}>
                    {isCurrentActive ? 'SIGNAL GREEN' : 'SIGNAL RED'}
                  </span>
                  {!st.feed_healthy && (
                    <span className="badge badge-amber">CAM DROPOUT (DECAY HOLD)</span>
                  )}
                </div>
              </div>

              {/* Synthetic Detection Overlay Box */}
              <div className="relative w-full h-48 bg-slate-950 rounded-xl overflow-hidden border border-slate-800 mb-4 flex items-center justify-center">
                {/* Simulated ROI Polygon & Detection Bounding Boxes */}
                <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#06b6d4_1px,transparent_1px)] [background-size:16px_16px]" />

                {/* ROI Line */}
                <div className="absolute inset-x-4 bottom-8 border-b-2 border-dashed border-cyan-400 opacity-60 flex justify-between text-[10px] text-cyan-300 font-mono px-2">
                  <span>ROI STOP LINE</span>
                  <span>CONF: 94.2%</span>
                </div>

                {/* Detections Overlay */}
                <div className="absolute inset-0 p-4 flex flex-wrap gap-2 items-center justify-center">
                  {Array.from({ length: Math.min(st.raw_count, 6) }).map((_, idx) => (
                    <div
                      key={idx}
                      className="border-2 border-emerald-400 bg-emerald-500/20 rounded px-2 py-1 text-[10px] font-mono text-emerald-200 shadow-md"
                    >
                      LMV #{101 + idx} (0.94)
                    </div>
                  ))}
                </div>

                <div className="absolute top-2 left-2 bg-slate-900/80 px-2.5 py-1 rounded text-[10px] font-mono text-slate-300">
                  FEED: {appId.toUpperCase()}_CAM_01
                </div>
              </div>

              {/* Metrics Breakdown */}
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-semibold uppercase">WEIGHTED QUEUE</div>
                  <div className="text-lg font-bold text-cyan-400 font-mono mt-0.5">{st.queue_length.toFixed(1)}</div>
                </div>

                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-semibold uppercase">WAIT TIME</div>
                  <div className="text-lg font-bold text-amber-400 font-mono mt-0.5">{st.wait_since_green_sec.toFixed(0)}s</div>
                </div>

                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-semibold uppercase">PRESSURE SCORE</div>
                  <div className="text-lg font-bold text-purple-400 font-mono mt-0.5">{st.pressure.toFixed(1)}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
