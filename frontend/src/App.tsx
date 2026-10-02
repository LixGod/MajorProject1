import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { JunctionMap } from './components/JunctionMap';
import { JunctionDetailView } from './components/JunctionDetailView';
import { ManualOverrideModal } from './components/ManualOverrideModal';
import { AnalyticsView } from './components/AnalyticsView';
import { ImageDetectionView } from './components/ImageDetectionView';
import { JunctionTelemetry } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'map' | 'detail' | 'override' | 'analytics' | 'image_upload'>('map');
  const [telemetry, setTelemetry] = useState<Record<string, JunctionTelemetry>>({});
  const [selectedJunctionId, setSelectedJunctionId] = useState<string>('weh_vile_parle');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState<boolean>(false);

  const fetchJunctionsList = () => {
    fetch('/api/junctions')
      .then((res) => res.json())
      .catch(console.error);
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/junctions`;

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket Connected to Smart Traffic Server');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'TELEMETRY_UPDATE' && data.junctions) {
            setTelemetry(data.junctions);
          }
        } catch (e) {
          console.error('WebSocket parse error:', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        ws?.close();
      };
    };

    connectWebSocket();

    return () => {
      if (ws) ws.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  const activeTelemetry = telemetry[selectedJunctionId];
  const activeAlertsCount = Object.values(telemetry).reduce((acc, j) => {
    return acc + (j.alerts.preemption_active ? 1 : 0) + (j.alerts.gridlock_warning ? 1 : 0);
  }, 0);

  const handleApplyOverride = (phaseId: number, reason: string) => {
    fetch(`/api/junctions/${selectedJunctionId}/override`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phase_id: phaseId, operator_id: 'operator_admin', reason })
    }).catch(console.error);
  };

  const handleClearOverride = () => {
    fetch(`/api/junctions/${selectedJunctionId}/clear_override`, {
      method: 'POST'
    }).catch(console.error);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isConnected={isConnected}
        activeAlertsCount={activeAlertsCount}
      />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {activeTab === 'map' && (
          <JunctionMap
            telemetry={telemetry}
            selectedJunctionId={selectedJunctionId}
            onSelectJunction={(id) => {
              setSelectedJunctionId(id);
              setActiveTab('detail');
            }}
          />
        )}

        {activeTab === 'detail' && (
          <JunctionDetailView
            telemetry={activeTelemetry}
            onOpenOverride={() => setIsOverrideModalOpen(true)}
          />
        )}

        {activeTab === 'image_upload' && (
          <ImageDetectionView onJunctionAdded={fetchJunctionsList} />
        )}

        {activeTab === 'override' && (
          <div className="space-y-6">
            <div className="glass-panel p-6">
              <h2 className="text-xl font-bold mb-2">Operator Control Center</h2>
              <p className="text-sm text-slate-400">Select a junction below to trigger or clear safety overrides.</p>
            </div>
            <JunctionDetailView
              telemetry={activeTelemetry}
              onOpenOverride={() => setIsOverrideModalOpen(true)}
            />
          </div>
        )}

        {activeTab === 'analytics' && <AnalyticsView />}
      </main>

      {/* Manual Override Modal */}
      {activeTelemetry && (
        <ManualOverrideModal
          isOpen={isOverrideModalOpen}
          onClose={() => setIsOverrideModalOpen(false)}
          phases={
            activeTelemetry.current_phase
              ? [activeTelemetry.current_phase]
              : []
          }
          onApplyOverride={handleApplyOverride}
          onClearOverride={handleClearOverride}
          isOverrideActive={activeTelemetry.alerts.manual_override_active}
        />
      )}
    </div>
  );
};
export default App;
