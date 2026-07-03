import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { bookingsAPI, hospitalsAPI } from "../../api/client";

export default function BookingForm() {
  const { hospitalId } = useParams();
  const navigate = useNavigate();

  const [hospital, setHospital] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [bedType, setBedType] = useState("");
  const [doctorId, setDoctorId] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [conditionCategory, setConditionCategory] = useState("");

  useEffect(() => {
    hospitalsAPI
      .detail(hospitalId)
      .then(({ data }) => {
        setHospital(data);
        const firstAvailable = data.bed_inventory.find((b) => b.available_count > 0);
        if (firstAvailable) setBedType(firstAvailable.bed_type);
      })
      .catch(() => setError("Couldn't load hospital details."))
      .finally(() => setLoading(false));
  }, [hospitalId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const payload = {
        hospital: Number(hospitalId),
        bed_type: bedType,
        condition_category: conditionCategory,
      };
      if (doctorId) payload.doctor = Number(doctorId);
      if (scheduledTime) payload.scheduled_time = new Date(scheduledTime).toISOString();

      const { data } = await bookingsAPI.create(payload);
      if (!data.id) {
        setError("Booking was created but the server response was missing an ID. Check your booking history instead.");
        return;
      }
      navigate(`/bookings/${data.id}/confirmation`);
    } catch (err) {
      const data = err.response?.data;
      setError(data ? Object.values(data).flat().join(" ") : "Couldn't create booking. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p style={{ textAlign: "center", marginTop: 80 }}>Loading...</p>;
  if (!hospital) return <p style={{ textAlign: "center", marginTop: 80, color: "#dc2626" }}>{error}</p>;

  const availableBedTypes = hospital.bed_inventory.filter((b) => b.available_count > 0);
  const onDutyDoctors = hospital.doctors.filter((d) => d.is_on_duty);

  return (
    <div className="auth-container" style={{ maxWidth: 480 }}>
      <Link to={`/hospitals/${hospitalId}`} style={{ fontSize: 13, color: "#2563eb", textDecoration: "none" }}>
        ← Back to {hospital.name}
      </Link>

      <h1 style={{ fontSize: 20, marginTop: 12 }}>Book a bed</h1>
      <p className="subtitle">{hospital.name} — {hospital.city}</p>

      {availableBedTypes.length === 0 ? (
        <div style={{ padding: 14, background: "#fef2f2", borderRadius: 8, color: "#b91c1c", fontSize: 14 }}>
          No beds are currently available at this hospital. Try another hospital or check back later.
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Bed type</label>
            <select value={bedType} onChange={(e) => setBedType(e.target.value)} required>
              {availableBedTypes.map((b) => (
                <option key={b.id} value={b.bed_type}>
                  {b.bed_type} ({b.available_count} available)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Preferred doctor (optional)</label>
            <select value={doctorId} onChange={(e) => setDoctorId(e.target.value)}>
              <option value="">No preference</option>
              {onDutyDoctors.map((d) => (
                <option key={d.id} value={d.id}>{d.name} — {d.specialty}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Preferred date/time (optional)</label>
            <input type="datetime-local" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} />
          </div>

          <div className="form-group">
            <label>Reason / condition (optional)</label>
            <input
              placeholder="e.g. post-surgery recovery"
              value={conditionCategory}
              onChange={(e) => setConditionCategory(e.target.value)}
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <p style={{ fontSize: 12, color: "#999", marginTop: -6, marginBottom: 14 }}>
            This sends a booking request — the hospital must confirm before it's finalized.
            A refundable hold/deposit will apply once payments are wired up (Day 13).
          </p>

          <button className="primary-btn" type="submit" disabled={submitting}>
            {submitting ? "Submitting request..." : "Request Booking"}
          </button>
        </form>
      )}
    </div>
  );
}
