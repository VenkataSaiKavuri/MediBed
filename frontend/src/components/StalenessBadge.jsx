import React from "react";

const CONFIG = {
  fresh: { label: "🟢 Live", bg: "#dcfce7", color: "#166534" },
  aging: { label: "🟡 Updated a while ago", bg: "#fef3c7", color: "#92400e" },
  stale: { label: "🔴 May be outdated", bg: "#fef2f2", color: "#b91c1c" },
};

/**
 * Shows a small trust-signal badge for how recently availability data was updated.
 * `level` is one of 'fresh' | 'aging' | 'stale' | null (from the backend's staleness_level()).
 * Renders nothing if level is null (e.g. a hospital with no bed inventory at all yet).
 */
export default function StalenessBadge({ level, compact = false }) {
  if (!level || !CONFIG[level]) return null;
  const { label, bg, color } = CONFIG[level];

  return (
    <span
      style={{
        fontSize: compact ? 10 : 11,
        fontWeight: 700,
        padding: compact ? "2px 6px" : "3px 8px",
        borderRadius: 10,
        background: bg,
        color,
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </span>
  );
}
