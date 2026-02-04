import React, { useEffect, useMemo, useState } from "react";

/**
 * Product-style UI:
 * - Base & Compare upload panels
 * - Run pipeline: /upload -> /extract -> /metrics
 * - Compare variance endpoint
 * - Ask endpoint with compare_upload_id
 *
 * Assumptions about backend routes:
 * - POST /upload (multipart form field: file) -> { upload_id }
 * - POST /extract/{upload_id}
 * - POST /metrics/{upload_id}
 * - POST /variance/{base}/{compare}
 * - POST /ask/{base} with JSON { question, compare_upload_id }
 * - GET  /health -> 200 OK (any JSON/text is fine)
 */

function cx(...classes) {
  return classes.filter(Boolean).join(" ");
}

function formatNumber(n) {
  if (typeof n !== "number" || Number.isNaN(n)) return "-";
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function Badge({ children, tone = "neutral" }) {
  const tones = {
    neutral: "bg-zinc-800/60 text-zinc-200 border-zinc-700",
    success: "bg-emerald-900/30 text-emerald-200 border-emerald-800/60",
    warning: "bg-amber-900/25 text-amber-200 border-amber-800/60",
    danger: "bg-rose-900/25 text-rose-200 border-rose-800/60",
    info: "bg-sky-900/25 text-sky-200 border-sky-800/60",
  };
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs",
        tones[tone] || tones.neutral,
      )}
    >
      {children}
    </span>
  );
}

function StatusChip({ label, value, tone = "neutral" }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-950/40 px-3 py-1.5 text-xs">
      <span className="text-zinc-400">{label}</span>
      <Badge tone={tone}>{value}</Badge>
    </div>
  );
}

function Card({ title, subtitle, right, children }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 shadow-sm">
      <div className="flex items-start justify-between gap-4 border-b border-zinc-800 px-5 py-4">
        <div>
          <div className="text-sm font-semibold text-zinc-100">{title}</div>
          {subtitle ? (
            <div className="mt-1 text-xs text-zinc-400">{subtitle}</div>
          ) : null}
        </div>
        {right ? <div className="shrink-0">{right}</div> : null}
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

function Button({ children, variant = "primary", className, ...props }) {
  const variants = {
    primary:
      "bg-white text-zinc-950 hover:bg-zinc-100 disabled:bg-zinc-200 disabled:text-zinc-500",
    secondary:
      "bg-zinc-800 text-zinc-100 hover:bg-zinc-700 disabled:bg-zinc-900 disabled:text-zinc-600",
    ghost:
      "bg-transparent text-zinc-100 hover:bg-zinc-800/60 disabled:text-zinc-600",
    danger:
      "bg-rose-600 text-white hover:bg-rose-500 disabled:bg-rose-900 disabled:text-rose-300",
  };
  return (
    <button
      className={cx(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition",
        "focus:outline-none focus:ring-2 focus:ring-white/15",
        "disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant] || variants.primary,
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

function SmallLabel({ children }) {
  return <div className="text-xs font-medium text-zinc-400">{children}</div>;
}

function KeyValue({ label, value }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 px-4 py-3">
      <div className="text-xs text-zinc-400">{label}</div>
      <div className="mt-1 text-sm font-semibold text-zinc-100 break-all">
        {value ?? "-"}
      </div>
    </div>
  );
}

function KPI({ label, value, sub, tone = "neutral" }) {
  const tones = {
    neutral: "border-zinc-800 bg-zinc-950/30",
    success: "border-emerald-900/50 bg-emerald-950/20",
    warning: "border-amber-900/50 bg-amber-950/15",
    danger: "border-rose-900/50 bg-rose-950/20",
    info: "border-sky-900/50 bg-sky-950/15",
  };

  return (
    <div className={cx("rounded-2xl border p-4", tones[tone] || tones.neutral)}>
      <div className="text-xs text-zinc-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold tracking-tight text-zinc-100">
        {value}
      </div>
      {sub ? <div className="mt-1 text-xs text-zinc-500">{sub}</div> : null}
    </div>
  );
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json();
}

async function postNoBody(url) {
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json();
}

async function uploadPDF(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/upload", { method: "POST", body: fd });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json(); // { upload_id, ... }
}

async function pingHealth() {
  // Works whether backend returns JSON or plain text.
  const res = await fetch("/health", { method: "GET" });
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return true;
}

function MetricTable({ metrics }) {
  const labels = {
    revenue: "Revenue",
    gross_profit: "Gross profit",
    operating_income: "Operating income",
    other_income_expense_net: "Other income/(expense), net",
    pre_tax_income: "Pre-tax income",
    income_taxes: "Income taxes",
    net_income: "Net income",
    total_assets: "Total assets",
    total_liabilities: "Total liabilities",
  };

  const rows = useMemo(() => {
    if (!metrics) return [];
    const order = [
      "revenue",
      "gross_profit",
      "operating_income",
      "other_income_expense_net",
      "pre_tax_income",
      "income_taxes",
      "net_income",
      "total_assets",
      "total_liabilities",
    ];
    return order.filter((k) => k in metrics).map((k) => ({ k, v: metrics[k] }));
  }, [metrics]);

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800">
      <table className="min-w-full divide-y divide-zinc-800">
        <thead className="bg-zinc-950/40">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-300">
              Metric
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-zinc-300">
              Value
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800 bg-zinc-900/20">
          {rows.map((r) => (
            <tr key={r.k} className="hover:bg-zinc-900/40">
              <td className="px-4 py-3 text-sm text-zinc-200">
                {labels[r.k] || r.k.replaceAll("_", " ")}
              </td>
              <td className="px-4 py-3 text-right text-sm font-medium text-zinc-100">
                {formatNumber(r.v)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DriverTable({ variance }) {
  const list = variance?.drivers_list || [];
  if (!list.length) return null;

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800">
      <table className="min-w-full divide-y divide-zinc-800">
        <thead className="bg-zinc-950/40">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-300">
              Driver
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-zinc-300">
              Impact
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-zinc-300">
              % of change
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800 bg-zinc-900/20">
          {list.map((d) => (
            <tr key={d.name} className="hover:bg-zinc-900/40">
              <td className="px-4 py-3 text-sm text-zinc-200">
                {String(d.name).replaceAll("_", " ")}
              </td>
              <td className="px-4 py-3 text-right text-sm font-medium text-zinc-100">
                {formatNumber(d.impact)}
              </td>
              <td className="px-4 py-3 text-right text-sm text-zinc-200">
                {typeof d.pct_of_change === "number"
                  ? `${d.pct_of_change.toFixed(2)}%`
                  : "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Citations({ citations }) {
  if (!citations?.length) return null;
  return (
    <div className="space-y-3">
      {citations.map((c) => (
        <div
          key={`${c.upload_id}:${c.chunk_id ?? c.page_start ?? Math.random()}`}
          className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="info">upload</Badge>
            <span className="text-xs text-zinc-300 break-all">
              {c.upload_id}
            </span>
            {c.page_start != null && c.page_end != null ? (
              <Badge>
                pages {c.page_start}–{c.page_end}
              </Badge>
            ) : null}
          </div>
          <div className="mt-2 text-sm leading-relaxed text-zinc-200">
            {c.text_preview || c.text || JSON.stringify(c)}
          </div>
        </div>
      ))}
    </div>
  );
}

/** A simple “pro” logo as inline SVG (no extra library needed) */
function AppLogo() {
  return (
    <div className="h-11 w-11 rounded-2xl border border-zinc-800 bg-zinc-950/40 grid place-items-center shadow-sm">
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        className="text-zinc-100"
        aria-hidden="true"
      >
        <path
          d="M12 2l8.5 20h-2.6l-2-5H8.1l-2 5H3.5L12 2z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path
          d="M9 14h6L12 6.5 9 14z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

export default function App() {
  const [baseFile, setBaseFile] = useState(null);
  const [compareFile, setCompareFile] = useState(null);

  const [base, setBase] = useState({
    uploadId: null,
    metrics: null,
    status: "idle",
  });
  const [compare, setCompare] = useState({
    uploadId: null,
    metrics: null,
    status: "idle",
  });

  const [variance, setVariance] = useState(null);
  const [answer, setAnswer] = useState(null);
  const [citations, setCitations] = useState([]);

  const [question, setQuestion] = useState(
    "Why did other change so much? Was it taxes or other income/expense?",
  );

  const [error, setError] = useState(null);

  // ====== Status chips state ======
  const [backendOk, setBackendOk] = useState(null); // null=unknown, true=ok, false=down
  const canCompare = Boolean(base.uploadId && compare.uploadId);

  const mode = canCompare ? "Compare" : "Single";
  const uploadsReady = canCompare ? "Ready" : "Missing";

  useEffect(() => {
    let alive = true;

    async function tick() {
      try {
        await pingHealth();
        if (alive) setBackendOk(true);
      } catch {
        if (alive) setBackendOk(false);
      }
    }

    tick();
    const id = setInterval(tick, 4000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // ====== KPIs ======
  const baseRevenue = base.metrics?.revenue;
  const compareRevenue = compare.metrics?.revenue;

  const revDelta =
    typeof baseRevenue === "number" && typeof compareRevenue === "number"
      ? compareRevenue - baseRevenue
      : null;

  const niDelta =
    typeof variance?.net_income_change === "number"
      ? variance.net_income_change
      : null;

  const explained =
    typeof variance?.explained_pct === "number"
      ? `${variance.explained_pct.toFixed(2)}% explained`
      : "Run variance to compute";

  async function runPipeline(which) {
    setError(null);

    const file = which === "base" ? baseFile : compareFile;
    const setState = which === "base" ? setBase : setCompare;

    try {
      setState((s) => ({ ...s, status: "uploading" }));
      const up = await uploadPDF(file);
      const uploadId = up.upload_id || up.uploadId;

      setState((s) => ({ ...s, uploadId, status: "extracting" }));
      await postNoBody(`/extract/${uploadId}`);

      setState((s) => ({ ...s, status: "metrics" }));
      const m = await postNoBody(`/metrics/${uploadId}`);

      setState((s) => ({ ...s, metrics: m.metrics || null, status: "ready" }));
    } catch (e) {
      setState((s) => ({ ...s, status: "error" }));
      setError(String(e?.message || e));
    }
  }

  async function runVariance() {
    setError(null);
    setVariance(null);
    setAnswer(null);
    setCitations([]);

    try {
      const v = await postNoBody(
        `/variance/${base.uploadId}/${compare.uploadId}`,
      );
      setVariance(v);
    } catch (e) {
      setError(String(e?.message || e));
    }
  }

  async function runAsk() {
    setError(null);
    setAnswer(null);
    setCitations([]);

    try {
      const payload = await postJSON(`/ask/${base.uploadId}`, {
        question,
        compare_upload_id: compare.uploadId,
      });
      setAnswer(payload.answer || "");
      setCitations(payload.citations || payload.evidence || []);
      setVariance(payload.variance || variance);
    } catch (e) {
      setError(String(e?.message || e));
    }
  }

  function statusBadge(status) {
    if (status === "idle") return <Badge>Idle</Badge>;
    if (status === "uploading") return <Badge tone="warning">Uploading</Badge>;
    if (status === "extracting")
      return <Badge tone="warning">Extracting</Badge>;
    if (status === "metrics") return <Badge tone="warning">Metrics</Badge>;
    if (status === "ready") return <Badge tone="success">Ready</Badge>;
    if (status === "error") return <Badge tone="danger">Error</Badge>;
    return <Badge>{status}</Badge>;
  }

  const canRunBase = Boolean(baseFile);
  const canRunCompare = Boolean(compareFile);

  const basePipelineLabel =
    base.status === "uploading"
      ? "Uploading…"
      : base.status === "extracting"
        ? "Extracting…"
        : base.status === "metrics"
          ? "Computing metrics…"
          : "Extract metrics";

  const comparePipelineLabel =
    compare.status === "uploading"
      ? "Uploading…"
      : compare.status === "extracting"
        ? "Extracting…"
        : compare.status === "metrics"
          ? "Computing metrics…"
          : "Extract metrics";

  // ====== Status chip tones ======
  const backendTone =
    backendOk == null ? "neutral" : backendOk ? "success" : "danger";
  const backendText =
    backendOk == null ? "Checking…" : backendOk ? "Connected" : "Down";

  const modeTone = mode === "Compare" ? "info" : "neutral";
  const uploadsTone = uploadsReady === "Ready" ? "success" : "warning";

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <div className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <AppLogo />
            <div>
              <div className="text-sm font-semibold text-zinc-100">
                AI Financial Report Analyst
              </div>
              <div className="text-xs text-zinc-400">
                PDF → Metrics → Variance → Numbers-first answers
              </div>
            </div>
          </div>

          {/* ✅ Replaces “Hybrid / Finance+AI” with real status chips */}
          <div className="hidden items-center gap-2 sm:flex">
            <StatusChip
              label="Backend"
              value={backendText}
              tone={backendTone}
            />
            <StatusChip label="Mode" value={mode} tone={modeTone} />
            <StatusChip
              label="Uploads"
              value={uploadsReady}
              tone={uploadsTone}
            />
          </div>
        </div>
      </div>

      {/* Main */}
      <div className="mx-auto max-w-6xl px-6 py-8">
        {error ? (
          <div className="mb-6 rounded-2xl border border-rose-900/60 bg-rose-950/40 p-4">
            <div className="text-sm font-semibold text-rose-200">Error</div>
            <div className="mt-1 text-sm text-rose-100/90 break-words">
              {error}
            </div>
          </div>
        ) : null}

        {/* KPI strip */}
        {base.metrics || compare.metrics || variance ? (
          <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPI
              label="Base revenue"
              value={formatNumber(baseRevenue)}
              sub={base.uploadId ? "Extracted" : "—"}
              tone={base.metrics ? "info" : "neutral"}
            />
            <KPI
              label="Compare revenue"
              value={formatNumber(compareRevenue)}
              sub={compare.uploadId ? "Extracted" : "—"}
              tone={compare.metrics ? "info" : "neutral"}
            />
            <KPI
              label="Revenue delta"
              value={revDelta == null ? "-" : formatNumber(revDelta)}
              sub="Compare − Base"
              tone={
                revDelta == null
                  ? "neutral"
                  : revDelta >= 0
                    ? "success"
                    : "danger"
              }
            />
            <KPI
              label="Net income delta"
              value={niDelta == null ? "-" : formatNumber(niDelta)}
              sub={explained}
              tone={
                niDelta == null
                  ? "neutral"
                  : niDelta >= 0
                    ? "success"
                    : "danger"
              }
            />
          </div>
        ) : null}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Base */}
          <Card
            title="Base period"
            subtitle="Upload a PDF (e.g., FY24 Q4) and extract metrics."
            right={statusBadge(base.status)}
          >
            <div className="space-y-4">
              <div>
                <SmallLabel>PDF file</SmallLabel>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setBaseFile(e.target.files?.[0] || null)}
                  className="mt-2 block w-full text-sm text-zinc-300 file:mr-4 file:rounded-xl file:border-0 file:bg-zinc-800 file:px-4 file:py-2 file:text-sm file:font-medium file:text-zinc-100 hover:file:bg-zinc-700"
                />
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <KeyValue label="Upload ID" value={base.uploadId} />
                <KeyValue label="Status" value={base.status} />
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => runPipeline("base")}
                  disabled={
                    !canRunBase ||
                    ["uploading", "extracting", "metrics"].includes(base.status)
                  }
                >
                  {basePipelineLabel}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() =>
                    setBase({ uploadId: null, metrics: null, status: "idle" })
                  }
                >
                  Reset
                </Button>
              </div>

              {base.metrics ? (
                <div className="pt-2">
                  <SmallLabel>Extracted metrics</SmallLabel>
                  <div className="mt-2">
                    <MetricTable metrics={base.metrics} />
                  </div>
                </div>
              ) : null}
            </div>
          </Card>

          {/* Compare */}
          <Card
            title="Compare period"
            subtitle="Upload the comparison PDF (e.g., FY25 Q4) and extract metrics."
            right={statusBadge(compare.status)}
          >
            <div className="space-y-4">
              <div>
                <SmallLabel>PDF file</SmallLabel>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setCompareFile(e.target.files?.[0] || null)}
                  className="mt-2 block w-full text-sm text-zinc-300 file:mr-4 file:rounded-xl file:border-0 file:bg-zinc-800 file:px-4 file:py-2 file:text-sm file:font-medium file:text-zinc-100 hover:file:bg-zinc-700"
                />
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <KeyValue label="Upload ID" value={compare.uploadId} />
                <KeyValue label="Status" value={compare.status} />
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => runPipeline("compare")}
                  disabled={
                    !canRunCompare ||
                    ["uploading", "extracting", "metrics"].includes(
                      compare.status,
                    )
                  }
                >
                  {comparePipelineLabel}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() =>
                    setCompare({
                      uploadId: null,
                      metrics: null,
                      status: "idle",
                    })
                  }
                >
                  Reset
                </Button>
              </div>

              {compare.metrics ? (
                <div className="pt-2">
                  <SmallLabel>Extracted metrics</SmallLabel>
                  <div className="mt-2">
                    <MetricTable metrics={compare.metrics} />
                  </div>
                </div>
              ) : null}
            </div>
          </Card>
        </div>

        {/* Compare actions */}
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Card
            title="Variance drivers"
            subtitle="Compute drivers (revenue, margin, opex, other) and view the breakdown."
            right={
              canCompare ? (
                <Badge tone="success">Ready</Badge>
              ) : (
                <Badge tone="warning">Upload both PDFs</Badge>
              )
            }
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <KeyValue label="Base ID" value={base.uploadId} />
                <KeyValue label="Compare ID" value={compare.uploadId} />
              </div>

              <div className="flex gap-3">
                <Button onClick={runVariance} disabled={!canCompare}>
                  Compute variance
                </Button>
              </div>

              {variance?.net_income_change != null ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-zinc-100">
                      Net income change
                    </div>
                    <Badge
                      tone={
                        variance.net_income_change >= 0 ? "success" : "danger"
                      }
                    >
                      {variance.net_income_change >= 0
                        ? "Increase"
                        : "Decrease"}
                    </Badge>
                  </div>
                  <div className="mt-2 text-2xl font-bold text-zinc-100">
                    {formatNumber(variance.net_income_change)}
                  </div>
                  <div className="mt-1 text-xs text-zinc-400">
                    Explained:{" "}
                    {typeof variance.explained_pct === "number"
                      ? `${variance.explained_pct.toFixed(2)}%`
                      : "-"}
                  </div>
                </div>
              ) : null}

              {variance ? <DriverTable variance={variance} /> : null}

              {variance?.other_breakdown ? (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <KeyValue
                    label="Tax impact"
                    value={formatNumber(variance.other_breakdown.tax_impact)}
                  />
                  <KeyValue
                    label="Other I/E impact"
                    value={formatNumber(
                      variance.other_breakdown.other_income_expense_impact,
                    )}
                  />
                  <KeyValue
                    label="Remaining other"
                    value={formatNumber(
                      variance.other_breakdown.remaining_other_impact,
                    )}
                  />
                </div>
              ) : null}
            </div>
          </Card>

          <Card
            title="Ask (numbers-first)"
            subtitle="Generate an auditable narrative + citations."
            right={
              canCompare ? (
                <Badge tone="info">Compare mode</Badge>
              ) : (
                <Badge tone="warning">Need IDs</Badge>
              )
            }
          >
            <div className="space-y-4">
              <div>
                <SmallLabel>Your question</SmallLabel>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  rows={5}
                  className="mt-2 w-full rounded-xl border border-zinc-800 bg-zinc-950/40 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-white/10"
                  placeholder="e.g., Why did net income increase? Was it margins, opex, or taxes?"
                />
              </div>

              <div className="flex gap-3">
                <Button onClick={runAsk} disabled={!canCompare}>
                  Generate answer
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setAnswer(null);
                    setCitations([]);
                  }}
                >
                  Clear
                </Button>
              </div>

              <div className="text-xs text-zinc-500">
                Output: narrative + key drivers + citations (auditable)
              </div>

              {answer ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                  <div className="text-xs font-semibold text-zinc-300">
                    Answer
                  </div>
                  <pre className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-zinc-100 font-mono/90">
                    {answer}
                  </pre>
                </div>
              ) : (
                <div className="rounded-xl border border-zinc-800 bg-zinc-950/30 p-4 text-sm text-zinc-400">
                  This calls <span className="text-zinc-200">/ask</span> with{" "}
                  <span className="text-zinc-200">compare_upload_id</span> and
                  shows citations below.
                </div>
              )}
            </div>
          </Card>

          <Card
            title="Citations"
            subtitle="Evidence chunks used for grounding (income statement–focused)."
            right={
              citations?.length ? (
                <Badge tone="success">{citations.length} chunks</Badge>
              ) : (
                <Badge>—</Badge>
              )
            }
          >
            <Citations citations={citations} />
            {!citations?.length ? (
              <div className="text-sm text-zinc-400">
                Run <span className="text-zinc-200">Generate answer</span> to
                populate citations.
              </div>
            ) : null}
          </Card>
        </div>

        {/* Footer */}
        <div className="mt-10 flex flex-col items-start justify-between gap-3 border-t border-zinc-800 pt-6 text-xs text-zinc-500 sm:flex-row sm:items-center">
          <div>
            Built for a product-style demo: clean layout, strong hierarchy,
            auditable outputs.
          </div>
          <div className="flex items-center gap-2">
            <Badge>Backend: FastAPI</Badge>
            <Badge>Frontend: React</Badge>
            <Badge>UI: Tailwind</Badge>
          </div>
        </div>
      </div>
    </div>
  );
}
