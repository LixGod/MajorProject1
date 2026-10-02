import React, { useState } from 'react';
import { Upload, Image as ImageIcon, Cpu, CheckCircle2, Search, MapPin, PlusCircle, AlertCircle } from 'lucide-react';

interface DetectionResult {
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number];
}

interface AnalysisData {
  model_used: string;
  total_vehicles_detected: number;
  category_counts: Record<string, number>;
  detections: DetectionResult[];
  annotated_image_base64: string;
}

interface ImageDetectionViewProps {
  onJunctionAdded?: () => void;
}

export const ImageDetectionView: React.FC<ImageDetectionViewProps> = ({ onJunctionAdded }) => {
  const [selectedModel, setSelectedModel] = useState<string>('best.pt');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisData | null>(null);

  // TomTom Search state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchLoading, setSearchLoading] = useState<boolean>(false);
  const [searchResult, setSearchResult] = useState<any>(null);
  const [addSuccessMsg, setAddSuccessMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setAnalysisResult(null);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('model', selectedModel);

    try {
      const res = await fetch('/api/detect_image', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setAnalysisResult(data);
    } catch (err) {
      console.error('Image detection failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTomTomSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    setSearchResult(null);
    setAddSuccessMsg(null);

    try {
      const res = await fetch('/api/junctions/search_tomtom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery })
      });
      const data = await res.json();
      setSearchResult(data);
    } catch (err) {
      console.error('TomTom Search failed:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAddJunction = async () => {
    if (!searchResult) return;
    const jId = searchQuery.toLowerCase().replace(/[^a-z0-9]/g, '_');

    try {
      const res = await fetch('/api/junctions/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ junction_id: jId, name: searchResult.name, num_approaches: 4 })
      });
      const data = await res.json();
      setAddSuccessMsg(`Successfully added "${searchResult.name}" to Mumbai live map!`);
      if (onJunctionAdded) onJunctionAdded();
    } catch (err) {
      console.error('Failed to add junction:', err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Section 1: Upload & Detect Vehicles using best.pt / local.pt */}
      <div className="glass-panel p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-xl text-white">
              <ImageIcon className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-white">Image Vehicle Detection & Model Testing</h2>
              <p className="text-xs text-slate-400">
                Upload traffic images and test detection using primary <span className="text-cyan-400 font-mono">best.pt</span> or local <span className="text-purple-400 font-mono">local.pt</span> weights.
              </p>
            </div>
          </div>

          {/* Model Selector */}
          <div className="flex items-center space-x-2 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
            <span className="text-xs font-semibold text-slate-400 px-2 flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              MODEL:
            </span>
            <button
              onClick={() => setSelectedModel('best.pt')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono transition-all ${
                selectedModel === 'best.pt'
                  ? 'bg-cyan-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              best.pt (Primary)
            </button>
            <button
              onClick={() => setSelectedModel('local.pt')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono transition-all ${
                selectedModel === 'local.pt'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              local.pt (Secondary)
            </button>
          </div>
        </div>

        {/* Upload Drop Zone & Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <label className="block border-2 border-dashed border-slate-700 hover:border-cyan-500 rounded-2xl p-8 text-center cursor-pointer transition-all bg-slate-950/40 hover:bg-slate-900/60">
              <Upload className="w-10 h-10 text-cyan-400 mx-auto mb-3" />
              <span className="text-sm font-bold text-slate-200 block">Click or Drag Image File Here</span>
              <span className="text-xs text-slate-400 block mt-1">Supports PNG, JPG, JPEG traffic frames</span>
              <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
            </label>

            {selectedFile && (
              <div className="flex items-center justify-between bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs">
                <span className="text-slate-300 font-mono truncate max-w-[200px]">{selectedFile.name}</span>
                <button
                  onClick={handleUploadSubmit}
                  disabled={loading}
                  className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold rounded-lg shadow-md disabled:opacity-50"
                >
                  {loading ? 'Processing Inference...' : `Run Detection (${selectedModel})`}
                </button>
              </div>
            )}
          </div>

          {/* Result / Preview Window */}
          <div className="bg-slate-950 rounded-2xl border border-slate-800 p-4 flex flex-col items-center justify-center min-h-[250px]">
            {analysisResult ? (
              <img
                src={analysisResult.annotated_image_base64}
                alt="Annotated Detection"
                className="w-full h-auto rounded-xl object-contain max-h-72 border border-slate-800 shadow-xl"
              />
            ) : previewUrl ? (
              <img src={previewUrl} alt="Preview" className="w-full h-auto rounded-xl object-contain max-h-72 opacity-60" />
            ) : (
              <div className="text-center text-slate-500 text-xs">
                Annotated bounding box result will render here after running detection.
              </div>
            )}
          </div>
        </div>

        {/* Vehicle Breakdown Statistics */}
        {analysisResult && (
          <div className="bg-slate-950/80 rounded-xl p-5 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                DETECTION ANALYSIS ({analysisResult.model_used})
              </h3>
              <span className="badge badge-green font-mono">
                TOTAL DETECTED: {analysisResult.total_vehicles_detected} VEHICLES
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              {Object.entries(analysisResult.category_counts).map(([cname, count]) => (
                <div key={cname} className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-semibold uppercase">{cname}</div>
                  <div className="text-xl font-extrabold text-cyan-400 font-mono mt-0.5">{count}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Section 2: TomTom Maps API Search for All Junctions in Mumbai */}
      <div className="glass-panel p-6 space-y-6">
        <div className="flex items-center space-x-3 border-b border-slate-800 pb-4">
          <div className="p-2.5 bg-gradient-to-tr from-amber-500 to-rose-600 rounded-xl text-white">
            <MapPin className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-white">TomTom Maps API — Mumbai Junction Geocoder</h2>
            <p className="text-xs text-slate-400">
              Query any junction address or landmark in Mumbai using your live TomTom Search API key (<span className="text-cyan-400 font-mono">Qx47lC...</span>).
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleTomTomSearch()}
              placeholder="e.g. Haji Ali Junction, Mumbai or Chembur Naka, Mumbai..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 pl-10 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
            />
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
          </div>

          <button
            onClick={handleTomTomSearch}
            disabled={searchLoading}
            className="px-6 py-3 bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg disabled:opacity-50 flex items-center space-x-2"
          >
            {searchLoading ? 'Geocoding...' : 'Geocode Junction'}
          </button>
        </div>

        {searchResult && (
          <div className="bg-slate-950/80 rounded-xl p-5 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-sm text-slate-100">{searchResult.name}</h4>
                <p className="text-xs text-slate-400">{searchResult.address}</p>
                <div className="text-[11px] font-mono text-cyan-400 mt-1">
                  LAT: {searchResult.latitude.toFixed(6)}, LON: {searchResult.longitude.toFixed(6)} (Source: {searchResult.source})
                </div>
              </div>

              <button
                onClick={handleAddJunction}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-lg shadow-md flex items-center space-x-1.5"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Add to Live Map</span>
              </button>
            </div>
          </div>
        )}

        {addSuccessMsg && (
          <div className="bg-emerald-950/80 border border-emerald-700 text-emerald-300 p-3 rounded-xl text-xs font-semibold flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{addSuccessMsg}</span>
          </div>
        )}
      </div>
    </div>
  );
};
