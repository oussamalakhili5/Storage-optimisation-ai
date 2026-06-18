import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const StorageChart = ({ serverId }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!serverId) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch both history and forecast simultaneously
        const [historyRes, forecastRes] = await Promise.all([
          fetch(`http://localhost:8000/api/storage/history/${serverId}`),
          fetch(`http://localhost:8000/api/storage/forecast/${serverId}?days=7`)
        ]);

        if (!historyRes.ok) throw new Error("Failed to fetch historical data");
        
        const historyJson = await historyRes.json();
        const historyData = historyJson.data || [];

        let forecastData = [];
        if (forecastRes.ok) {
          const forecastJson = await forecastRes.json();
          forecastData = forecastJson.data || [];
        }

        // Merge the data for Recharts
        // History data points will have 'historical_used'
        // Forecast data points will have 'forecasted_used'
        
        const mergedData = [];
        
        // Add historical data
        historyData.forEach(item => {
          mergedData.push({
            date: item.date,
            historical_used: item.used_storage,
            forecasted_used: null,
            total: item.total_storage
          });
        });

        // To make the dashed line connect to the solid line, 
        // we add the last historical point as the start of the forecast line
        if (historyData.length > 0 && forecastData.length > 0) {
          const lastHistory = historyData[historyData.length - 1];
          forecastData.unshift({
            date: lastHistory.date,
            predicted_used_storage: lastHistory.used_storage,
            total_storage: lastHistory.total_storage
          });
        }

        // Add forecast data
        forecastData.forEach(item => {
          // If the date already exists (e.g. the connection point), update it
          const existing = mergedData.find(d => d.date === item.date);
          if (existing) {
            existing.forecasted_used = item.predicted_used_storage;
          } else {
            mergedData.push({
              date: item.date,
              historical_used: null,
              forecasted_used: item.predicted_used_storage,
              total: item.total_storage
            });
          }
        });

        setData(mergedData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [serverId]);

  if (loading) return <div className="p-4 text-center">Loading storage metrics for {serverId}...</div>;
  if (error) return <div className="p-4 text-red-500 bg-red-50 rounded">Error: {error}</div>;
  if (data.length === 0) return <div className="p-4">No data available for {serverId}</div>;

  return (
    <div className="w-full h-96 bg-white p-4 rounded-lg shadow-sm border border-gray-100">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Storage Evolution & Forecast: {serverId}</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fill: '#6b7280' }} tickMargin={10} />
          <YAxis 
            domain={[0, data[0]?.total || 'dataMax + 100']} 
            tick={{ fill: '#6b7280' }} 
            label={{ value: 'Storage (GB)', angle: -90, position: 'insideLeft', fill: '#4b5563' }}
          />
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          
          {/* Solid line for historical data */}
          <Line 
            type="monotone" 
            name="Historical Usage"
            dataKey="historical_used" 
            stroke="#3b82f6" 
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6 }} 
          />
          
          {/* Dashed line for forecast data */}
          <Line 
            type="monotone" 
            name="AI Forecast"
            dataKey="forecasted_used" 
            stroke="#f59e0b" 
            strokeWidth={3}
            strokeDasharray="5 5"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default StorageChart;
