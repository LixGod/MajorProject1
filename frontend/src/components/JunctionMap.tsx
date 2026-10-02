import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { JunctionTelemetry } from '../types';
import { MapPin, Navigation } from 'lucide-react';

interface JunctionMapProps {
  telemetry: Record<string, JunctionTelemetry>;
  selectedJunctionId: string;
  onSelectJunction: (id: string) => void;
}

export const JunctionMap: React.FC<JunctionMapProps> = ({
  telemetry,
  selectedJunctionId,
  onSelectJunction
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<Record<string, L.Marker>>({});

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Initialize Leaflet map centered at Mumbai
      const map = L.map(mapContainerRef.current).setView([19.0760, 72.8777], 12);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors | TomTom Geocoding'
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Update markers for each junction
    Object.values(telemetry).forEach((j) => {
      const { junction_id, junction_name, location, approach_states, alerts } = j;
      if (!location || !location.latitude || !location.longitude) return;

      const lat = location.latitude;
      const lng = location.longitude;

      // Calculate total vehicle queue
      const totalQueue = Object.values(approach_states).reduce((acc, s) => acc + s.queue_length, 0);

      let color = '#10b981'; // Green
      if (alerts.preemption_active || alerts.gridlock_warning) {
        color = '#f43f5e'; // Red
      } else if (totalQueue > 12) {
        color = '#f59e0b'; // Amber
      }

      const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `
          <div style="
            background: ${color};
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 15px ${color};
            cursor: pointer;
          "></div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      if (!markersRef.current[junction_id]) {
        const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);
        marker.on('click', () => onSelectJunction(junction_id));
        marker.bindTooltip(`<b>${junction_name}</b><br/>Queue: ${totalQueue.toFixed(1)} veh`, {
          permanent: false,
          direction: 'top'
        });
        markersRef.current[junction_id] = marker;
      } else {
        markersRef.current[junction_id].setLatLng([lat, lng]);
        markersRef.current[junction_id].setIcon(customIcon);
      }
    });

  }, [telemetry, onSelectJunction]);

  return (
    <div className="relative w-full h-[calc(100vh-80px)] rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Floating Info Overlay */}
      <div className="absolute top-4 left-4 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-800 p-4 rounded-xl shadow-xl max-w-sm">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 mb-2">
          <Navigation className="w-4 h-4 text-cyan-400" />
          MUMBAI JUNCTION NETWORK MAP
        </h3>
        <p className="text-xs text-slate-400 mb-3">
          Geocoded coordinates powered by <span className="text-cyan-400 font-semibold">TomTom Maps API</span>. Click any node to open live telemetry.
        </p>

        <div className="space-y-2 text-xs">
          {Object.values(telemetry).map((j) => {
            const isSelected = j.junction_id === selectedJunctionId;
            const totalQueue = Object.values(j.approach_states).reduce((acc, s) => acc + s.queue_length, 0);

            return (
              <div
                key={j.junction_id}
                onClick={() => onSelectJunction(j.junction_id)}
                className={`p-2.5 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
                  isSelected
                    ? 'bg-cyan-950/60 border-cyan-500 text-cyan-200'
                    : 'bg-slate-950/40 border-slate-800 text-slate-300 hover:bg-slate-900'
                }`}
              >
                <div>
                  <div className="font-semibold text-slate-100">{j.junction_name}</div>
                  <div className="text-[10px] text-slate-400 truncate max-w-[200px]">{j.location?.address}</div>
                </div>
                <div className="text-right">
                  <span className="badge badge-green">{totalQueue.toFixed(0)} veh</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
