import React, { useState, useEffect } from 'react';

const AlertPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCriticalAlerts = async () => {
      setLoading(true);
      setError(null);
      try {
        // 1. Fetch servers that are currently critical
        const criticalRes = await fetch('http://localhost:8000/api/alerts/critical');
        if (!criticalRes.ok) throw new Error("Failed to fetch critical alerts");
        
        const criticalJson = await criticalRes.json();
        const criticalServers = criticalJson.data || [];

        // 2. For each critical server, fetch its ML forecast to calculate Days to 100%
        const enrichedAlerts = await Promise.all(
          criticalServers.map(async (server) => {
            try {
              // Fetch a longer forecast to find the saturation point
              const forecastRes = await fetch(`http://localhost:8000/api/storage/forecast/${server.server_id}?days=30`);
              if (!forecastRes.ok) return { ...server, daysToFull: 'Unknown' };

              const forecastJson = await forecastRes.json();
              const forecastData = forecastJson.data || [];

              // Find the first day where predicted usage exceeds total storage (or hits 100%)
              const saturationPoint = forecastData.findIndex(
                (day) => day.predicted_used_storage >= server.total_storage
              );

              return {
                ...server,
                // If it hits 100% within 30 days, index + 1 is the number of days.
                // If not found in 30 days, we mark it as >30.
                daysToFull: saturationPoint !== -1 ? saturationPoint + 1 : '>30'
              };
            } catch (err) {
              return { ...server, daysToFull: 'Error' };
            }
          })
        );

        setAlerts(enrichedAlerts);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCriticalAlerts();
  }, []);

  if (loading) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md shadow-sm animate-pulse">
        <p className="text-red-700">Analyzing critical server trajectories...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md shadow-sm">
        <h3 className="text-red-800 font-bold">Error loading alerts</h3>
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-md shadow-sm">
        <h3 className="text-green-800 font-bold">System Healthy</h3>
        <p className="text-green-700">No critical servers detected. All storage capacities are optimal.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-100 overflow-hidden">
      <div className="bg-red-600 px-4 py-3 border-b border-red-700">
        <h3 className="text-white font-bold text-lg flex items-center">
          <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
          Critical Storage Alerts
        </h3>
      </div>
      
      <div className="divide-y divide-gray-100">
        {alerts.map((alert, index) => (
          <div key={index} className="p-4 hover:bg-red-50 transition-colors duration-150">
            <div className="flex justify-between items-start">
              <div>
                <span className="inline-block px-2 py-1 bg-red-100 text-red-800 text-xs font-bold rounded-full mb-2">
                  {alert.server_id}
                </span>
                <p className="text-gray-800 text-sm">
                  <span className="font-semibold">Warning:</span> Server {alert.server_id} is currently at 
                  <span className="font-bold text-red-600 ml-1">{alert.utilization_percent}%</span> capacity 
                  ({alert.used_storage} / {alert.total_storage} GB).
                </p>
                <p className="text-sm mt-1 text-red-700 font-medium">
                  {alert.daysToFull === '>30' 
                    ? "Based on AI forecasting, it will not hit 100% in the next 30 days." 
                    : alert.daysToFull === 'Unknown' || alert.daysToFull === 'Error'
                    ? "AI forecast unavailable."
                    : `Based on AI forecasting, it will reach 100% capacity in exactly ${alert.daysToFull} day(s).`
                  }
                </p>
              </div>
              
              <div className="ml-4 flex-shrink-0">
                <div className="w-16 h-16 rounded-full border-4 border-red-200 flex items-center justify-center relative">
                  <svg className="w-full h-full absolute transform -rotate-90 text-red-600" viewBox="0 0 36 36">
                    <path
                      className="text-red-500"
                      strokeDasharray={`${alert.utilization_percent}, 100`}
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                  </svg>
                  <span className="text-xs font-bold text-gray-700 relative z-10">
                    {alert.utilization_percent}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertPanel;
