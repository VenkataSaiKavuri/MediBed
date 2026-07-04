import React, { useEffect, useState } from "react";
import { bookingsAPI } from "../../api/client";

const STATUS_TABS = [
  { value: "requested", label: "Pending" },
  { value: "confirmed", label: "Confirmed" },
  { value: "completed", label: "Completed" },
  { value: "", label: "All" },
];

function SlaCountdown({ deadline }) {
  const [remaining, setRemaining] = useState("");

  useEffect(() => {
    if (!deadline) return;
    const tick = () => {
      const diffMs = new Date(deadline) - new Date();
      if (diffMs <= 0) {
        setRemaining("SLA expired");
        return;
      }
      const mins = Math.floor(diffMs / 60000);
      const hrs = Math.floor(mins / 60);
      setRemaining(hrs > 0 ? `${hrs}h ${mins % 60}m left` : `${mins}m left`);
    };
    tick();
    const interval = setInterval(tick, 30000);
    return () => clearInterval(interval);
  }, [deadline]);

  if (!deadline) return null;
  const expired = remaining === "SLA expired";
  return (
    <span style={{ fontSize: 12, fontWeight: 700, color: expired ? "#dc2626" : "#d97706" }}>
      ⏱ {remaining}
    </span>
  );
}

export default function BookingsDashboard() {
  const [bookings, setBookings] = useState([]);
  const [activeTab, setActiveTab] = useState("requested");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actingOn, setActingOn] = useState(null);

  const load = () => {
    setLoading(true);
    bookingsAPI
      .hospitalList(activeTab || undefined)
      .then(({ data }) => setBookings(data.results || data)) // handles paginated or plain array
      .catch(() => setError("Couldn't load bookings."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [activeTab]);

  const act = async (bookingId, status) => {
    setActingOn(bookingId);
    try {
      await bookingsAPI.transition(bookingId, status);
      load();
    } catch (err) {
      const message = err.response?.data?.detail || "Action failed.";
      alert(message); // e.g. "No 'icu' beds currently available at this hospital." (409 Conflict)
    } finally {
      setActingOn(null);
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", padding: "0 20px" }}>
      <h1 style={{ marginBottom: 4 }}>Bookings</h1>
      <p style={{ color: "#666", marginTop: 0, marginBottom: 20 }}>
        Manage incoming requests for your hospital.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 20, borderBottom: "1px solid #eee" }}>
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setActiveTab(tab.value)}
            style={{
              padding: "8px 16px", border: "none", background: "none", cursor: "pointer",
              fontWeight: activeTab === tab.value ? 700 : 400,
              borderBottom: activeTab === tab.value ? "2px solid #2563eb" : "2px solid transparent",
              color: activeTab === tab.value ? "#2563eb" : "#666",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}
      {!loading && !error && bookings.length === 0 && (
        <p style={{ color: "#666" }}>No bookings in this category.</p>
      )}

      <div style={{ display: "grid", gap: 12 }}>
        {bookings.map((b) => (
          <div key={b.id} style={{ padding: 16, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
              <div>
                <strong>{b.patient_name || "Unnamed patient"}</strong>
                <span style={{ marginLeft: 8, fontSize: 12, color: "#999" }}>{b.patient_phone}</span>
                <p style={{ margin: "4px 0", fontSize: 14, textTransform: "capitalize" }}>
                  {b.bed_type} bed
                  {b.doctor_name && <> — Dr. {b.doctor_name}</>}
                  {b.condition_category && <> — {b.condition_category}</>}
                </p>
                <p style={{ margin: 0, fontSize: 12, color: "#999" }}>
                  Requested {new Date(b.created_at).toLocaleString()}
                </p>
              </div>
              <div style={{ textAlign: "right" }}>
                <span style={statusBadgeStyle(b.status)}>{b.status.replace("_", " ")}</span>
                {b.status === "requested" && <div style={{ marginTop: 6 }}><SlaCountdown deadline={b.sla_deadline} /></div>}
              </div>
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              {b.status === "requested" && (
                <>
                  <button disabled={actingOn === b.id} onClick={() => act(b.id, "confirmed")} style={acceptBtnStyle}>
                    ✓ Confirm
                  </button>
                  <button disabled={actingOn === b.id} onClick={() => act(b.id, "rejected")} style={rejectBtnStyle}>
                    ✕ Reject
                  </button>
                </>
              )}
              {b.status === "confirmed" && (
                <>
                  <button disabled={actingOn === b.id} onClick={() => act(b.id, "completed")} style={acceptBtnStyle}>
                    ✓ Mark Completed
                  </button>
                  <button disabled={actingOn === b.id} onClick={() => act(b.id, "no_show")} style={rejectBtnStyle}>
                    Mark No-show
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function statusBadgeStyle(status) {
  const map = {
    requested: { bg: "#fef3c7", color: "#d97706" },
    confirmed: { bg: "#dcfce7", color: "#16a34a" },
    rejected: { bg: "#fef2f2", color: "#dc2626" },
    completed: { bg: "#dbeafe", color: "#2563eb" },
    cancelled: { bg: "#f3f4f6", color: "#666" },
    no_show: { bg: "#fef2f2", color: "#dc2626" },
  };
  const s = map[status] || { bg: "#f3f4f6", color: "#333" };
  return {
    display: "inline-block", padding: "4px 10px", borderRadius: 12, fontSize: 12,
    fontWeight: 700, background: s.bg, color: s.color, textTransform: "capitalize",
  };
}

const acceptBtnStyle = {
  padding: "8px 14px", background: "#16a34a", color: "white", border: "none",
  borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer",
};
const rejectBtnStyle = {
  padding: "8px 14px", background: "white", color: "#dc2626", border: "1px solid #fecaca",
  borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer",
};
