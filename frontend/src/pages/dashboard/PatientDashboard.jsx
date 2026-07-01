import React, { useEffect, useState } from "react";
import { hospitalsAPI } from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

export default function PatientDashboard() {
  const { user, logout } = useAuth();
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    hospitalsAPI
      .list()
      .then(({ data }) => setHospitals(data))
      .catch(() => setError("Couldn't load hospitals."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0 }}>Hi, {user?.first_name || user?.username}</h1>
          <p style={{ color: "#666", margin: "4px 0 0" }}>Find and book a hospital bed.</p>
        </div>
        <button onClick={logout} style={{ background: "none", border: "1px solid #ddd", borderRadius: 8, padding: "8px 14px", cursor: "pointer" }}>
          Log out
        </button>
      </div>

      {/* Emergency booking button — wired up on Day 21 */}
      <button
        style={{
          width: "100%", padding: 16, background: "#dc2626", color: "white",
          border: "none", borderRadius: 10, fontSize: 16, fontWeight: 700,
          marginBottom: 28, cursor: "pointer",
        }}
        onClick={() => alert("Emergency booking flow arrives on Day 21.")}
      >
        🚨 Emergency Booking
      </button>

      <h2 style={{ fontSize: 18 }}>Nearby Hospitals</h2>
      {loading && <p>Loading hospitals...</p>}
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}
      {!loading && !error && hospitals.length === 0 && (
        <p style={{ color: "#666" }}>No verified hospitals yet — add one via Django admin to see it here.</p>
      )}

      <div style={{ display: "grid", gap: 12 }}>
        {hospitals.map((h) => (
          <div key={h.id} style={{ padding: 16, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
            <strong>{h.name}</strong>
            <p style={{ margin: "4px 0 0", color: "#666", fontSize: 14 }}>{h.address}, {h.city}</p>
            {/* Search filters (bed type, specialty) and a real "Book" button come in Day 5 & 9 */}
          </div>
        ))}
      </div>
    </div>
  );
}
