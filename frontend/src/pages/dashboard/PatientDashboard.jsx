import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { hospitalsAPI } from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

const BED_TYPES = ["", "general", "icu", "ventilator", "maternity", "emergency"];

export default function PatientDashboard() {
  const { user, logout } = useAuth();
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [bedType, setBedType] = useState("");
  const [specialty, setSpecialty] = useState("");

  const runSearch = () => {
    setLoading(true);
    setError("");
    const params = {};
    if (search) params.search = search;
    if (city) params.city = city;
    if (bedType) params.bed_type = bedType;
    if (specialty) params.specialty = specialty;

    hospitalsAPI
      .list(params)
      .then(({ data }) => setHospitals(data))
      .catch(() => setError("Couldn't load hospitals."))
      .finally(() => setLoading(false));
  };

  // Initial load
  useEffect(() => {
    runSearch();
  }, []);

  // Debounced re-search whenever filters change
  useEffect(() => {
    const timer = setTimeout(runSearch, 400);
    return () => clearTimeout(timer);
  }, [search, city, bedType, specialty]);

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

      {/* Search + filters */}
      <div style={{ background: "white", padding: 16, borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)", marginBottom: 20 }}>
        <input
          placeholder="Search hospital name or city..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: "100%", padding: 10, border: "1px solid #d7dbe0", borderRadius: 8, fontSize: 14, marginBottom: 10 }}
        />
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            placeholder="City"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            style={{ flex: 1, minWidth: 120, padding: 8, border: "1px solid #d7dbe0", borderRadius: 8, fontSize: 13 }}
          />
          <select value={bedType} onChange={(e) => setBedType(e.target.value)} style={{ padding: 8, borderRadius: 8, border: "1px solid #d7dbe0", fontSize: 13 }}>
            <option value="">Any bed type</option>
            {BED_TYPES.filter(Boolean).map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input
            placeholder="Specialty (e.g. cardiology)"
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            style={{ flex: 1, minWidth: 140, padding: 8, border: "1px solid #d7dbe0", borderRadius: 8, fontSize: 13 }}
          />
        </div>
      </div>

      <h2 style={{ fontSize: 18 }}>{loading ? "Searching..." : `${hospitals.length} hospital${hospitals.length === 1 ? "" : "s"} found`}</h2>
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}
      {!loading && !error && hospitals.length === 0 && (
        <p style={{ color: "#666" }}>No hospitals match your filters. Try broadening your search.</p>
      )}

      <div style={{ display: "grid", gap: 12 }}>
        {hospitals.map((h) => (
          <Link key={h.id} to={`/hospitals/${h.id}`} style={{ textDecoration: "none", color: "inherit" }}>
            <div style={{ padding: 16, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
              <strong>{h.name}</strong>
              <p style={{ margin: "4px 0 8px", color: "#666", fontSize: 14 }}>{h.address}, {h.city}</p>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {Object.entries(h.available_beds || {}).map(([type, count]) => (
                  <span key={type} style={{
                    fontSize: 12, padding: "3px 8px", borderRadius: 12,
                    background: count > 0 ? "#dcfce7" : "#f3f4f6",
                    color: count > 0 ? "#166534" : "#999",
                  }}>
                    {type}: {count}
                  </span>
                ))}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
