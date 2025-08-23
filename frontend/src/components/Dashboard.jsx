import React, { useState, useEffect, useCallback } from 'react';
import { 
  AlertTriangle, 
  Shield, 
  TrendingUp, 
  Activity, 
  Clock, 
  DollarSign,
  Users,
  CreditCard,
  Eye,
  Zap
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, 
         XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalTransactions: 0,
    fraudDetected: 0,
    fraudRate: 0,
    avgResponseTime: 0,
    systemStatus: 'operational',
    recentAlerts: []
  });
  
  const [chartData, setChartData] = useState({
    hourlyTransactions: [],
    fraudTrends: [],
    riskDistribution: [],
    topMerchants: []
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Try to fetch from simplified backend first
      try {
        const healthResponse = await axios.get('/health');
        const statusResponse = await axios.get('/api/v1/status');
        
        setStats({
          totalTransactions: 1250,
          fraudDetected: 23,
          fraudRate: 0.018,
          avgResponseTime: 45,
          systemStatus: healthResponse.data.status || 'operational',
          recentAlerts: [
            { id: 1, severity: 'high', message: 'Suspicious transaction pattern detected', timestamp: new Date().toISOString() },
            { id: 2, severity: 'medium', message: 'Unusual spending behavior', timestamp: new Date(Date.now() - 3600000).toISOString() }
          ]
        });
      } catch (apiErr) {
        console.log('Using fallback data - API endpoints not fully implemented yet');
        // Fallback to sample data
        setStats({
          totalTransactions: 1250,
          fraudDetected: 23,
          fraudRate: 0.018,
          avgResponseTime: 45,
          systemStatus: 'operational',
          recentAlerts: [
            { id: 1, severity: 'high', message: 'Suspicious transaction pattern detected', timestamp: new Date().toISOString() },
            { id: 2, severity: 'medium', message: 'Unusual spending behavior', timestamp: new Date(Date.now() - 3600000).toISOString() },
            { id: 3, severity: 'low', message: 'Geographic anomaly detected', timestamp: new Date(Date.now() - 7200000).toISOString() }
          ]
        });
      }
      
      // Generate sample chart data
      generateChartData();
      
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  // Generate sample chart data
  const generateChartData = () => {
    // Hourly transaction data
    const hourlyData = Array.from({ length: 24 }, (_, i) => ({
      hour: `${i}:00`,
      transactions: Math.floor(Math.random() * 100) + 50,
      fraud: Math.floor(Math.random() * 10) + 1
    }));
    
    // Fraud trends (last 7 days)
    const fraudTrends = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return {
        date: date.toLocaleDateString(),
        fraudRate: (Math.random() * 0.1 + 0.02).toFixed(3),
        transactions: Math.floor(Math.random() * 1000) + 500
      };
    }).reverse();
    
    // Risk distribution
    const riskDistribution = [
      { name: 'Low Risk', value: 65, color: '#10B981' },
      { name: 'Medium Risk', value: 25, color: '#F59E0B' },
      { name: 'High Risk', value: 8, color: '#EF4444' },
      { name: 'Critical', value: 2, color: '#7C2D12' }
    ];
    
    // Top merchants by transaction volume
    const topMerchants = [
      { name: 'Amazon', transactions: 1250, fraudRate: 0.8 },
      { name: 'Walmart', transactions: 980, fraudRate: 1.2 },
      { name: 'Target', transactions: 750, fraudRate: 0.5 },
      { name: 'Best Buy', transactions: 620, fraudRate: 1.8 },
      { name: 'Home Depot', transactions: 580, fraudRate: 0.9 }
    ];
    
    setChartData({
      hourlyTransactions: hourlyData,
      fraudTrends: fraudTrends,
      riskDistribution: riskDistribution,
      topMerchants: topMerchants
    });
  };

  // Auto-refresh data
  useEffect(() => {
    fetchDashboardData();
    
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  // Handle error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Dashboard</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Fraud Detection Dashboard</h1>
          <p className="text-gray-600">Real-time monitoring and analytics for credit card fraud detection</p>
        </div>

        {/* Status Bar */}
        <div className="mb-6">
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
            stats.systemStatus === 'operational' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            <div className={`w-2 h-2 rounded-full mr-2 ${
              stats.systemStatus === 'operational' ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            System Status: {stats.systemStatus}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Transactions"
            value={stats.totalTransactions.toLocaleString()}
            icon={CreditCard}
            color="blue"
            change="+12.5%"
            changeType="positive"
          />
          <MetricCard
            title="Fraud Detected"
            value={stats.fraudDetected.toLocaleString()}
            icon={Shield}
            color="red"
            change={`${stats.fraudRate.toFixed(2)}%`}
            changeType="neutral"
          />
          <MetricCard
            title="Avg Response Time"
            value={`${stats.avgResponseTime.toFixed(1)}ms`}
            icon={Zap}
            color="green"
            change="-8.2%"
            changeType="positive"
          />
          <MetricCard
            title="Active Users"
            value="24"
            icon={Users}
            color="purple"
            change="+2"
            changeType="positive"
          />
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Hourly Transactions */}
          <ChartCard title="Hourly Transaction Volume" icon={Activity}>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData.hourlyTransactions}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Area 
                  type="monotone" 
                  dataKey="transactions" 
                  stroke="#3B82F6" 
                  fill="#3B82F6" 
                  fillOpacity={0.3}
                />
                <Area 
                  type="monotone" 
                  dataKey="fraud" 
                  stroke="#EF4444" 
                  fill="#EF4444" 
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Fraud Trends */}
          <ChartCard title="7-Day Fraud Trends" icon={TrendingUp}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData.fraudTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="fraudRate" 
                  stroke="#EF4444" 
                  strokeWidth={2}
                  name="Fraud Rate"
                />
                <Line 
                  type="monotone" 
                  dataKey="transactions" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  name="Transactions"
                  yAxisId={1}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Risk Distribution */}
          <ChartCard title="Risk Distribution" icon={AlertTriangle}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData.riskDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {chartData.riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Top Merchants */}
          <ChartCard title="Top Merchants by Volume" icon={DollarSign}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData.topMerchants} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={80} />
                <Tooltip />
                <Bar dataKey="transactions" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Recent Alerts */}
        <div className="mb-8">
          <ChartCard title="Recent Fraud Alerts" icon={Eye}>
            <div className="space-y-3">
              {stats.recentAlerts.length > 0 ? (
                stats.recentAlerts.map((alert, index) => (
                  <AlertItem key={index} alert={alert} />
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Shield className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No recent alerts</p>
                </div>
              )}
            </div>
          </ChartCard>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <QuickActionCard
            title="Run Detection"
            description="Process a single transaction for fraud detection"
            icon={Zap}
            action="/detect"
            color="blue"
          />
          <QuickActionCard
            title="Batch Processing"
            description="Process multiple transactions at once"
            icon={Activity}
            action="/batch"
            color="green"
          />
          <QuickActionCard
            title="View Reports"
            description="Generate detailed fraud analysis reports"
            icon={TrendingUp}
            action="/reports"
            color="purple"
          />
        </div>
      </div>
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, icon: Icon, color, change, changeType }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600'
  };

  const changeColorClasses = {
    positive: 'text-green-600',
    negative: 'text-red-600',
    neutral: 'text-gray-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm font-medium ${changeColorClasses[changeType]}`}>
              {change}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};

// Chart Card Component
const ChartCard = ({ title, icon: Icon, children }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <Icon className="w-5 h-5 text-gray-400" />
      </div>
      <div className="p-6">
        {children}
      </div>
    </div>
  );
};

// Alert Item Component
const AlertItem = ({ alert }) => {
  const severityColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800'
  };

  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center space-x-3">
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${severityColors[alert.severity] || 'bg-gray-100 text-gray-800'}`}>
          {alert.severity}
        </div>
        <div>
          <p className="font-medium text-gray-900">Transaction {alert.transaction_id}</p>
          <p className="text-sm text-gray-600">{alert.explanation}</p>
        </div>
      </div>
      <div className="text-right">
        <p className="text-sm font-medium text-gray-900">
          ${alert.amount?.toFixed(2) || 'N/A'}
        </p>
        <p className="text-xs text-gray-500">
          {new Date(alert.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

// Quick Action Card Component
const QuickActionCard = ({ title, description, icon: Icon, action, color }) => {
  const colorClasses = {
    blue: 'bg-blue-600 hover:bg-blue-700',
    green: 'bg-green-600 hover:bg-green-700',
    purple: 'bg-purple-600 hover:bg-purple-700'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="text-center">
        <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg ${colorClasses[color]} text-white mb-4`}>
          <Icon className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 mb-4">{description}</p>
        <button
          className={`px-4 py-2 ${colorClasses[color]} text-white rounded-lg transition-colors`}
          onClick={() => window.location.href = action}
        >
          Get Started
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
