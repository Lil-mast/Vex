import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  color: 'green' | 'blue' | 'orange' | 'red';
  subtitle?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, color, subtitle }) => {
  const colorClasses = {
    green: 'bg-gradient-to-br from-green-900 to-green-800 border-green-500',
    blue: 'bg-gradient-to-br from-blue-900 to-blue-800 border-blue-500',
    orange: 'bg-gradient-to-br from-orange-900 to-orange-800 border-orange-500',
    red: 'bg-gradient-to-br from-red-900 to-red-800 border-red-500'
  };

  const iconColors = {
    green: 'text-green-400',
    blue: 'text-blue-400',
    orange: 'text-orange-400',
    red: 'text-red-400'
  };

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-300 text-sm font-medium">{title}</p>
          <p className="text-white text-2xl font-bold mt-1">{value}</p>
          {subtitle && <p className="text-gray-400 text-xs mt-1">{subtitle}</p>}
        </div>
        <Icon className={`w-8 h-8 ${iconColors[color]}`} />
      </div>
    </div>
  );
};