import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { hospitalsAPI } from "../api/client";

export default function HospitalDetail() {
  const { id } = useParams();
  const [hospital, setHospital] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    hospitalsAPI
      .detail(id)
      .then(({ data }) => setHospital(data))
      .catch(() => setError("Couldn't load this hospital."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p style={{ textAlign: "center", marginTop: 80 }}>Loading...</p>;
  if (error) return <p style={{ textAlign: "center", marginTop: 80, color: "#dc2626" }}>{error}</p>;

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: "0 20px" }}>
      <Link to="/dashboard/patient" style={{ fontSize: 14, color: "#2563eb", textDecoration: "none" }}>
        ← Back to search
      </Link>

      <h1 style={{ margin: "12px 0 4px" }}>{hospital.name}</h1>
      <p style={{ color: "#666", margin: 0 }}>{hospital.address}, {hospital.city}</p>
      <p style={{ color: "#666", margin: "4px 0 24px" }}>📞 {hospital.phone_number}</p>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16 }}>Bed Availability</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10 }}>
          {hospital.bed_inventory.length === 0 && <p style={{ color: "#666" }}>No bed data yet.</p>}
          {hospital.bed_inventory.map((bed) => (
            <div key={bed.id} style={cardStyle}>
              <strong style={{ textTransform: "capitalize" }}>{bed.bed_type}</strong>
              <p style={{ margin: "4px 0 0", fontSize: 18, fontWeight: 700 }}>{bed.available_count}/{bed.total_count}</p>
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16 }}>Doctors on Duty</h2>
        {hospital.doctors.filter((d) => d.is_on_duty).length === 0 && <p style={{ color: "#666" }}>No doctors currently on duty listed.</p>}
        <div style={{ display: "grid", gap: 6 }}>
          {hospital.doctors.filter((d) => d.is_on_duty).map((doc) => (
            <div key={doc.id} style={{ padding: 10, background: "white", borderRadius: 8 }}>
              {doc.name} — {doc.specialty}
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16 }}>Equipment</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10 }}>
          {hospital.equipment.map((eq) => (
            <div key={eq.id} style={cardStyle}>
              <strong>{eq.name}</strong>
              <p style={{ margin: "4px 0 0", fontSize: 18, fontWeight: 700 }}>{eq.available_count}/{eq.total_count}</p>
            </div>
          ))}
        </div>
      </section>

      <button
        style={{ width: "100%", padding: 14, background: "#2563eb", color: "white", border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: "pointer" }}
        onClick={() => alert("Booking form arrives on Day 9.")}
      >
        Book a Bed Here
      </button>
    </div>
  );
}

const cardStyle = {
  padding: 12, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
};
