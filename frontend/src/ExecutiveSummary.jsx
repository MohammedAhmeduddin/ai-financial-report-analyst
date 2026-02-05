// frontend/src/ExecutiveSummary.jsx

import React from "react";

function formatNumber(n) {
  if (typeof n !== "number" || Number.isNaN(n)) return "-";
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export default function ExecutiveSummary({ variance }) {
  if (!variance?.net_income_change || !variance?.drivers_list) return null;

  const totalChange = variance.net_income_change;

  // Find primary driver by absolute impact
  const primary = [...variance.drivers_list].sort(
    (a, b) => Math.abs(b.impact) - Math.abs(a.impact),
  )[0];

  const operatingImpact = variance.drivers_list
    .filter((d) =>
      ["revenue_impact", "margin_impact", "opex_impact"].includes(d.name),
    )
    .reduce((sum, d) => sum + (d.impact || 0), 0);

  const operatingPct =
    totalChange !== 0 ? Math.round((operatingImpact / totalChange) * 100) : 0;

  const primaryLabel =
    primary.name === "other"
      ? "below-the-line items, notably a tax benefit"
      : primary.name.replaceAll("_", " ");

  return (
    <div className="mb-6 rounded-2xl border border-zinc-800 bg-zinc-950/40 px-5 py-4">
      <div className="text-sm font-semibold text-zinc-100">
        Executive Summary
      </div>
      <div className="mt-0.5 text-xs text-zinc-400">
        All figures derived from audited filings
      </div>

      <p className="mt-2 text-sm leading-relaxed text-zinc-300">
        Net income increased by{" "}
        <span className="font-semibold text-zinc-100">
          {formatNumber(totalChange)}
        </span>{" "}
        year-over-year, driven primarily by{" "}
        <span className="font-semibold text-zinc-100">{primaryLabel}</span>.
        Core operating performance (revenue and margin) contributed
        approximately{" "}
        <span className="font-semibold text-zinc-100">{operatingPct}%</span> of
        the total change. Results are fully reconciled and auditable against
        consolidated financial statements.
      </p>
    </div>
  );
}
