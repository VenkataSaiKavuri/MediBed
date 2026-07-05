import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { hospitalsAPI } from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

const BED_TYPES = ["", "general", "icu", "ventilator", "maternity", "emergency"];
const SORT_OPTIONS = [
  { value: "name", label: "Name (A–Z)" },
  { value: "-name", label: "Name (Z–A)" },
  { value: "city", label: "City (A–Z)" },
  { value: "-updated_at", label: "Recently updated" },
];

export default function PatientDashboard() {
  const { user, logout } = useAuth();
  const [hospitals, setHospitals] = useState([]);
  const [count, setCount] = useState(0);
  const [nextUrl, setNextUrl] = useState(null);
  const [prevUrl, setPrevUrl] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [bedType, setBedType] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [ordering, setOrdering] = useState("name");

  const runSearch = (targetPage = 1) => {
    setLoading(true);
    setError("");
    const params = { page: targetPage, ordering };
    if (search) params.search = search;
    if (city) params.city = city;
    if (bedType) params.bed_type = bedType;
    if (specialty) params.specialty = specialty;

    hospitalsAPI
      .list(params)
      .then(({ data }) => {
        setHospitals(data.results);
        setCount(data.count);
        setNextUrl(data.next);
        setPrevUrl(data.previous);
        setPage(targetPage);
      })
      .catch(() => setError("Couldn't load hospitals."))
      .finally(() => setLoading(false));
  };

  // Initial load
  useEffect(() => {
    runSearch(1);
  }, []);

  // Debounced re-search whenever filters/sort change — always resets to page 1
  useEffect(() => {
    const timer = setTimeout(() => runSearch(1), 400);
    return () => clearTimeout(timer);
  }, [search, city, bedType, specialty, ordering]);

  const totalPages = Math.max(1, Math.ceil(count / 10)); // PAGE_SIZE=10 set in backend settings

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

      {user?.is_flagged && (
        <div style={{ padding: 12, background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, color: "#b91c1c", fontSize: 13, marginBottom: 16 }}>
          ⚠ Your account has restricted booking privileges due to repeated no-shows or late
          cancellations. Please call hospitals directly, or contact support to restore instant booking.
        </div>
      )}

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
          <select value={ordering} onChange={(e) => setOrdering(e.target.value)} style={{ padding: 8, borderRadius: 8, border: "1px solid #d7dbe0", fontSize: 13 }}>
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      <h2 style={{ fontSize: 18 }}>{loading ? "Searching..." : `${count} hospital${count === 1 ? "" : "s"} found`}</h2>
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}
      {!loading && !error && hospitals.length === 0 && (
        <p style={{ color: "#666" }}>No hospitals match your filters. Try broadening your search.</p>
      )}

      <div style={{ display: "grid", gap: 12, marginBottom: 20 }}>
        {hospitals.map((h) => (
          <Link key={h.id} to={`/hospitals/${h.id}`} style={{ textDecoration: "none", color: "inherit" }}>
            <div style={{ padding: 16, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
              <strong>{h.name}</strong>
              <p style={{ margin: "4px 0 8px", color: "#666", fontSize: 14 }}>{h.address}, {h.city}</p>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {Object.entries(h.available_beds || {}).map(([type, cnt]) => (
                  <span key={type} style={{
                    fontSize: 12, padding: "3px 8px", borderRadius: 12,
                    background: cnt > 0 ? "#dcfce7" : "#f3f4f6",
                    color: cnt > 0 ? "#166534" : "#999",
                  }}>
                    {type}: {cnt}
                  </span>
                ))}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Pagination controls */}
      {count > 0 && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 16 }}>
          <button
            disabled={!prevUrl}
            onClick={() => runSearch(page - 1)}
            style={{ ...pageBtnStyle, opacity: prevUrl ? 1 : 0.4, cursor: prevUrl ? "pointer" : "not-allowed" }}
          >
            ← Previous
          </button>
          <span style={{ fontSize: 13, color: "#666" }}>Page {page} of {totalPages}</span>
          <button
            disabled={!nextUrl}
            onClick={() => runSearch(page + 1)}
            style={{ ...pageBtnStyle, opacity: nextUrl ? 1 : 0.4, cursor: nextUrl ? "pointer" : "not-allowed" }}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

const pageBtnStyle = {
  padding: "8px 16px", background: "white", border: "1px solid #d7dbe0",
  borderRadius: 8, fontSize: 13, fontWeight: 600,
};
