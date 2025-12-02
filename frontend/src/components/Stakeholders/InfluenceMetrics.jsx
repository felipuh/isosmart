import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp, Users, Network } from 'lucide-react';

const InfluenceMetrics = ({ stakeholders, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-80 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!stakeholders || stakeholders.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Métricas de Influencia</h3>
        <p className="text-gray-500 text-center py-8">No hay datos disponibles</p>
      </div>
    );
  }

  // Preparar datos para el gráfico (top 10 por influencia)
  const chartData = [...stakeholders]
    .sort((a, b) => b.influence_score - a.influence_score)
    .slice(0, 10)
    .map(sh => ({
      name: sh.name.length > 20 ? sh.name.substring(0, 20) + '...' : sh.name,
      fullName: sh.name,
      influence: (sh.influence_score * 100).toFixed(0),
      type: sh.stakeholder_type,
      power: sh.power,
      interest: sh.interest
    }));

  const getBarColor = (value) => {
    if (value >= 70) return '#ef4444'; // Rojo - Alto
    if (value >= 50) return '#f59e0b'; // Naranja - Medio
    return '#3b82f6'; // Azul - Bajo
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900">{data.fullName}</p>
          <p className="text-sm text-gray-600 capitalize">Tipo: {data.type}</p>
          <p className="text-sm text-gray-600">Influencia: {data.influence}%</p>
          <p className="text-sm text-gray-600 capitalize">Poder: {data.power}</p>
          <p className="text-sm text-gray-600 capitalize">Interés: {data.interest}</p>
        </div>
      );
    }
    return null;
  };

  // Calcular estadísticas generales
  const stats = {
    total: stakeholders.length,
    avgInfluence: (stakeholders.reduce((sum, sh) => sum + sh.influence_score, 0) / stakeholders.length * 100).toFixed(1),
    highInfluence: stakeholders.filter(sh => sh.influence_score >= 0.7).length,
    criticalCount: stakeholders.filter(sh => sh.is_critical).length
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center">
        <TrendingUp className="mr-2 h-5 w-5 text-blue-500" />
        Métricas de Influencia
      </h3>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total</p>
              <p className="text-2xl font-bold text-blue-600">{stats.total}</p>
            </div>
            <Users className="h-8 w-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Promedio</p>
              <p className="text-2xl font-bold text-green-600">{stats.avgInfluence}%</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-400" />
          </div>
        </div>

        <div className="bg-orange-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Alta Influencia</p>
              <p className="text-2xl font-bold text-orange-600">{stats.highInfluence}</p>
            </div>
            <Network className="h-8 w-8 text-orange-400" />
          </div>
        </div>

        <div className="bg-red-50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Críticos</p>
              <p className="text-2xl font-bold text-red-600">{stats.criticalCount}</p>
            </div>
            <Network className="h-8 w-8 text-red-400" />
          </div>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Top 10 por Influencia</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 100]} />
            <YAxis type="category" dataKey="name" width={100} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="influence" radius={[0, 8, 8, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.influence)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default InfluenceMetrics;