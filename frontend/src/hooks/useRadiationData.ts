import { useState, useEffect, useCallback } from 'react';
import { RadiationReading, Alert, RadiationStats } from '../types/radiation';
import { generateMockRadiationData, calculateStats, generateAlert } from '../utils/radiationUtils';

export const useRadiationData = () => {
  const [readings, setReadings] = useState<RadiationReading[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<RadiationStats>({
    totalReadings: 0,
    averageLevel: 0,
    maxLevel: 0,
    safeAreas: 0,
    dangerousAreas: 0
  });
  const [isActive, setIsActive] = useState(true);

  const updateReadings = useCallback(() => {
    const newReadings = generateMockRadiationData();
    setReadings(newReadings);
    
    const newStats = calculateStats(newReadings);
    setStats(newStats);

    // Generate alerts for dangerous readings
    const newAlerts: Alert[] = [];
    newReadings.forEach(reading => {
      const alert = generateAlert(reading);
      if (alert) {
        newAlerts.push(alert);
      }
    });

    setAlerts(prevAlerts => {
      const combinedAlerts = [...newAlerts, ...prevAlerts].slice(0, 10); // Keep last 10 alerts
      return combinedAlerts;
    });
  }, []);

  useEffect(() => {
    // Initial data load
    updateReadings();

    // Set up real-time updates every 3 seconds
    const interval = setInterval(() => {
      if (isActive) {
        updateReadings();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [updateReadings, isActive]);

  const toggleMonitoring = () => {
    setIsActive(!isActive);
  };

  const clearAlerts = () => {
    setAlerts([]);
  };

  return {
    readings,
    alerts,
    stats,
    isActive,
    toggleMonitoring,
    clearAlerts
  };
};