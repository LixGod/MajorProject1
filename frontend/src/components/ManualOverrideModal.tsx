import React, { useState } from 'react';
import { PhaseData } from '../types';
import { Shield, X, AlertOctagon } from 'lucide-react';

interface ManualOverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
  phases: PhaseData[];
  onApplyOverride: (phaseId: number, reason: string) => void;
  onClearOverride: () => void;
  isOverrideActive: boolean;
}

export const ManualOverrideModal: React.FC<ManualOverrideModalProps> = ({
  isOpen,
  onClose,
  phases,
  onApplyOverride,
  onClearOverride,
  isOverrideActive
}) => {
  const [selectedPhaseId, setSelectedPhaseId] = useState<number>(phases[0]?.id || 1);
  const [reason, setReason] = useState<string>('Traffic incident manual intervention');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Manual Signal Override</h3>
              <p className="text-xs text-slate-400">Mandatory audit logging enabled for operator safety controls</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Phase Selection List */}
        <div className="space-y-3">
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Select Force Target Phase
          </label>
          <div className="space-y-2">
            {phases.map((p) => (
              <div
                key={p.id}
                onClick={() => setSelectedPhaseId(p.id)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                  selectedPhaseId === p.id
                    ? 'bg-rose-950/40 border-rose-500 text-rose-200'
                    : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                <div>
                  <div className="font-bold text-sm text-slate-100">{p.name}</div>
                  <div className="text-xs text-slate-400 font-mono mt-0.5">
                    Movements: {p.movements.join(', ')}
                  </div>
                </div>
                {selectedPhaseId === p.id && (
                  <span className="badge badge-red">SELECTED</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Audit Log Reason Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
            Operator Reason / Audit Log Justification
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:border-rose-500"
            placeholder="Enter reason for manual override..."
          />
        </div>

        {/* Safety Warning */}
        <div className="bg-amber-950/40 border border-amber-800 p-3 rounded-xl flex items-start space-x-2 text-xs text-amber-300">
          <AlertOctagon className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <span>
            Safety Invariant: Override will execute via mandatory <b>All-Red Clearance (3s)</b>. Emergency preemption logic remains active.
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-2">
          {isOverrideActive ? (
            <button
              onClick={() => {
                onClearOverride();
                onClose();
              }}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs uppercase"
            >
              Resume Autonomous Max-Pressure Control
            </button>
          ) : (
            <div />
          )}

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                onApplyOverride(selectedPhaseId, reason);
                onClose();
              }}
              className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs uppercase shadow-lg shadow-rose-600/30"
            >
              Apply Forced Override
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
