import React from 'react';
import { 
  Zap, 
  Shield, 
  AlertTriangle, 
  Activity, 
  MapPin, 
  Eye,
  ArrowRight,
  CheckCircle,
  Globe,
  Clock
} from 'lucide-react';

interface LandingPageProps {
  onEnterApp: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterApp }) => {
  const features = [
    {
      icon: Activity,
      title: "Real-Time Monitoring",
      description: "Continuous radiation level tracking with live data feeds from multiple sensors across the region."
    },
    {
      icon: MapPin,
      title: "Interactive Heatmap",
      description: "Visual representation of radiation levels with zoom and pan controls for detailed area analysis."
    },
    {
      icon: AlertTriangle,
      title: "Instant Alerts",
      description: "Immediate notifications when radiation levels exceed safe thresholds with severity classification."
    },
    {
      icon: Shield,
      title: "Risk Assessment",
      description: "AI-powered risk level classification from safe to critical with actionable recommendations."
    },
    {
      icon: Eye,
      title: "Advanced Analytics",
      description: "Comprehensive statistics and trend analysis for informed decision making."
    },
    {
      icon: Globe,
      title: "Wide Coverage",
      description: "Extensive sensor network providing comprehensive radiation monitoring across large areas."
    }
  ];

  const stats = [
    { value: "50+", label: "Active Sensors" },
    { value: "24/7", label: "Monitoring" },
    { value: "100km²", label: "Coverage Area" },
    { value: "<3s", label: "Alert Time" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `radial-gradient(circle at 25% 25%, #3b82f6 0%, transparent 50%),
                             radial-gradient(circle at 75% 75%, #1d4ed8 0%, transparent 50%)`
          }}></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-6 py-20">
          <div className="text-center">
            {/* Logo and Title */}
            <div className="flex items-center justify-center gap-4 mb-8">
              <div className="relative">
                <Zap className="w-16 h-16 text-blue-400" />
                <div className="absolute inset-0 w-16 h-16 bg-blue-400 rounded-full opacity-20 animate-pulse"></div>
              </div>
              <h1 className="text-5xl md:text-6xl font-bold text-white">
                VEX
              </h1>
            </div>

            {/* Subtitle */}
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
              Advanced AI-powered radiation detection and outbreak monitoring system with 
              real-time alerts and interactive visualization
            </p>

            {/* Status Indicator */}
            <div className="flex items-center justify-center gap-3 mb-12">
              <div className="flex items-center gap-2 bg-green-900 bg-opacity-50 px-4 py-2 rounded-full border border-green-500">
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-300 text-sm font-medium">System Online</span>
              </div>
              <div className="flex items-center gap-2 bg-blue-900 bg-opacity-50 px-4 py-2 rounded-full border border-blue-500">
                <Clock className="w-4 h-4 text-blue-400" />
                <span className="text-blue-300 text-sm font-medium">Live Monitoring Active</span>
              </div>
            </div>

            {/* CTA Button */}
            <button
              onClick={onEnterApp}
              className="group relative inline-flex items-center gap-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300 transform hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/25"
            >
              <span>Enter Monitoring Dashboard</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-500 rounded-xl opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
            </button>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16 max-w-4xl mx-auto">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-white mb-2">{stat.value}</div>
                  <div className="text-gray-400 text-sm">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20 bg-gray-900 bg-opacity-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Advanced Radiation Monitoring Features
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Comprehensive radiation detection and analysis tools designed for maximum safety and awareness
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group bg-gray-800 bg-opacity-50 border border-gray-700 rounded-xl p-6 hover:bg-opacity-70 hover:border-blue-500 transition-all duration-300 hover:transform hover:scale-105"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-blue-600 bg-opacity-20 rounded-lg flex items-center justify-center group-hover:bg-opacity-30 transition-all duration-300">
                    <feature.icon className="w-6 h-6 text-blue-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
                </div>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Safety Information */}
      <div className="py-16 bg-gradient-to-r from-blue-900 to-indigo-900">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h3 className="text-2xl md:text-3xl font-bold text-white mb-6">
            Your Safety is Our Priority
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center gap-3 justify-center">
              <CheckCircle className="w-6 h-6 text-green-400" />
              <span className="text-white">Real-time Detection</span>
            </div>
            <div className="flex items-center gap-3 justify-center">
              <CheckCircle className="w-6 h-6 text-green-400" />
              <span className="text-white">Instant Notifications</span>
            </div>
            <div className="flex items-center gap-3 justify-center">
              <CheckCircle className="w-6 h-6 text-green-400" />
              <span className="text-white">AI-Powered Analysis</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="py-8 bg-gray-900 border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-gray-500">
            VEX © 2025 • Advanced radiation monitoring and detection system
          </p>
        </div>
      </div>
    </div>
  );
};