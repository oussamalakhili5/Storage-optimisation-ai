import { useEffect, useState } from "react";
import "./App.css";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  BarChart,
  Bar,
} from "recharts";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("storage_user");

    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch (error) {
        console.error("Erreur localStorage :", error);
        localStorage.removeItem("storage_user");
        return null;
      }
    }

    return null;
  });

  const [authMode, setAuthMode] = useState("login");

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [authMessage, setAuthMessage] = useState("");

  const [storageData, setStorageData] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [predictionData, setPredictionData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const [selectedServer, setSelectedServer] = useState("all");

  useEffect(() => {
    async function fetchAllData() {
      setLoading(true);

      try {
        const [
          statusRes,
          historyRes,
          predictionRes,
          anomaliesRes,
          alertsRes,
          recommendationsRes,
          statisticsRes,
          reportRes,
        ] = await Promise.all([
          fetch(`${API_URL}/storage/status`),
          fetch(`${API_URL}/storage/history`),
          fetch(`${API_URL}/storage/prediction`),
          fetch(`${API_URL}/storage/anomalies`),
          fetch(`${API_URL}/storage/alerts`),
          fetch(`${API_URL}/storage/recommendations`),
          fetch(`${API_URL}/storage/statistics`),
          fetch(`${API_URL}/storage/report`),
        ]);

        setStorageData(await statusRes.json());
        setHistoryData(await historyRes.json());
        setPredictionData(await predictionRes.json());
        setAnomalies(await anomaliesRes.json());
        setAlerts(await alertsRes.json());
        setRecommendations(await recommendationsRes.json());
        setStatistics(await statisticsRes.json());
        setReport(await reportRes.json());
      } catch (error) {
        console.error("Erreur lors du chargement des données :", error);
      } finally {
        setLoading(false);
      }
    }

    if (user) {
      fetchAllData();
    }
  }, [user]);

  async function handleRegister(e) {
    e.preventDefault();
    setAuthMessage("");

    try {
      const response = await fetch(`${API_URL}/api/register/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setAuthMessage(data.detail || "Erreur lors de l'inscription");
        return;
      }

      setAuthMessage("Compte créé avec succès. Connectez-vous maintenant.");
      setAuthMode("login");
      setPassword("");
    } catch (error) {
      console.error("Erreur register :", error);
      setAuthMessage("Erreur de connexion avec le serveur");
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    setAuthMessage("");

    try {
      const response = await fetch(`${API_URL}/api/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setAuthMessage(data.detail || "Email ou mot de passe incorrect");
        return;
      }

      setUser(data.user);
      localStorage.setItem("storage_user", JSON.stringify(data.user));
    } catch (error) {
      console.error("Erreur login :", error);
      setAuthMessage("Erreur de connexion avec le serveur");
    }
  }

  function handleLogout() {
    localStorage.removeItem("storage_user");

    setUser(null);
    setStorageData(null);
    setHistoryData([]);
    setPredictionData([]);
    setAnomalies([]);
    setAlerts([]);
    setRecommendations([]);
    setStatistics(null);
    setReport(null);
    setSelectedServer("all");

    setUsername("");
    setEmail("");
    setPassword("");
    setAuthMessage("");
    setAuthMode("login");
  }

  const serverList = [
    ...new Set(historyData.map((item) => item.server_id)),
  ];

  const filteredHistory =
    selectedServer === "all"
      ? historyData
      : historyData.filter((item) => item.server_id === selectedServer);

  const filteredAlerts =
    selectedServer === "all"
      ? alerts
      : alerts.filter((item) => item.server_id === selectedServer);

  const filteredAnomalies =
    selectedServer === "all"
      ? anomalies
      : anomalies.filter((item) => item.server_id === selectedServer);

  const filteredRecommendations =
    selectedServer === "all"
      ? recommendations
      : recommendations.filter((item) => item.server_id === selectedServer);

  const filteredPredictions =
    selectedServer === "all"
      ? predictionData
      : predictionData.filter((item) => item.server_id === selectedServer);

  const anomalyPoints = filteredHistory.filter((item) =>
    filteredAnomalies.some(
      (a) => a.date === item.date && a.server_id === item.server_id
    )
  );

  const statusColor =
    storageData?.server_status === "critique"
      ? "status-critical"
      : storageData?.server_status === "chargé"
      ? "status-loaded"
      : "status-normal";

  if (!user) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h1>Storage Optimization AI</h1>

          <p className="subtitle">
            Connectez-vous pour accéder au dashboard intelligent.
          </p>

          <div className="auth-tabs">
            <button
              type="button"
              className={authMode === "login" ? "active-tab" : ""}
              onClick={() => {
                setAuthMode("login");
                setAuthMessage("");
              }}
            >
              Login
            </button>

            <button
              type="button"
              className={authMode === "register" ? "active-tab" : ""}
              onClick={() => {
                setAuthMode("register");
                setAuthMessage("");
              }}
            >
              Register
            </button>
          </div>

          <form
            onSubmit={authMode === "login" ? handleLogin : handleRegister}
            className="auth-form"
          >
            {authMode === "register" && (
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                minLength="3"
                required
              />
            )}

            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength="6"
              required
            />

            <button type="submit" className="auth-button">
              {authMode === "login" ? "Se connecter" : "Créer un compte"}
            </button>
          </form>

          {authMessage && <p className="auth-message">{authMessage}</p>}
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="dashboard">
        <h1>Storage Optimization Dashboard</h1>
        <p>Chargement des données...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="topbar">
        <div>
          <h1>Storage Optimization Dashboard</h1>
          <p className="subtitle">
            Optimisation dynamique des ressources de stockage avec Machine
            Learning
          </p>
        </div>

        <div className="user-box">
          <span>{user.username}</span>
          <button type="button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      <div className="section">
        <h2>Filtrer par serveur</h2>

        <select
          className="server-select"
          value={selectedServer}
          onChange={(e) => setSelectedServer(e.target.value)}
        >
          <option value="all">Tous les serveurs</option>

          {serverList.map((server) => (
            <option key={server} value={server}>
              {server}
            </option>
          ))}
        </select>
      </div>

      {storageData && (
        <>
          <div className="cards">
            <div className="card">
              <h2>Serveur actuel</h2>
              <p>{storageData.server_id}</p>
            </div>

            <div className="card">
              <h2>Total Storage</h2>
              <p>{storageData.total_storage} GB</p>
            </div>

            <div className="card">
              <h2>Used Storage</h2>
              <p>{storageData.used_storage} GB</p>
            </div>

            <div className="card">
              <h2>Free Storage</h2>
              <p>{storageData.free_storage} GB</p>
            </div>

            <div className="card">
              <h2>Usage</h2>
              <p>{storageData.usage_percentage}%</p>
            </div>

            <div className="card">
              <h2>CPU Usage</h2>
              <p>{storageData.cpu_usage}%</p>
            </div>

            <div className="card">
              <h2>Memory Usage</h2>
              <p>{storageData.memory_usage}%</p>
            </div>

            <div className="card">
              <h2>I/O Activity</h2>
              <p>
                R:{storageData.read_frequency} / W:
                {storageData.write_frequency}
              </p>
            </div>
          </div>

          <div className="section">
            <h2>État actuel du serveur</h2>
            <p>
              Serveur : <strong>{storageData.server_id}</strong>
            </p>
            <p>
              Date : <strong>{storageData.date}</strong>
            </p>
            <p>
              Statut :{" "}
              <span className={`status-badge ${statusColor}`}>
                {storageData.server_status}
              </span>
            </p>
          </div>

          <div className="alert-box">
            <h2>Alerte</h2>
            <p>{storageData.alert}</p>
          </div>

          <div className="recommendation-box">
            <h2>Recommandation</h2>
            <p>{storageData.recommendation}</p>
          </div>
        </>
      )}

      {filteredPredictions.length > 0 && (
        <div className="prediction-box">
          <h2>Prédictions IA par serveur</h2>

          <table>
            <thead>
              <tr>
                <th>Serveur</th>
                <th>Prediction GB</th>
                <th>Usage prévu</th>
                <th>Statut prévu</th>
                <th>Recommandation</th>
              </tr>
            </thead>

            <tbody>
              {filteredPredictions.map((item, index) => (
                <tr key={index}>
                  <td>{item.server_id}</td>
                  <td>{item.next_day_prediction} GB</td>
                  <td>{item.predicted_usage_percentage}%</td>
                  <td>{item.predicted_status}</td>
                  <td>{item.recommendation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {statistics && (
        <div className="section">
          <h2>Statistiques globales</h2>

          <div className="cards">
            <div className="card">
              <h2>Total Servers</h2>
              <p>{statistics.total_servers}</p>
            </div>

            <div className="card">
              <h2>Total Records</h2>
              <p>{statistics.total_records}</p>
            </div>

            <div className="card">
              <h2>Average Usage</h2>
              <p>{statistics.average_usage_percentage}%</p>
            </div>

            <div className="card">
              <h2>Average CPU</h2>
              <p>{statistics.average_cpu_usage}%</p>
            </div>

            <div className="card">
              <h2>Average Memory</h2>
              <p>{statistics.average_memory_usage}%</p>
            </div>

            <div className="card">
              <h2>Critical Cases</h2>
              <p>{statistics.critical_servers}</p>
            </div>

            <div className="card">
              <h2>Loaded Cases</h2>
              <p>{statistics.loaded_servers}</p>
            </div>

            <div className="card">
              <h2>Normal Cases</h2>
              <p>{statistics.normal_servers}</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={[
                { name: "Normal", value: statistics.normal_servers },
                { name: "Chargé", value: statistics.loaded_servers },
                { name: "Critique", value: statistics.critical_servers },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="chart-box">
        <h2>
          Évolution du stockage{" "}
          {selectedServer === "all"
            ? "de tous les serveurs"
            : `du serveur ${selectedServer}`}
        </h2>

        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={filteredHistory}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />

            <Line
              type="monotone"
              dataKey="used_storage"
              stroke="#2563eb"
              strokeWidth={3}
            />

            <Scatter data={anomalyPoints} dataKey="used_storage" fill="red" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {filteredAlerts.length > 0 && (
        <div className="section">
          <h2>Alertes générées</h2>

          <table>
            <thead>
              <tr>
                <th>Serveur</th>
                <th>Date</th>
                <th>Usage</th>
                <th>CPU</th>
                <th>Memory</th>
                <th>Statut</th>
                <th>Alerte</th>
              </tr>
            </thead>

            <tbody>
              {filteredAlerts.map((item, index) => (
                <tr key={index}>
                  <td>{item.server_id}</td>
                  <td>{item.date}</td>
                  <td>{item.usage_percentage}%</td>
                  <td>{item.cpu_usage}%</td>
                  <td>{item.memory_usage}%</td>
                  <td>{item.server_status}</td>
                  <td>{item.alert}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {filteredAnomalies.length > 0 && (
        <div className="anomaly-box">
          <h2>Anomalies détectées</h2>

          {filteredAnomalies.map((item, index) => (
            <div key={index} className="anomaly-item">
              <p>
                <strong>Serveur :</strong> {item.server_id}
              </p>

              <p>
                <strong>Date :</strong> {item.date}
              </p>

              <p>
                <strong>Used Storage :</strong> {item.used_storage} GB
              </p>

              <p>
                <strong>Usage :</strong> {item.usage_percentage}%
              </p>

              <p>
                <strong>CPU :</strong> {item.cpu_usage}%
              </p>

              <p>
                <strong>Memory :</strong> {item.memory_usage}%
              </p>

              <p>
                <strong>Read / Write :</strong> {item.read_frequency} /{" "}
                {item.write_frequency}
              </p>

              <p>
                <strong>Recommandation :</strong> {item.recommendation}
              </p>
            </div>
          ))}
        </div>
      )}

      {filteredRecommendations.length > 0 && (
        <div className="section">
          <h2>Recommandations d’optimisation</h2>

          <table>
            <thead>
              <tr>
                <th>Serveur</th>
                <th>Date</th>
                <th>Usage</th>
                <th>Statut</th>
                <th>Recommandation</th>
              </tr>
            </thead>

            <tbody>
              {filteredRecommendations.map((item, index) => (
                <tr key={index}>
                  <td>{item.server_id}</td>
                  <td>{item.date}</td>
                  <td>{item.usage_percentage}%</td>
                  <td>{item.server_status}</td>
                  <td>{item.recommendation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {filteredHistory.length > 0 && (
        <div className="section">
          <h2>Historique des serveurs</h2>

          <table>
            <thead>
              <tr>
                <th>Serveur</th>
                <th>Date</th>
                <th>Total</th>
                <th>Used</th>
                <th>Free</th>
                <th>CPU</th>
                <th>Memory</th>
                <th>Read</th>
                <th>Write</th>
                <th>Statut</th>
              </tr>
            </thead>

            <tbody>
              {filteredHistory.map((item, index) => (
                <tr key={index}>
                  <td>{item.server_id}</td>
                  <td>{item.date}</td>
                  <td>{item.total_storage}</td>
                  <td>{item.used_storage}</td>
                  <td>{item.free_storage}</td>
                  <td>{item.cpu_usage}%</td>
                  <td>{item.memory_usage}%</td>
                  <td>{item.read_frequency}</td>
                  <td>{item.write_frequency}</td>
                  <td>{item.server_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {report && (
        <div className="report-box">
          <h2>Rapport résumé</h2>

          <p>
            <strong>Projet :</strong> {report.project_name}
          </p>

          <p>
            <strong>Serveur actuel :</strong> {report.current_server}
          </p>

          <p>
            <strong>Date actuelle :</strong> {report.current_date}
          </p>

          <p>
            <strong>Usage actuel :</strong> {report.current_usage_percentage}%
          </p>

          <p>
            <strong>Statut actuel :</strong> {report.current_status}
          </p>

          <p>
            <strong>Total serveurs :</strong> {report.total_servers}
          </p>

          <p>
            <strong>Total alertes :</strong> {report.total_alerts}
          </p>

          <p>
            <strong>Cas critiques :</strong> {report.total_critical_cases}
          </p>

          <p>{report.summary}</p>
        </div>
      )}
    </div>
  );
}

export default App;