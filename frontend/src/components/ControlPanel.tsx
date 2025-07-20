import React, { useState } from 'react';
import { Play, Pause, RotateCcw, ZoomIn, ZoomOut, Settings } from 'lucide-react';

interface ControlPanelProps {
  isActive: boolean;
  onToggleMonitoring: () => void;
  zoom: number;
  onZoomChange: (zoom: number) => void;
  onResetView: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  isActive,
  onToggleMonitoring,
  zoom,
  onZoomChange,
  onResetView
}) => {
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 shadow-lg">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Settings className="w-5 h-5 text-blue-400" />
        Control Panel
      </h3>

      <div className="space-y-4">
        {/* Monitoring Control */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Radiation Monitoring
          </label>
          <button
            onClick={onToggleMonitoring}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
              isActive
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-600 hover:bg-gray-700 text-gray-200'
            }`}
          >
            {isActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isActive ? 'Stop Monitoring' : 'Start Monitoring'}
          </button>
          <div className="flex items-center gap-2 mt-2">
            <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-400 animate-pulse' : 'bg-gray-500'}`}></div>
            <span className="text-xs text-gray-400">
              {isActive ? 'Live monitoring active' : 'Monitoring paused'}
            </span>
          </div>
        </div>

        {/* Zoom Controls */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Map Zoom ({zoom.toFixed(1)}x)
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => onZoomChange(Math.max(0.5, zoom - 0.5))}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors duration-200"
            >
              <ZoomOut className="w-4 h-4" />
              Out
            </button>
            <button
              onClick={() => onZoomChange(Math.min(5, zoom + 0.5))}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors duration-200"
            >
              <ZoomIn className="w-4 h-4" />
              In
            </button>
          </div>
          <input
            type="range"
            min="0.5"
            max="5"
            step="0.1"
            value={zoom}
            onChange={(e) => onZoomChange(Number(e.target.value))}
            className="w-full mt-2 accent-blue-500"
          />
        </div>

        {/* Reset View */}
        <button
          onClick={onResetView}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
        >
          <RotateCcw className="w-4 h-4" />
          Reset View
        </button>

        {/* Additional Settings */}
        <div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="w-full text-left text-sm text-gray-400 hover:text-white transition-colors duration-200"
          >
            Advanced Settings {showSettings ? '▼' : '▶'}
          </button>
          {showSettings && (
            <div className="mt-2 space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Update Interval</span>
                <span className="text-white">3 seconds</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Data Points</span>
                <span className="text-white">50 sensors</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Coverage Area</span>
                <span className="text-white">100 km²</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};