import React, { useState } from "react";
import { hospitalsAPI } from "../../../api/client";

export default function DoctorSection({ doctors, onChange }) {
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ user_id: "", specialty: "", license_number: "" });
  const [error, setError] = useState("");

  const handleAdd = async () => {
    setError("");
    try {
      await hospitalsAPI.doctors.create({ ...form, user_id: Number(form.user_id) });
      setAdding(false);
      setForm({ user_id: "", specialty: "", license_number: "" });
      onChange();
    } catch (err) {
      const data = err.response?.data;
      setError(data ? Object.values(data).flat().join(" ") : "Couldn't add doctor.");
    }
  };

  const toggleDuty = async (doc) => {
    await hospitalsAPI.doctors.update(doc.id, { is_on_duty: !doc.is_on_duty });
    onChange();
  };

  const handleDelete = async (id) => {
    if (!confirm("Remove this doctor from the roster?")) return;
    await hospitalsAPI.doctors.delete(id);
    onChange();
  };

  return (
    <section style={{ marginBottom: 28 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 18 }}>Doctors</h2>
        <button onClick={() => setAdding(!adding)} style={smallBtnStyle}>
          {adding ? "Cancel" : "+ Add Doctor"}
        </button>
      </div>

      {adding && (
        <div style={{ marginBottom: 12, padding: 12, background: "#f9fafb", borderRadius: 8 }}>
          <p style={{ fontSize: 12, color: "#666", marginTop: 0 }}>
            The doctor must already have a user account with role="doctor" (create via Django admin
            first if they don't have one yet) — enter their User ID below.
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input
              placeholder="User ID"
              value={form.user_id}
              onChange={(e) => setForm({ ...form, user_id: e.target.value })}
              style={{ width: 80 }}
            />
            <input
              placeholder="Specialty"
              value={form.specialty}
              onChange={(e) => setForm({ ...form, specialty: e.target.value })}
            />
            <input
              placeholder="License number"
              value={form.license_number}
              onChange={(e) => setForm({ ...form, license_number: e.target.value })}
            />
            <button onClick={handleAdd} style={smallBtnStyle}>Save</button>
          </div>
        </div>
      )}
      {error && <p style={{ color: "#dc2626", fontSize: 13 }}>{error}</p>}

      {doctors.length === 0 && !adding && <p style={{ color: "#666" }}>No doctors added yet.</p>}

      <div style={{ display: "grid", gap: 8 }}>
        {doctors.map((doc) => (
          <div key={doc.id} style={{ padding: 12, background: "white", borderRadius: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>{doc.name} — {doc.specialty}</span>
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <button onClick={() => toggleDuty(doc)} style={{ ...smallBtnStyle, background: doc.is_on_duty ? "#16a34a" : "#999" }}>
                {doc.is_on_duty ? "On duty" : "Off duty"}
              </button>
              <button onClick={() => handleDelete(doc.id)} style={deleteBtnStyle}>✕</button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

const smallBtnStyle = {
  padding: "6px 12px", background: "#2563eb", color: "white", border: "none",
  borderRadius: 6, fontSize: 13, cursor: "pointer",
};
const deleteBtnStyle = {
  background: "none", border: "none", color: "#dc2626", cursor: "pointer", fontSize: 13,
};
