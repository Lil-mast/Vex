import React, { useRef, useEffect, useState } from 'react';
import { RadiationReading, HeatmapPoint } from '../types/radiation';
import { getRiskColor } from '../utils/radiationUtils';

interface RadiationHeatmapProps {
  readings: RadiationReading[];
  zoom: number;
  onResetView: () => void;
}

export const RadiationHeatmap: React.FC<RadiationHeatmapProps> = ({ readings, zoom }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });

  // Convert lat/lng to canvas coordinates
  const latLngToCanvas = (lat: number, lng: number, width: number, height: number) => {
    // Simple projection for demo purposes
    const centerLat = 40.7128;
    const centerLng = -74.0060;
    
    const x = ((lng - centerLng) * 5000 * zoom + width / 2) + pan.x;
    const y = ((centerLat - lat) * 5000 * zoom + height / 2) + pan.y;
    
    return { x, y };
  };

  // Create heatmap points from readings
  const createHeatmapPoints = (width: number, height: number): HeatmapPoint[] => {
    return readings.map(reading => {
      const { x, y } = latLngToCanvas(reading.lat, reading.lng, width, height);
      return {
        x,
        y,
        intensity: Math.min(reading.level / 15, 1), // Normalize to 0-1
        riskLevel: reading.riskLevel
      };
    });
  };

  // Draw heatmap
  const drawHeatmap = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const { width, height } = canvas;
    
    // Clear canvas
    ctx.fillStyle = '#111827';
    ctx.fillRect(0, 0, width, height);

    const points = createHeatmapPoints(width, height);

    // Draw grid
    ctx.strokeStyle = '#374151';
    ctx.lineWidth = 1;
    for (let i = 0; i < width; i += 50) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, height);
      ctx.stroke();
    }
    for (let i = 0; i < height; i += 50) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(width, i);
      ctx.stroke();
    }

    // Draw heatmap points
    points.forEach(point => {
      if (point.x < -100 || point.x > width + 100 || point.y < -100 || point.y > height + 100) {
        return; // Skip points outside visible area
      }

      const radius = 20 + (point.intensity * 40 * zoom);
      const gradient = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, radius);
      
      const color = getRiskColor(point.riskLevel);
      gradient.addColorStop(0, `${color}80`); // 50% opacity
      gradient.addColorStop(0.5, `${color}40`); // 25% opacity
      gradient.addColorStop(1, `${color}00`); // Transparent
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
      ctx.fill();

      // Draw center point
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw center crosshair
    const centerX = width / 2 + pan.x;
    const centerY = height / 2 + pan.y;
    ctx.strokeStyle = '#6b7280';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(centerX - 10, centerY);
    ctx.lineTo(centerX + 10, centerY);
    ctx.moveTo(centerX, centerY - 10);
    ctx.lineTo(centerX, centerY + 10);
    ctx.stroke();
  };

  // Handle mouse events for panning
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - lastMousePos.x;
    const deltaY = e.clientY - lastMousePos.y;
    
    setPan(prev => ({
      x: prev.x + deltaX,
      y: prev.y + deltaY
    }));
    
    setLastMousePos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Handle wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    // Zoom is handled by parent component
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      drawHeatmap();
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    return () => window.removeEventListener('resize', resizeCanvas);
  }, []);

  useEffect(() => {
    drawHeatmap();
  }, [readings, zoom, pan]);

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden shadow-lg">
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          Live Radiation Heatmap
        </h3>
        <p className="text-sm text-gray-400 mt-1">
          Interactive visualization • Click and drag to pan • Scroll to zoom
        </p>
      </div>
      
      <div className="relative">
        <canvas
          ref={canvasRef}
          className="w-full h-96 cursor-move"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        />
        
        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-gray-900 bg-opacity-90 rounded-lg p-3">
          <h4 className="text-white text-sm font-medium mb-2">Risk Levels</h4>
          <div className="space-y-1">
            {[
              { level: 'Safe', color: '#10b981', range: '< 0.1 μSv/h' },
              { level: 'Low', color: '#f59e0b', range: '0.1-0.5 μSv/h' },
              { level: 'Moderate', color: '#f97316', range: '0.5-2.0 μSv/h' },
              { level: 'High', color: '#ef4444', range: '2.0-10 μSv/h' },
              { level: 'Critical', color: '#dc2626', range: '> 10 μSv/h' }
            ].map(item => (
              <div key={item.level} className="flex items-center gap-2 text-xs">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                ></div>
                <span className="text-white">{item.level}</span>
                <span className="text-gray-400">{item.range}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Zoom indicator */}
        <div className="absolute top-4 right-4 bg-gray-900 bg-opacity-90 rounded-lg px-3 py-2">
          <span className="text-white text-sm font-mono">{zoom.toFixed(1)}x</span>
        </div>
      </div>
    </div>
  );
};