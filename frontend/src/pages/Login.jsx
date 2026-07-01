import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authAPI } from "../api/client";

// Decode JWT payload without extra dependencies
function decodeJwt(token) {
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch {
    return null;
  }
}

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await authAPI.login(username, password);
      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);

      const payload = decodeJwt(data.access);
      // Day 3 will build the actual dashboard routes — for now just log the role we got back
      console.log("Logged in as role:", payload?.role);

      if (payload?.role === "hospital_admin") {
        navigate("/dashboard/hospital-admin");
      } else if (payload?.role === "platform_admin") {
        navigate("/dashboard/platform-admin");
      } else {
        navigate("/dashboard/patient");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid username or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="emergency-banner">🚨 Medical emergency? Emergency booking will be enabled after Day 21.</div>

      <h1>Log in</h1>
      <p className="subtitle">Welcome back to MedBeds.</p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>

        {error && <p className="error-text">{error}</p>}

        <button className="primary-btn" type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Log in"}
        </button>
      </form>

      <p className="switch-link">
        New here? <Link to="/signup">Create an account</Link>
      </p>
    </div>
  );
}
