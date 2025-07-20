import React from 'react';
import { AlertTriangle, Clock, MapPin, X } from 'lucide-react';
import { Alert } from '../types/radiation';
import { getRiskColor, formatRadiationLevel } from '../utils/radiationUtils';

interface AlertPanelProps {
  alerts: Alert[];
  onClearAlerts: () => void;
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts, onClearAlerts }) => {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString();
  };

  const getSeverityIcon = (severity: string) => {
    return <AlertTriangle className={`w-4 h-4`} style={{ color: getRiskColor(severity as any) }} />;
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          Real-Time Alerts
          {alerts.length > 0 && (
            <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
              {alerts.length}
            </span>
          )}
        </h3>
        {alerts.length > 0 && (
          <button
            onClick={onClearAlerts}
            className="text-gray-400 hover:text-white transition-colors duration-200"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="space-y-3 max-h-64 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-900 rounded-full flex items-center justify-center mx-auto mb-3">
              <AlertTriangle className="w-8 h-8 text-green-400" />
            </div>
            <p className="text-gray-400">No active alerts</p>
            <p className="text-gray-500 text-sm">All radiation levels are within safe parameters</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className="bg-gray-900 border border-gray-600 rounded-lg p-4 hover:bg-gray-850 transition-colors duration-200"
            >
              <div className="flex items-start gap-3">
                {getSeverityIcon(alert.severity)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-white font-medium text-sm">{alert.message}</h4>
                    <span className="text-gray-400 text-xs flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTime(alert.timestamp)}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {alert.location}
                    </span>
                    <span className="font-mono">
                      {formatRadiationLevel(alert.level)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};