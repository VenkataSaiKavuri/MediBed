import React, { useEffect, useState } from "react";
import { hospitalsAPI } from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";

export default function HospitalAdminDashboard() {
  const { user, logout } = useAuth();
  const [hospital, setHospital] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    hospitalsAPI
      .mine()
      .then(({ data }) => setHospital(data))
      .catch((err) =>
        setError(err.response?.data?.detail || "Your account isn't linked to a hospital yet.")
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ textAlign: "center", marginTop: 80 }}>Loading...</p>;

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", padding: "0 20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0 }}>{hospital?.name || "Hospital Admin"}</h1>
          <p style={{ color: "#666", margin: "4px 0 0" }}>Logged in as {user?.first_name || user?.username}</p>
        </div>
        <button onClick={logout} style={{ background: "none", border: "1px solid #ddd", borderRadius: 8, padding: "8px 14px", cursor: "pointer" }}>
          Log out
        </button>
      </div>

      {error && (
        <div style={{ padding: 16, background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, color: "#b91c1c" }}>
          {error}
          <p style={{ fontSize: 13, marginTop: 8, marginBottom: 0 }}>
            Fix: in Django admin, open your Hospital, then open your User and set its "Hospital" field.
          </p>
        </div>
      )}

      {hospital && (
        <>
          <section style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: 18 }}>Bed Inventory</h2>
            {hospital.bed_inventory.length === 0 && <p style={{ color: "#666" }}>No bed types added yet — add via Django admin.</p>}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
              {hospital.bed_inventory.map((bed) => (
                <div key={bed.id} style={{ padding: 14, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
                  <strong style={{ textTransform: "capitalize" }}>{bed.bed_type}</strong>
                  <p style={{ margin: "6px 0 0", fontSize: 20, fontWeight: 700 }}>
                    {bed.available_count}/{bed.total_count}
                  </p>
                  <p style={{ margin: 0, fontSize: 12, color: "#999" }}>available / total</p>
                  {/* Edit form to update total_count comes in Day 4 */}
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: 18 }}>Doctors</h2>
            {hospital.doctors.length === 0 && <p style={{ color: "#666" }}>No doctors added yet.</p>}
            <div style={{ display: "grid", gap: 8 }}>
              {hospital.doctors.map((doc) => (
                <div key={doc.id} style={{ padding: 12, background: "white", borderRadius: 8, display: "flex", justifyContent: "space-between" }}>
                  <span>{doc.name} — {doc.specialty}</span>
                  <span style={{ color: doc.is_on_duty ? "#16a34a" : "#999" }}>
                    {doc.is_on_duty ? "On duty" : "Off duty"}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 style={{ fontSize: 18 }}>Equipment</h2>
            {hospital.equipment.length === 0 && <p style={{ color: "#666" }}>No equipment added yet.</p>}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
              {hospital.equipment.map((eq) => (
                <div key={eq.id} style={{ padding: 14, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
                  <strong>{eq.name}</strong>
                  <p style={{ margin: "6px 0 0", fontSize: 20, fontWeight: 700 }}>
                    {eq.available_count}/{eq.total_count}
                  </p>
                  <p style={{ margin: 0, fontSize: 12, color: "#999", textTransform: "capitalize" }}>{eq.status}</p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
