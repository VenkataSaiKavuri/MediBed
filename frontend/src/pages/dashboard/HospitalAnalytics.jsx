import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client, { bookingsAPI } from "../../api/client";

const STATUS_COLORS = {
  requested: "#d97706", confirmed: "#16a34a", rejected: "#dc2626",
  completed: "#2563eb", cancelled: "#666", no_show: "#dc2626", escalated: "#d97706",
};

function BookingVolumeChart({ data }) {
  if (data.length === 0) return <p style={{ color: "#666", fontSize: 13 }}>No bookings in this period.</p>;
  const max = Math.max(...data.map((d) => d.count), 1);
  const width = 700, height = 160, barGap = 4;
  const barWidth = Math.max(4, width / data.length - barGap);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto" }}>
      {data.map((d, i) => {
        const barHeight = (d.count / max) * (height - 24);
        const x = i * (barWidth + barGap);
        return (
          <g key={d.date}>
            <rect
              x={x} y={height - barHeight - 20} width={barWidth} height={barHeight}
              fill="#2563eb" rx={2}
            >
              <title>{d.date}: {d.count} booking{d.count === 1 ? "" : "s"}</title>
            </rect>
            <text x={x + barWidth / 2} y={height - 6} fontSize={9} fill="#999" textAnchor="middle">
              {d.count}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function HospitalAnalytics() {
  const [data, setData] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    bookingsAPI
      .analytics(days)
      .then(({ data }) => setData(data))
      .catch(() => setError("Couldn't load analytics."))
      .finally(() => setLoading(false));
  }, [days]);

  const handleExport = async () => {
    try {
      const response = await client.get(bookingsAPI.analyticsExportUrl, { responseType: "blob" });
      const url = window.URL.createObjectURL(response.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "medbeds_bookings_export.csv";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Couldn't export CSV.");
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", padding: "0 20px" }}>
      <Link to="/dashboard/hospital-admin" style={{ fontSize: 13, color: "#2563eb", textDecoration: "none" }}>
        ← Back to dashboard
      </Link>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "12px 0 24px" }}>
        <h1 style={{ margin: 0 }}>Analytics</h1>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <select value={days} onChange={(e) => setDays(Number(e.target.value))} style={{ padding: 8, borderRadius: 8, border: "1px solid #ddd" }}>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button onClick={handleExport} style={{ padding: "8px 14px", background: "#2563eb", color: "white", border: "none", borderRadius: 8, cursor: "pointer", fontSize: 13, fontWeight: 600 }}>
            ⬇ Export CSV
          </button>
        </div>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}

      {data && (
        <>
          <section style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: 16 }}>Current Occupancy</h2>
            <p style={{ fontSize: 12, color: "#999", marginTop: -4 }}>
              Right-now utilization per bed type — not a historical trend, since we don't store
              bed-count snapshots over time.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 12 }}>
              {data.occupancy.length === 0 && <p style={{ color: "#666" }}>No bed data yet.</p>}
              {data.occupancy.map((o) => (
                <div key={o.bed_type} style={{ padding: 14, background: "white", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
                  <strong style={{ textTransform: "capitalize", fontSize: 13 }}>{o.bed_type}</strong>
                  <p style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>{o.occupancy_pct}%</p>
                  <div style={{ background: "#f3f4f6", borderRadius: 6, height: 8, overflow: "hidden" }}>
                    <div style={{ width: `${o.occupancy_pct}%`, background: o.occupancy_pct > 80 ? "#dc2626" : "#2563eb", height: "100%" }} />
                  </div>
                  <p style={{ margin: "6px 0 0", fontSize: 11, color: "#999" }}>{o.occupied}/{o.total} occupied</p>
                </div>
              ))}
            </div>
          </section>

          <section style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: 16 }}>Booking Volume</h2>
            <div style={{ background: "white", borderRadius: 10, padding: 16, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
              <BookingVolumeChart data={data.booking_volume} />
            </div>
          </section>

          <section style={{ marginBottom: 28, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div style={{ background: "white", borderRadius: 10, padding: 16, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
              <h2 style={{ fontSize: 16, marginTop: 0 }}>No-Show Rate</h2>
              <p style={{ fontSize: 28, fontWeight: 700, margin: "4px 0", color: data.no_show.no_show_rate_pct > 15 ? "#dc2626" : "#16a34a" }}>
                {data.no_show.no_show_rate_pct}%
              </p>
              <p style={{ fontSize: 12, color: "#999", margin: 0 }}>
                {data.no_show.no_show_count} of {data.no_show.resolved_count} resolved bookings
              </p>
            </div>

            <div style={{ background: "white", borderRadius: 10, padding: 16, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
              <h2 style={{ fontSize: 16, marginTop: 0 }}>Status Breakdown</h2>
              {data.status_breakdown.length === 0 && <p style={{ color: "#666", fontSize: 13 }}>No bookings in this period.</p>}
              {data.status_breakdown.map((s) => (
                <div key={s.status} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "4px 0" }}>
                  <span style={{ color: STATUS_COLORS[s.status] || "#333", textTransform: "capitalize", fontWeight: 600 }}>
                    {s.status.replace("_", " ")}
                  </span>
                  <span>{s.count}</span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
