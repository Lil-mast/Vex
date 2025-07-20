import { RadiationReading, RiskLevel, Alert, RadiationStats } from '../types/radiation';

export const classifyRiskLevel = (level: number): RiskLevel => {
  if (level < 0.1) return 'safe';
  if (level < 0.5) return 'low';
  if (level < 2.0) return 'moderate';
  if (level < 10.0) return 'high';
  return 'critical';
};

export const getRiskColor = (riskLevel: RiskLevel): string => {
  switch (riskLevel) {
    case 'safe': return '#10b981';
    case 'low': return '#f59e0b';
    case 'moderate': return '#f97316';
    case 'high': return '#ef4444';
    case 'critical': return '#dc2626';
  }
};

export const getRiskBgColor = (riskLevel: RiskLevel): string => {
  switch (riskLevel) {
    case 'safe': return '#064e3b';
    case 'low': return '#451a03';
    case 'moderate': return '#431407';
    case 'high': return '#450a0a';
    case 'critical': return '#7f1d1d';
  }
};

export const formatRadiationLevel = (level: number): string => {
  return `${level.toFixed(3)} μSv/h`;
};

export const generateMockRadiationData = (): RadiationReading[] => {
  const readings: RadiationReading[] = [];
  const locations = [
    'Downtown', 'Industrial District', 'Residential Area', 'Power Plant Vicinity',
    'Hospital Zone', 'University Campus', 'Airport Area', 'Port District'
  ];

  for (let i = 0; i < 50; i++) {
    const level = Math.random() * 15; // 0-15 μSv/h range
    const reading: RadiationReading = {
      id: `reading-${i}`,
      lat: 40.7128 + (Math.random() - 0.5) * 0.1,
      lng: -74.0060 + (Math.random() - 0.5) * 0.1,
      level,
      riskLevel: classifyRiskLevel(level),
      timestamp: new Date(),
      location: locations[Math.floor(Math.random() * locations.length)]
    };
    readings.push(reading);
  }
  
  return readings;
};

export const calculateStats = (readings: RadiationReading[]): RadiationStats => {
  if (readings.length === 0) {
    return {
      totalReadings: 0,
      averageLevel: 0,
      maxLevel: 0,
      safeAreas: 0,
      dangerousAreas: 0
    };
  }

  const totalLevel = readings.reduce((sum, reading) => sum + reading.level, 0);
  const maxLevel = Math.max(...readings.map(r => r.level));
  const safeAreas = readings.filter(r => r.riskLevel === 'safe').length;
  const dangerousAreas = readings.filter(r => ['high', 'critical'].includes(r.riskLevel)).length;

  return {
    totalReadings: readings.length,
    averageLevel: totalLevel / readings.length,
    maxLevel,
    safeAreas,
    dangerousAreas
  };
};

export const generateAlert = (reading: RadiationReading): Alert | null => {
  if (reading.riskLevel === 'safe' || reading.riskLevel === 'low') {
    return null;
  }

  const messages = {
    moderate: 'Elevated radiation detected',
    high: 'High radiation warning',
    critical: 'CRITICAL radiation alert - immediate evacuation recommended'
  };

  return {
    id: `alert-${Date.now()}-${Math.random()}`,
    message: messages[reading.riskLevel as keyof typeof messages],
    severity: reading.riskLevel,
    timestamp: new Date(),
    location: reading.location,
    level: reading.level
  };
};