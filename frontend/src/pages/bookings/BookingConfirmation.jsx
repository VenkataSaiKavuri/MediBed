import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { bookingsAPI } from "../../api/client";

const STATUS_LABELS = {
  requested: { label: "Awaiting hospital confirmation", color: "#d97706", bg: "#fef3c7" },
  confirmed: { label: "Confirmed", color: "#16a34a", bg: "#dcfce7" },
  rejected: { label: "Rejected by hospital", color: "#dc2626", bg: "#fef2f2" },
  completed: { label: "Completed", color: "#2563eb", bg: "#dbeafe" },
  cancelled: { label: "Cancelled", color: "#666", bg: "#f3f4f6" },
  no_show: { label: "Marked as no-show", color: "#dc2626", bg: "#fef2f2" },
  escalated: { label: "Escalated to another hospital", color: "#d97706", bg: "#fef3c7" },
};

export default function BookingConfirmation() {
  const { id } = useParams();
  const [booking, setBooking] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  const load = () => {
    bookingsAPI
      .detail(id)
      .then(({ data }) => setBooking(data))
      .catch(() => setError("Couldn't load this booking."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [id]);

  const handleCancel = async () => {
    if (!confirm("Cancel this booking request?")) return;
    setCancelling(true);
    try {
      await bookingsAPI.transition(id, "cancelled");
      load();
    } catch {
      alert("Couldn't cancel this booking.");
    } finally {
      setCancelling(false);
    }
  };

  if (loading) return <p style={{ textAlign: "center", marginTop: 80 }}>Loading...</p>;
  if (error || !booking) return <p style={{ textAlign: "center", marginTop: 80, color: "#dc2626" }}>{error}</p>;

  const statusInfo = STATUS_LABELS[booking.status] || { label: booking.status, color: "#333", bg: "#f3f4f6" };
  const canCancel = ["requested", "confirmed"].includes(booking.status);

  return (
    <div className="auth-container" style={{ maxWidth: 480, textAlign: "center" }}>
      <div style={{ fontSize: 40, marginBottom: 8 }}>
        {booking.status === "requested" ? "⏳" : booking.status === "confirmed" ? "✅" : booking.status === "rejected" ? "❌" : "📋"}
      </div>
      <h1 style={{ fontSize: 20, marginBottom: 4 }}>Booking Request Sent</h1>
      <p className="subtitle">{booking.hospital_name}</p>

      <span style={{
        display: "inline-block", padding: "6px 14px", borderRadius: 20, fontSize: 13, fontWeight: 700,
        background: statusInfo.bg, color: statusInfo.color, marginBottom: 20,
      }}>
        {statusInfo.label}
      </span>

      <div style={{ textAlign: "left", background: "#f9fafb", borderRadius: 10, padding: 16, marginBottom: 20 }}>
        <Row label="Bed type" value={booking.bed_type} />
        {booking.doctor_name && <Row label="Doctor" value={booking.doctor_name} />}
        {booking.scheduled_time && <Row label="Scheduled" value={new Date(booking.scheduled_time).toLocaleString()} />}
        {booking.condition_category && <Row label="Reason" value={booking.condition_category} />}
        <Row label="Requested" value={new Date(booking.created_at).toLocaleString()} />
      </div>

      {canCancel && (
        <button
          onClick={handleCancel}
          disabled={cancelling}
          style={{ width: "100%", padding: 12, background: "white", border: "1px solid #fecaca", color: "#dc2626", borderRadius: 8, fontWeight: 600, cursor: "pointer", marginBottom: 12 }}
        >
          {cancelling ? "Cancelling..." : "Cancel this booking"}
        </button>
      )}

      <Link to="/dashboard/patient" style={{ display: "block", fontSize: 14, color: "#2563eb", textDecoration: "none" }}>
        ← Back to dashboard
      </Link>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #eee", fontSize: 14 }}>
      <span style={{ color: "#666" }}>{label}</span>
      <span style={{ fontWeight: 600, textTransform: "capitalize" }}>{value}</span>
    </div>
  );
}
