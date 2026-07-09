import React, { useState } from "react";
import { hospitalsAPI } from "../../../api/client";
import StalenessBadge from "../../../components/StalenessBadge.jsx";

const BED_TYPES = ["general", "icu", "ventilator", "maternity", "emergency"];

export default function BedInventorySection({ beds, onChange }) {
  const [adding, setAdding] = useState(false);
  const [newBed, setNewBed] = useState({ bed_type: "general", total_count: 0 });
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState(0);
  const [error, setError] = useState("");

  const handleAdd = async () => {
    setError("");
    try {
      await hospitalsAPI.beds.create(newBed);
      setAdding(false);
      setNewBed({ bed_type: "general", total_count: 0 });
      onChange();
    } catch (err) {
      setError(err.response?.data?.bed_type?.[0] || err.response?.data?.detail || "Couldn't add bed type.");
    }
  };

  const startEdit = (bed) => {
    setEditingId(bed.id);
    setEditValue(bed.total_count);
  };

  const saveEdit = async (bedId) => {
    await hospitalsAPI.beds.update(bedId, { total_count: Number(editValue) });
    setEditingId(null);
    onChange();
  };

  const handleDelete = async (bedId) => {
    if (!confirm("Remove this bed type? This can't be undone.")) return;
    await hospitalsAPI.beds.delete(bedId);
    onChange();
  };

  return (
    <section style={{ marginBottom: 28 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 18 }}>Bed Inventory</h2>
        <button onClick={() => setAdding(!adding)} style={smallBtnStyle}>
          {adding ? "Cancel" : "+ Add Bed Type"}
        </button>
      </div>

      {adding && (
        <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
          <select value={newBed.bed_type} onChange={(e) => setNewBed({ ...newBed, bed_type: e.target.value })}>
            {BED_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input
            type="number"
            min={0}
            value={newBed.total_count}
            onChange={(e) => setNewBed({ ...newBed, total_count: e.target.value })}
            style={{ width: 80 }}
            placeholder="Total"
          />
          <button onClick={handleAdd} style={smallBtnStyle}>Save</button>
        </div>
      )}
      {error && <p style={{ color: "#dc2626", fontSize: 13 }}>{error}</p>}

      {beds.length === 0 && !adding && <p style={{ color: "#666" }}>No bed types yet — click "+ Add Bed Type".</p>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
        {beds.map((bed) => (
          <div key={bed.id} style={cardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong style={{ textTransform: "capitalize" }}>{bed.bed_type}</strong>
              <button onClick={() => handleDelete(bed.id)} style={deleteBtnStyle} title="Remove bed type">✕</button>
            </div>

            {editingId === bed.id ? (
              <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
                <input
                  type="number"
                  min={0}
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  style={{ width: 60 }}
                />
                <button onClick={() => saveEdit(bed.id)} style={smallBtnStyle}>✓</button>
              </div>
            ) : (
              <>
                <p style={{ margin: "6px 0 0", fontSize: 20, fontWeight: 700 }}>
                  {bed.available_count}/{bed.total_count}
                </p>
                <p style={{ margin: 0, fontSize: 12, color: "#999" }}>
                  available / total —{" "}
                  <a href="#" onClick={(e) => { e.preventDefault(); startEdit(bed); }}>edit total</a>
                </p>
                <div style={{ marginTop: 6 }}><StalenessBadge level={bed.staleness} compact /></div>
              </>
            )}
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
