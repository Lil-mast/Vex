export interface RadiationReading {
  id: string;
  lat: number;
  lng: number;
  level: number; // μSv/h (microsieverts per hour)
  riskLevel: RiskLevel;
  timestamp: Date;
  location: string;
}

export type RiskLevel = 'safe' | 'low' | 'moderate' | 'high' | 'critical';

export interface Alert {
  id: string;
  message: string;
  severity: RiskLevel;
  timestamp: Date;
  location: string;
  level: number;
}

export interface RadiationStats {
  totalReadings: number;
  averageLevel: number;
  maxLevel: number;
  safeAreas: number;
  dangerousAreas: number;
}

export interface HeatmapPoint {
  x: number;
  y: number;
  intensity: number;
  riskLevel: RiskLevel;
}