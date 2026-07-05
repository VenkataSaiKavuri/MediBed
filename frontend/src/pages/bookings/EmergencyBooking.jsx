import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { bookingsAPI, hospitalsAPI } from "../../api/client";

const CONDITIONS = [
  { value: "cardiac", label: "🫀 Cardiac", },
  { value: "trauma", label: "🩹 Trauma / Accident" },
  { value: "respiratory", label: "🫁 Breathing Difficulty" },
  { value: "maternity", label: "🤰 Maternity" },
  { value: "other", label: "❗ Other Emergency" },
];

const BED_TYPES = ["emergency", "icu", "ventilator", "general", "maternity"];

export default function EmergencyBooking() {
  const navigate = useNavigate();
  const [condition, setCondition] = useState("");
  const [bedType, setBedType] = useState("emergency");
  const [hospitals, setHospitals] = useState([]);
  const [hospitalId, setHospitalId] = useState("");
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // Capture location immediately on page load — no reason to wait for the user to tap
    // anything else first, since every second matters here.
    if (!navigator.geolocation) {
      setLocationError("Your browser doesn't support location — you can still continue without it.");
    } else {
      navigator.geolocation.getCurrentPosition(
        (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => setLocationError("Couldn't get your location — you can still continue without it."),
        { enableHighAccuracy: true, timeout: 8000 }
      );
    }

    // Day 22 will replace this with real nearest-hospital matching by distance. For now,
    // just load verified hospitals so there's at least something to pick from.
    hospitalsAPI
      .list({ ordering: "name" })
      .then(({ data }) => setHospitals(data.results || data))
      .catch(() => {});
  }, []);

  const handleSubmit = async () => {
    if (!condition) {
      setError("Please select what's happening.");
      return;
    }
    if (!hospitalId) {
      setError("Please select a hospital.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const payload = {
        hospital: Number(hospitalId),
        bed_type: bedType,
        condition_category: condition,
      };
      if (location) {
        payload.patient_latitude = location.lat;
        payload.patient_longitude = location.lng;
      }
      const { data } = await bookingsAPI.createEmergency(payload);
      navigate(`/bookings/${data.id}/confirmation`);
    } catch (err) {
      const data = err.response?.data;
      setError(data ? Object.values(data).flat().join(" ") : "Couldn't submit emergency request. Please call the hospital directly.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 480, margin: "24px auto", padding: "0 20px" }}>
      <div style={{ background: "#dc2626", color: "white", padding: "16px 20px", borderRadius: 14, marginBottom: 20, textAlign: "center" }}>
        <div style={{ fontSize: 28, marginBottom: 4 }}>🚨</div>
        <h1 style={{ margin: 0, fontSize: 20 }}>Emergency Booking</h1>
        <p style={{ margin: "4px 0 0", fontSize: 13, opacity: 0.9 }}>
          This skips the usual checks to get you help faster.
        </p>
      </div>

      <div style={{ background: "white", borderRadius: 14, padding: 20, boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
        <label style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, display: "block" }}>
          What's happening?
        </label>
        <div style={{ display: "grid", gap: 8, marginBottom: 20 }}>
          {CONDITIONS.map((c) => (
            <button
              key={c.value}
              onClick={() => setCondition(c.value)}
              style={{
                padding: 14, borderRadius: 10, textAlign: "left", fontSize: 15, cursor: "pointer",
                border: condition === c.value ? "2px solid #dc2626" : "1px solid #ddd",
                background: condition === c.value ? "#fef2f2" : "white",
                fontWeight: condition === c.value ? 700 : 400,
              }}
            >
              {c.label}
            </button>
          ))}
        </div>

        <label style={{ fontSize: 13, fontWeight: 700, marginBottom: 6, display: "block" }}>
          Bed type needed
        </label>
        <select
          value={bedType}
          onChange={(e) => setBedType(e.target.value)}
          style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ddd", marginBottom: 16 }}
        >
          {BED_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>

        <label style={{ fontSize: 13, fontWeight: 700, marginBottom: 6, display: "block" }}>
          Hospital
        </label>
        <select
          value={hospitalId}
          onChange={(e) => setHospitalId(e.target.value)}
          style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #ddd", marginBottom: 8 }}
        >
          <option value="">Select a hospital...</option>
          {hospitals.map((h) => (
            <option key={h.id} value={h.id}>{h.name} — {h.city}</option>
          ))}
        </select>
        <p style={{ fontSize: 11, color: "#999", marginTop: 0, marginBottom: 16 }}>
          Automatic nearest-hospital matching is coming soon — for now, please pick manually.
        </p>

        <div style={{ fontSize: 12, color: location ? "#16a34a" : "#d97706", marginBottom: 16 }}>
          {location ? "📍 Location captured" : locationError || "📍 Getting your location..."}
        </div>

        {error && <p className="error-text">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={submitting}
          style={{
            width: "100%", padding: 16, background: "#dc2626", color: "white", border: "none",
            borderRadius: 10, fontSize: 16, fontWeight: 700, cursor: "pointer",
          }}
        >
          {submitting ? "Sending request..." : "Send Emergency Request"}
        </button>
      </div>

      <p style={{ textAlign: "center", fontSize: 12, color: "#999", marginTop: 16 }}>
        If this is life-threatening, also call your local emergency number directly.
      </p>
    </div>
  );
}
