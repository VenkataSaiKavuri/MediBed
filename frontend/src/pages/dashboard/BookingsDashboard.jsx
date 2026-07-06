import React, { useEffect, useRef, useState } from "react";
import { bookingsAPI } from "../../api/client";

const STATUS_TABS = [
  { value: "requested", label: "Pending" },
  { value: "confirmed", label: "Confirmed" },
  { value: "completed", label: "Completed" },
  { value: "", label: "All" },
];

const EMERGENCY_POLL_INTERVAL_MS = 15000; // check for new emergencies every 15s — no websockets yet,
                                            // this is the pragmatic stand-in until real-time push exists

function playAlertBeep() {
  // Self-contained beep via Web Audio API — no external sound file needed.
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.connect(gain);
    gain.connect(ctx.destination);
    oscillator.frequency.value = 880;
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.3);
  } catch {
    // Audio can fail silently (e.g. browser blocks autoplay before any user interaction) —
    // the visual banner below is the primary alert either way, sound is a bonus.
  }
}

function SlaCountdown({ deadline, urgent }) {
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
    const interval = setInterval(tick, urgent ? 10000 : 30000); // tighter refresh for emergencies
    return () => clearInterval(interval);
  }, [deadline, urgent]);

  if (!deadline) return null;
  const expired = remaining === "SLA expired";
  return (
    <span
      style={{
        fontSize: 12, fontWeight: 700,
        color: expired ? "#dc2626" : urgent ? "#dc2626" : "#d97706",
        animation: urgent && !expired ? "pulse-text 1.5s infinite" : "none",
      }}
    >
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
  const [pendingEmergencies, setPendingEmergencies] = useState([]);
  const previousEmergencyCount = useRef(0);
  const originalTitle = useRef(document.title);

  const load = () => {
    setLoading(true);
    bookingsAPI
      .hospitalList(activeTab || undefined)
      .then(({ data }) => setBookings(data.results || data)) // handles paginated or plain array
      .catch(() => setError("Couldn't load bookings."))
      .finally(() => setLoading(false));
  };

  // Independent poll for pending emergencies, regardless of which tab is open — this is
  // what makes the alert feel "instant" without needing websockets/real-time push. Runs
  // every 15s; if the count goes UP since last check, that means a brand-new emergency
  // request just landed, so we beep and flash the browser tab title to grab attention.
  const pollEmergencies = () => {
    bookingsAPI
      .hospitalList("requested", true)
      .then(({ data }) => {
        const results = data.results || data;
        if (results.length > previousEmergencyCount.current) {
          playAlertBeep();
          document.title = "🚨 NEW EMERGENCY — MedBeds";
        }
        previousEmergencyCount.current = results.length;
        setPendingEmergencies(results);
      })
      .catch(() => {});
  };

  useEffect(() => {
    load();
  }, [activeTab]);

  useEffect(() => {
    pollEmergencies();
    const interval = setInterval(pollEmergencies, EMERGENCY_POLL_INTERVAL_MS);
    return () => {
      clearInterval(interval);
      document.title = originalTitle.current;
    };
  }, []);

  // Clear the flashing title once the admin actually looks at the tab
  useEffect(() => {
    const handleFocus = () => { document.title = originalTitle.current; };
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  const act = async (bookingId, status) => {
    setActingOn(bookingId);
    try {
      await bookingsAPI.transition(bookingId, status);
      load();
      pollEmergencies();
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

      {pendingEmergencies.length > 0 && (
        <div
          onClick={() => setActiveTab("requested")}
          style={{
            padding: "14px 18px", background: "#dc2626", color: "white", borderRadius: 12,
            marginBottom: 20, cursor: "pointer", animation: "pulse-bg 1.5s infinite",
            display: "flex", justifyContent: "space-between", alignItems: "center",
          }}
        >
          <span style={{ fontWeight: 700 }}>
            🚨 {pendingEmergencies.length} emergency request{pendingEmergencies.length === 1 ? "" : "s"} awaiting response!
          </span>
          <span style={{ fontSize: 13, textDecoration: "underline" }}>View →</span>
        </div>
      )}

      <style>{`
        @keyframes pulse-bg {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.75; }
        }
        @keyframes pulse-text {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>

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
                {b.is_emergency && (
                  <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 800, padding: "2px 8px", borderRadius: 10, background: "#dc2626", color: "white" }}>
                    🚨 EMERGENCY
                  </span>
                )}
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
                {b.status === "requested" && <div style={{ marginTop: 6 }}><SlaCountdown deadline={b.sla_deadline} urgent={b.is_emergency} /></div>}
                {b.status === "requested" && Number(b.deposit_amount) > 0 && (
                  <div style={{ marginTop: 4, fontSize: 11, fontWeight: 700, color: b.deposit_paid ? "#16a34a" : "#dc2626" }}>
                    {b.deposit_paid ? "✓ Deposit paid" : "⚠ Deposit not paid"}
                  </div>
                )}
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
