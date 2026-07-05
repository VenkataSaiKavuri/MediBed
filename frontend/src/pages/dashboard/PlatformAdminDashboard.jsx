import React, { useEffect, useState } from "react";
import client, { fraudAPI } from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

const TABS = [
  { key: "users", label: "Flagged Users" },
  { key: "bookings", label: "Suspicious Bookings" },
  { key: "documents", label: "Pending ID Reviews" },
];

export default function PlatformAdminDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("users");
  const [summary, setSummary] = useState(null);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actingOn, setActingOn] = useState(null);

  const loadSummary = () => {
    fraudAPI.summary().then(({ data }) => setSummary(data)).catch(() => {});
  };

  const loadTab = () => {
    setLoading(true);
    setError("");
    const call =
      activeTab === "users" ? fraudAPI.flaggedUsers()
      : activeTab === "bookings" ? fraudAPI.suspiciousBookings()
      : fraudAPI.pendingDocuments();

    call
      .then(({ data }) => setData(data.results || data))
      .catch(() => setError("Couldn't load this list."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadSummary(); }, []);
  useEffect(() => { loadTab(); }, [activeTab]);

  const refreshAll = () => { loadTab(); loadSummary(); };

  const handleUnflag = async (userId) => {
    setActingOn(userId);
    try {
      await fraudAPI.unflagUser(userId);
      refreshAll();
    } catch {
      alert("Couldn't unflag this user.");
    } finally {
      setActingOn(null);
    }
  };

  const handleClearBooking = async (bookingId) => {
    setActingOn(bookingId);
    try {
      await fraudAPI.clearBookingFlag(bookingId);
      refreshAll();
    } catch {
      alert("Couldn't clear this flag.");
    } finally {
      setActingOn(null);
    }
  };

  const handleReviewDocument = async (docId, action) => {
    setActingOn(docId);
    try {
      await fraudAPI.reviewDocument(docId, action);
      refreshAll();
    } catch {
      alert("Couldn't submit this review.");
    } finally {
      setActingOn(null);
    }
  };

  const handleViewDocument = async (downloadUrl) => {
    // A plain <a href> wouldn't carry the JWT Authorization header, so this fetches
    // through the authenticated axios client and opens the result as a blob instead.
    try {
      const response = await client.get(downloadUrl.replace("/api", ""), { responseType: "blob" });
      const blobUrl = window.URL.createObjectURL(response.data);
      window.open(blobUrl, "_blank");
    } catch {
      alert("Couldn't open this document.");
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", padding: "0 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div>
          <h1 style={{ margin: 0 }}>Fraud Review Dashboard</h1>
          <p style={{ color: "#666", margin: "4px 0 0" }}>Logged in as {user?.first_name || user?.username}</p>
        </div>
        <button onClick={logout} style={{ background: "none", border: "1px solid #ddd", borderRadius: 8, padding: "8px 14px", cursor: "pointer" }}>
          Log out
        </button>
      </div>

      <div style={{ display: "flex", gap: 8, margin: "20px 0", borderBottom: "1px solid #eee" }}>
        {TABS.map((tab) => {
          const count = summary && (
            tab.key === "users" ? summary.flagged_users_count
            : tab.key === "bookings" ? summary.suspicious_bookings_count
            : summary.pending_documents_count
          );
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: "8px 16px", border: "none", background: "none", cursor: "pointer",
                fontWeight: activeTab === tab.key ? 700 : 400,
                borderBottom: activeTab === tab.key ? "2px solid #2563eb" : "2px solid transparent",
                color: activeTab === tab.key ? "#2563eb" : "#666",
              }}
            >
              {tab.label} {count != null && `(${count})`}
            </button>
          );
        })}
      </div>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}
      {!loading && !error && data.length === 0 && <p style={{ color: "#666" }}>Nothing here right now.</p>}

      {/* --- Flagged Users tab --- */}
      {activeTab === "users" && data.map((u) => (
        <div key={u.id} style={cardStyle}>
          <div>
            <strong>{u.first_name || u.username}</strong>
            <span style={{ marginLeft: 8, fontSize: 12, color: "#999" }}>{u.phone_number}</span>
            <p style={{ margin: "4px 0 0", fontSize: 13, color: "#666" }}>
              Reputation: {u.reputation_score} · No-shows: {u.no_show_count}
            </p>
          </div>
          <button disabled={actingOn === u.id} onClick={() => handleUnflag(u.id)} style={approveBtnStyle}>
            Restore booking privileges
          </button>
        </div>
      ))}

      {/* --- Suspicious Bookings tab --- */}
      {activeTab === "bookings" && data.map((b) => (
        <div key={b.id} style={cardStyle}>
          <div>
            <strong>{b.patient_name}</strong>
            <span style={{ marginLeft: 8, fontSize: 12, color: "#999" }}>{b.hospital_name} — {b.bed_type}</span>
            <p style={{ margin: "4px 0 0", fontSize: 13, color: "#b91c1c" }}>
              {(b.fraud_flags || []).join("; ")}
            </p>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "#999" }}>
              Device: {b.device_id || "—"} · IP: {b.ip_address || "—"}
            </p>
          </div>
          <button disabled={actingOn === b.id} onClick={() => handleClearBooking(b.id)} style={approveBtnStyle}>
            Mark as legitimate
          </button>
        </div>
      ))}

      {/* --- Pending ID Reviews tab --- */}
      {activeTab === "documents" && data.map((d) => (
        <div key={d.id} style={cardStyle}>
          <div>
            <strong>{d.patient_name}</strong>
            <span style={{ marginLeft: 8, fontSize: 12, color: "#999" }}>{d.patient_phone}</span>
            <p style={{ margin: "4px 0 0", fontSize: 13 }}>
              {d.document_type} — typed name: "<strong>{d.name_on_document}</strong>"
            </p>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "#d97706" }}>
              Match: {d.name_match_result.replace("_", " ")} (score {d.name_match_score.toFixed(2)})
            </p>
            <button
              onClick={() => handleViewDocument(d.download_url)}
              style={{ fontSize: 12, background: "none", border: "none", color: "#2563eb", cursor: "pointer", padding: 0, textDecoration: "underline" }}
            >
              View document
            </button>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button disabled={actingOn === d.id} onClick={() => handleReviewDocument(d.id, "approve")} style={approveBtnStyle}>
              Approve
            </button>
            <button disabled={actingOn === d.id} onClick={() => handleReviewDocument(d.id, "reject")} style={rejectBtnStyle}>
              Reject
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

const cardStyle = {
  padding: 16, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
  marginBottom: 12, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12,
};
const approveBtnStyle = {
  padding: "8px 14px", background: "#16a34a", color: "white", border: "none",
  borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap",
};
const rejectBtnStyle = {
  padding: "8px 14px", background: "white", color: "#dc2626", border: "1px solid #fecaca",
  borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer",
};
