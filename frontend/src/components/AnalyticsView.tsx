import React, { useEffect, useState } from 'react';
import { AnalyticsComparison } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { Award, TrendingUp, Clock, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';

export const AnalyticsView: React.FC = () => {
  const [data, setData] = useState<AnalyticsComparison | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch('/api/analytics')
      .then((res) => res.json())
      .then((resData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load analytics:', err);
        setLoading(false);
      });
  }, []);

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-96 glass-panel text-cyan-400 font-mono text-sm animate-pulse">
        Running simulation-mode paper evaluation benchmark...
      </div>
    );
  }

  const chartData = [
    {
      metric: 'Avg Wait (s)',
      Baseline: data.baseline.avg_wait_sec,
      MaxPressure: data.max_pressure.avg_wait_sec
    },
    {
      metric: '95th Wait (s)',
      Baseline: data.baseline.p95_wait_sec,
      MaxPressure: data.max_pressure.p95_wait_sec
    },
    {
      metric: 'Gridlock Triggers',
      Baseline: data.baseline.gridlock_triggers,
      MaxPressure: data.max_pressure.gridlock_triggers
    },
    {
      metric: 'Preemption Latency (s)',
      Baseline: data.baseline.preemption_response_sec,
      MaxPressure: data.max_pressure.preemption_response_sec
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Paper Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel p-6 border-l-4 border-emerald-500 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AVERAGE WAIT REDUCTION</div>
            <div className="text-3xl font-extrabold text-emerald-400 font-mono mt-1">
              -{data.improvement.avg_wait_reduction_pct}%
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Compared to Fixed-Timer baseline</p>
          </div>
          <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
            <TrendingUp className="w-8 h-8" />
          </div>
        </div>

        <div className="glass-panel p-6 border-l-4 border-cyan-500 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">95TH %-ILE TAIL WAIT</div>
            <div className="text-3xl font-extrabold text-cyan-400 font-mono mt-1">
              -{data.improvement.p95_wait_reduction_pct}%
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Starvation cap override enforced</p>
          </div>
          <div className="p-3 bg-cyan-500/10 rounded-xl text-cyan-400">
            <Clock className="w-8 h-8" />
          </div>
        </div>

        <div className="glass-panel p-6 border-l-4 border-purple-500 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">THROUGHPUT INCREASE</div>
            <div className="text-3xl font-extrabold text-purple-400 font-mono mt-1">
              +{data.improvement.throughput_increase_pct}%
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Vehicles cleared per hour</p>
          </div>
          <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
            <Zap className="w-8 h-8" />
          </div>
        </div>
      </div>

      {/* Main Comparative Results Table */}
      <div className="glass-panel p-6">
        <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
          <Award className="w-5 h-5 text-amber-400" />
          PAPER EVALUATION RESULTS TABLE: BASELINE VS PROPOSED ALGORITHM
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider bg-slate-950/40">
                <th className="p-3.5">Control Method</th>
                <th className="p-3.5">Avg Wait (sec)</th>
                <th className="p-3.5">95th %-ile Wait (sec)</th>
                <th className="p-3.5">Throughput (veh/hr)</th>
                <th className="p-3.5">Gridlock Triggers</th>
                <th className="p-3.5">Preemption Latency (sec)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              <tr className="hover:bg-slate-900/40">
                <td className="p-3.5 font-sans font-semibold text-slate-300">Fixed-Timer Baseline</td>
                <td className="p-3.5 text-amber-400">{data.baseline.avg_wait_sec.toFixed(1)}s</td>
                <td className="p-3.5 text-amber-400">{data.baseline.p95_wait_sec.toFixed(1)}s</td>
                <td className="p-3.5 text-slate-300">{data.baseline.throughput_veh_per_hr.toFixed(0)}</td>
                <td className="p-3.5 text-rose-400">{data.baseline.gridlock_triggers}</td>
                <td className="p-3.5 text-amber-400">{data.baseline.preemption_response_sec.toFixed(1)}s</td>
              </tr>
              <tr className="bg-cyan-950/20 hover:bg-cyan-950/30">
                <td className="p-3.5 font-sans font-bold text-cyan-300 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Max-Pressure + Aging + Gap-Out (Proposed)
                </td>
                <td className="p-3.5 font-bold text-emerald-400">{data.max_pressure.avg_wait_sec.toFixed(1)}s</td>
                <td className="p-3.5 font-bold text-emerald-400">{data.max_pressure.p95_wait_sec.toFixed(1)}s</td>
                <td className="p-3.5 font-bold text-purple-300">{data.max_pressure.throughput_veh_per_hr.toFixed(0)}</td>
                <td className="p-3.5 font-bold text-emerald-400">{data.max_pressure.gridlock_triggers}</td>
                <td className="p-3.5 font-bold text-emerald-400">{data.max_pressure.preemption_response_sec.toFixed(1)}s</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual Comparison Chart */}
      <div className="glass-panel p-6">
        <h4 className="text-sm font-bold text-slate-200 mb-4 uppercase tracking-wider">
          Visual Metric Comparison
        </h4>
        <div className="w-full h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="metric" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
              <Legend />
              <Bar dataKey="Baseline" fill="#f59e0b" radius={[6, 6, 0, 0]} />
              <Bar dataKey="MaxPressure" fill="#10b981" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
