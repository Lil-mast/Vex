import React, { useState } from 'react';
import { Activity, Shield, AlertTriangle, BarChart3, Zap, MapPin, ArrowLeft } from 'lucide-react';
import { useRadiationData } from '../hooks/useRadiationData';
import { StatsCard } from './StatsCard';
import { AlertPanel } from './AlertPanel';
import { ControlPanel } from './ControlPanel';
import { RadiationHeatmap } from './RadiationHeatmap';
import { formatRadiationLevel } from '../utils/radiationUtils';

interface DashboardProps {
  onBackToLanding?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onBackToLanding }) => {
  const { readings, alerts, stats, isActive, toggleMonitoring, clearAlerts } = useRadiationData();
  const [zoom, setZoom] = useState(1);

  const handleResetView = () => {
    setZoom(1);
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center mb-8">
          {onBackToLanding && (
            <button
              onClick={onBackToLanding}
              className="absolute top-6 left-6 flex items-center gap-2 text-gray-400 hover:text-white transition-colors duration-200 bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg border border-gray-700"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </button>
          )}
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <Zap className="w-10 h-10 text-blue-400" />
            VEX
          </h1>
          <p className="text-gray-400 text-lg">
            Real-time radiation monitoring and outbreak detection system
          </p>
          <div className="flex items-center justify-center gap-2 mt-3">
            <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
            <span className="text-sm text-gray-300">
              {isActive ? 'System Active' : 'System Inactive'} • {stats.totalReadings} sensors online
            </span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard
            title="Total Readings"
            value={stats.totalReadings}
            icon={Activity}
            color="blue"
            subtitle="Active sensors"
          />
          <StatsCard
            title="Average Level"
            value={formatRadiationLevel(stats.averageLevel)}
            icon={BarChart3}
            color="green"
            subtitle="Current average"
          />
          <StatsCard
            title="Peak Level"
            value={formatRadiationLevel(stats.maxLevel)}
            icon={AlertTriangle}
            color="orange"
            subtitle="Highest detected"
          />
          <StatsCard
            title="Safe Areas"
            value={`${stats.safeAreas}/${stats.totalReadings}`}
            icon={Shield}
            color="green"
            subtitle="Within safe limits"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Heatmap - Takes up 2 columns */}
          <div className="lg:col-span-2">
            <RadiationHeatmap 
              readings={readings} 
              zoom={zoom}
              onResetView={handleResetView}
            />
          </div>

          {/* Right sidebar with controls and alerts */}
          <div className="space-y-6">
            <ControlPanel
              isActive={isActive}
              onToggleMonitoring={toggleMonitoring}
              zoom={zoom}
              onZoomChange={setZoom}
              onResetView={handleResetView}
            />
            
            <AlertPanel 
              alerts={alerts}
              onClearAlerts={clearAlerts}
            />
          </div>
        </div>

        {/* Recent Readings Table */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-lg">
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <MapPin className="w-5 h-5 text-blue-400" />
              Recent Sensor Readings
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Radiation Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Risk Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {readings.slice(0, 8).map((reading) => (
                  <tr key={reading.id} className="hover:bg-gray-750 transition-colors duration-200">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {reading.location}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-300">
                      {formatRadiationLevel(reading.level)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span 
                        className="inline-flex px-2 py-1 text-xs font-semibold rounded-full capitalize"
                        style={{ 
                          backgroundColor: `${reading.riskLevel === 'safe' ? '#065f46' : 
                                           reading.riskLevel === 'low' ? '#92400e' :
                                           reading.riskLevel === 'moderate' ? '#9a3412' :
                                           reading.riskLevel === 'high' ? '#991b1b' : '#7f1d1d'}`,
                          color: 'white'
                        }}
                      >
                        {reading.riskLevel}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {reading.timestamp.toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-6 border-t border-gray-700">
          <p className="text-gray-500 text-sm">
            VEX © 2025 • Real-time radiation monitoring system
          </p>
        </div>
      </div>
    </div>
  );
};