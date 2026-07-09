import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { hospitalsAPI } from "../../api/client";
import { useAuth } from "../../context/AuthContext.jsx";
import BedInventorySection from "./components/BedInventorySection.jsx";
import DoctorSection from "./components/DoctorSection.jsx";
import EquipmentSection from "./components/EquipmentSection.jsx";

export default function HospitalAdminDashboard() {
  const { user, logout } = useAuth();
  const [hospital, setHospital] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadHospital = () => {
    hospitalsAPI
      .mine()
      .then(({ data }) => setHospital(data))
      .catch((err) =>
        setError(err.response?.data?.detail || "Your account isn't linked to a hospital yet.")
      )
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadHospital();
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

      <Link
        to="/dashboard/hospital-admin/bookings"
        style={{
          display: "inline-block", marginBottom: 20, padding: "10px 16px", background: "#2563eb",
          color: "white", borderRadius: 8, fontSize: 14, fontWeight: 600, textDecoration: "none",
        }}
      >
        📋 View Booking Requests
      </Link>

      {error && (
        <div style={{ padding: 16, background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, color: "#b91c1c" }}>
          {error}
          <p style={{ fontSize: 13, marginTop: 8, marginBottom: 0 }}>
            Fix: in Django admin, open your Hospital, then open your User and set its "Hospital" field.
          </p>
        </div>
      )}

      {hospital && (() => {
        const staleItems = [
          ...(hospital.bed_inventory || []).filter((b) => b.staleness === "stale"),
          ...(hospital.equipment || []).filter((e) => e.staleness === "stale"),
        ];
        if (staleItems.length === 0) return null;
        return (
          <div style={{ padding: 14, background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, color: "#b91c1c", marginBottom: 20, fontSize: 13 }}>
            🔴 {staleItems.length} item{staleItems.length === 1 ? "" : "s"} haven't been updated in over
            6 hours. Patients may be seeing outdated availability — please review your counts below.
          </div>
        );
      })()}

      {hospital && (
        <>
          <BedInventorySection beds={hospital.bed_inventory} onChange={loadHospital} />
          <DoctorSection doctors={hospital.doctors} onChange={loadHospital} />
          <EquipmentSection equipment={hospital.equipment} onChange={loadHospital} />
        </>
      )}
    </div>
  );
}
