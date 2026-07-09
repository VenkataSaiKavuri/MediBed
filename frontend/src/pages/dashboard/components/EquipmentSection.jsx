import React, { useState } from "react";
import { hospitalsAPI } from "../../../api/client";
import StalenessBadge from "../../../components/StalenessBadge.jsx";

const STATUSES = ["available", "in_use", "maintenance"];

export default function EquipmentSection({ equipment, onChange }) {
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", total_count: 0, available_count: 0, status: "available" });
  const [error, setError] = useState("");

  const handleAdd = async () => {
    setError("");
    try {
      await hospitalsAPI.equipment.create(form);
      setAdding(false);
      setForm({ name: "", total_count: 0, available_count: 0, status: "available" });
      onChange();
    } catch (err) {
      setError(err.response?.data?.name?.[0] || "Couldn't add equipment.");
    }
  };

  const cycleStatus = async (eq) => {
    const next = STATUSES[(STATUSES.indexOf(eq.status) + 1) % STATUSES.length];
    await hospitalsAPI.equipment.update(eq.id, { status: next });
    onChange();
  };

  const handleDelete = async (id) => {
    if (!confirm("Remove this equipment entry?")) return;
    await hospitalsAPI.equipment.delete(id);
    onChange();
  };

  return (
    <section>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 18 }}>Equipment</h2>
        <button onClick={() => setAdding(!adding)} style={smallBtnStyle}>
          {adding ? "Cancel" : "+ Add Equipment"}
        </button>
      </div>

      {adding && (
        <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <input placeholder="Name (e.g. Ventilator)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input type="number" min={0} placeholder="Total" value={form.total_count} onChange={(e) => setForm({ ...form, total_count: e.target.value })} style={{ width: 70 }} />
          <input type="number" min={0} placeholder="Available" value={form.available_count} onChange={(e) => setForm({ ...form, available_count: e.target.value })} style={{ width: 80 }} />
          <button onClick={handleAdd} style={smallBtnStyle}>Save</button>
        </div>
      )}
      {error && <p style={{ color: "#dc2626", fontSize: 13 }}>{error}</p>}

      {equipment.length === 0 && !adding && <p style={{ color: "#666" }}>No equipment added yet.</p>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
        {equipment.map((eq) => (
          <div key={eq.id} style={cardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{eq.name}</strong>
              <button onClick={() => handleDelete(eq.id)} style={deleteBtnStyle}>✕</button>
            </div>
            <p style={{ margin: "6px 0 0", fontSize: 20, fontWeight: 700 }}>{eq.available_count}/{eq.total_count}</p>
            <button onClick={() => cycleStatus(eq)} style={{ ...smallBtnStyle, marginTop: 6, textTransform: "capitalize" }}>
              {eq.status.replace("_", " ")}
            </button>
            <div style={{ marginTop: 6 }}><StalenessBadge level={eq.staleness} compact /></div>
          </div>
        ))}
      </div>
    </section>
  );
}

const cardStyle = {
  padding: 14, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
};
const smallBtnStyle = {
  padding: "6px 12px", background: "#2563eb", color: "white", border: "none",
  borderRadius: 6, fontSize: 13, cursor: "pointer",
};
const deleteBtnStyle = {
  background: "none", border: "none", color: "#dc2626", cursor: "pointer", fontSize: 13,
};
