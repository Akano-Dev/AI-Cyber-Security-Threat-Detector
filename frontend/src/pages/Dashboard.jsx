import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence, useReducedMotion, useMotionValue, useTransform, animate } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { BASE, WS_URL, HEALTH_URL, apiFetch } from "../api";

// ── icons (inline SVG, lucide-style — replaces emoji) ─────────────────────

const ICONS = {
  shield:   <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />,
  ban:      <><circle cx="12" cy="12" r="9" /><path d="m5.6 5.6 12.8 12.8" /></>,
  clock:    <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  alert:    <><path d="M10.3 3.8 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0z" /><path d="M12 9v4" /><path d="M12 17h.01" /></>,
  sun:      <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M5 5l1.4 1.4M17.6 17.6 19 19M2 12h2M20 12h2M5 19l1.4-1.4M17.6 6.4 19 5" /></>,
  moon:     <path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" />,
  search:   <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
  sliders:  <path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M2 14h4M10 8h4M18 16h4" />,
  zap:      <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z" />,
  download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10 5 5 5-5" /><path d="M12 15V3" /></>,
  check:    <path d="m20 6-11 11-5-5" />,
  chevron:  <path d="m6 9 6 6 6-6" />,
  reset:    <><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></>,
  activity: <path d="M22 12h-4l-3 9L9 3l-3 9H2" />,
};

function Icon({ name, className = "w-4 h-4", strokeWidth = 1.75 }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth}
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {ICONS[name]}
    </svg>
  );
}

// ── theme-aware primitives ────────────────────────────────────────────────

const card  = "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl";
const input = "w-full bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-600 rounded-lg px-3.5 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition font-mono";
const label = "text-[11px] font-medium uppercase tracking-wider text-zinc-400 dark:text-zinc-500";

// ── colour maps ───────────────────────────────────────────────────────────

const SEV = {
  high:   { dot: "bg-red-500",     badge: "text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-500/10 ring-1 ring-inset ring-red-600/20 dark:ring-red-500/25",       left: "border-l-red-500/70"     },
  medium: { dot: "bg-amber-500",   badge: "text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 ring-1 ring-inset ring-amber-600/20 dark:ring-amber-500/25", left: "border-l-amber-500/70" },
  low:    { dot: "bg-emerald-500", badge: "text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 ring-1 ring-inset ring-emerald-600/20 dark:ring-emerald-500/25", left: "border-l-emerald-500/70" },
};

const STATUS_MOTION = {
  new:     { backgroundColor: "rgba(99,102,241,0.10)",  color: "#6366f1", borderColor: "rgba(99,102,241,0.28)" },
  blocked: { backgroundColor: "rgba(239,68,68,0.10)",   color: "#ef4444", borderColor: "rgba(239,68,68,0.28)" },
  ignored: { backgroundColor: "rgba(113,113,122,0.12)", color: "#a1a1aa", borderColor: "rgba(113,113,122,0.28)" },
};

const TYPE_COLOR = {
  "SQL Injection": "#6366f1", "XSS": "#8b5cf6",
  "Path Traversal": "#f59e0b", "Command Injection": "#ef4444",
  "Suspicious User-Agent": "#0ea5e9", "Anomalous Payload": "#14b8a6",
  "Brute Force / Rate Abuse": "#ec4899",
};

const FILTERS = ["All", "New", "Blocked", "Ignored"];

function parseUTC(ts) { return new Date(ts.replace(" ", "T") + "Z"); }

// ── theme toggle ──────────────────────────────────────────────────────────

function ThemeToggle({ dark, setDark }) {
  return (
    <button
      onClick={() => setDark(d => !d)}
      title="Toggle theme"
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      className="h-8 w-8 flex items-center justify-center rounded-lg
                 text-zinc-500 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800
                 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition cursor-pointer"
    >
      <Icon name={dark ? "sun" : "moon"} className="w-4 h-4" />
    </button>
  );
}

// ── animated number ───────────────────────────────────────────────────────

function AnimatedNumber({ value }) {
  const reduced = useReducedMotion();
  const mv = useMotionValue(0);
  const rounded = useTransform(mv, v => Math.round(v));
  useEffect(() => {
    const c = animate(mv, value, { duration: reduced ? 0 : 0.6, ease: "easeOut" });
    return c.stop;
  }, [value]);
  return <motion.span>{rounded}</motion.span>;
}

// ── stat card ─────────────────────────────────────────────────────────────

function StatCard({ label: lbl, value, icon }) {
  return (
    <div className={`${card} p-5`}>
      <div className="flex items-center justify-between">
        <span className={label}>{lbl}</span>
        <span className="text-zinc-300 dark:text-zinc-600"><Icon name={icon} className="w-4 h-4" /></span>
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50 tabular-nums truncate">
        {typeof value === "number" ? <AnimatedNumber value={value} /> : value}
      </p>
    </div>
  );
}

function StatsBar({ threats }) {
  const s = useMemo(() => {
    const total    = threats.length;
    const blocked  = threats.filter(t => t.status === "blocked").length;
    const lastHour = threats.filter(t => parseUTC(t.timestamp) > new Date(Date.now() - 3_600_000)).length;
    const counts   = {};
    threats.forEach(t => { counts[t.threat_type] = (counts[t.threat_type] ?? 0) + 1; });
    const topType  = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";
    return { total, blocked, lastHour, topType };
  }, [threats]);

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <StatCard label="Total Threats" value={s.total}    icon="shield" />
      <StatCard label="Blocked IPs"   value={s.blocked}  icon="ban" />
      <StatCard label="Last Hour"     value={s.lastHour} icon="clock" />
      <StatCard label="Top Attack"    value={s.topType}  icon="alert" />
    </div>
  );
}

// ── chart ─────────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-1.5 shadow-md text-xs">
      <span className="font-medium text-zinc-700 dark:text-zinc-200">{p.name}</span>
      <span className="ml-2 tabular-nums text-zinc-400">{p.count}</span>
    </div>
  );
}

function ThreatChart({ threats }) {
  const reduced = useReducedMotion();
  const data = useMemo(() => {
    const counts = {};
    threats.forEach(t => { counts[t.threat_type] = (counts[t.threat_type] ?? 0) + 1; });
    return Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);
  }, [threats]);

  if (!data.length) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-400 dark:text-zinc-500">
          <Icon name="activity" className="w-4 h-4" />
        </span>
        <p className="mt-3 text-sm text-zinc-400 dark:text-zinc-500">No threat data yet.</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(data.length * 42, 120)}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 28, top: 2, bottom: 2 }}>
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: "#a1a1aa" }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12, fill: "#a1a1aa" }} axisLine={false} tickLine={false} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(161,161,170,0.08)" }} />
        <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={18}
             isAnimationActive={!reduced} animationDuration={600} animationEasing="ease-out">
          {data.map(e => <Cell key={e.name} fill={TYPE_COLOR[e.name] ?? "#6366f1"} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── confidence bar ────────────────────────────────────────────────────────

function ConfidenceBar({ value }) {
  if (value == null) return <span className="text-zinc-300 dark:text-zinc-600">—</span>;
  const color = value >= 80 ? "#ef4444" : value >= 55 ? "#f59e0b" : "#10b981";
  return (
    <span className="flex items-center gap-2">
      <span className="w-14 h-1 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden inline-block">
        <span style={{ width: `${value}%`, background: color }} className="block h-full rounded-full transition-all duration-500" />
      </span>
      <span style={{ color }} className="text-xs font-medium tabular-nums w-8">{value}%</span>
    </span>
  );
}

// ── status badge ──────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const reduced = useReducedMotion();
  return (
    <motion.span
      className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border capitalize"
      animate={STATUS_MOTION[status] ?? STATUS_MOTION.new}
      transition={{ duration: reduced ? 0 : 0.3 }}
    >
      {status}
    </motion.span>
  );
}

// ── skeleton ──────────────────────────────────────────────────────────────

function SkeletonTable() {
  return (
    <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="px-5 py-4 flex items-center gap-4 animate-pulse">
          <div className="h-3 w-6 bg-zinc-100 dark:bg-zinc-800 rounded" />
          <div className="h-3 w-36 bg-zinc-100 dark:bg-zinc-800 rounded" />
          <div className="h-3 w-24 bg-zinc-100 dark:bg-zinc-800 rounded" />
          <div className="h-3 w-28 bg-zinc-100 dark:bg-zinc-800 rounded" />
          <div className="h-3 flex-1 bg-zinc-100 dark:bg-zinc-800 rounded" />
          <div className="h-3 w-12 bg-zinc-100 dark:bg-zinc-800 rounded" />
          <div className="h-3 w-16 bg-zinc-100 dark:bg-zinc-800 rounded" />
        </div>
      ))}
    </div>
  );
}

// ── toast ─────────────────────────────────────────────────────────────────

function ToastItem({ message }) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      initial={{ opacity: 0, y: reduced ? 0 : 12, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: reduced ? 0 : 6, scale: 0.97 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={`${card} px-3.5 py-2.5 flex items-center gap-2.5 text-sm font-medium
                  text-zinc-700 dark:text-zinc-200 shadow-lg min-w-[220px]`}
    >
      <span className="w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center text-white flex-shrink-0">
        <Icon name="check" className="w-2.5 h-2.5" strokeWidth={3} />
      </span>
      {message}
    </motion.div>
  );
}

function ToastContainer({ toasts }) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 items-end">
      <AnimatePresence>{toasts.map(t => <ToastItem key={t.id} message={t.message} />)}</AnimatePresence>
    </div>
  );
}

// ── action buttons ────────────────────────────────────────────────────────

function ActionButtons({ threat, onUpdate, onToast }) {
  const [loading, setLoading] = useState(null);
  const reduced = useReducedMotion();

  async function act(action) {
    setLoading(action);
    try {
      await apiFetch(`/threats/${threat.id}/${action}`, { method: "POST" });
      const s = action === "block" ? "blocked" : "ignored";
      onUpdate(threat.id, s);
      onToast?.(action === "block" ? `IP ${threat.source_ip} blocked` : `Threat #${threat.id} ignored`);
    } finally { setLoading(null); }
  }

  if (threat.status !== "new") return null;
  return (
    <span className="flex gap-1.5">
      <motion.button onClick={() => act("block")} disabled={!!loading}
        whileTap={reduced ? {} : { scale: 0.94 }}
        className="px-2.5 py-1 rounded-md text-xs font-medium cursor-pointer transition
                   text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/25
                   hover:bg-red-50 dark:hover:bg-red-500/10
                   disabled:opacity-40 disabled:cursor-not-allowed">
        {loading === "block" ? "…" : "Block"}
      </motion.button>
      <motion.button onClick={() => act("ignore")} disabled={!!loading}
        whileTap={reduced ? {} : { scale: 0.94 }}
        className="px-2.5 py-1 rounded-md text-xs font-medium cursor-pointer transition
                   text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700
                   hover:bg-zinc-100 dark:hover:bg-zinc-800
                   disabled:opacity-40 disabled:cursor-not-allowed">
        {loading === "ignore" ? "…" : "Ignore"}
      </motion.button>
    </span>
  );
}

// ── collapsible panel shell ───────────────────────────────────────────────

function Panel({ icon, title, open, onToggle, children }) {
  return (
    <div className={card}>
      <button onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-3.5 cursor-pointer group">
        <span className="flex items-center gap-2 text-sm font-medium text-zinc-800 dark:text-zinc-100">
          <span className="text-zinc-400 dark:text-zinc-500"><Icon name={icon} className="w-4 h-4" /></span>
          {title}
        </span>
        <span className="text-zinc-400 dark:text-zinc-500 transition-transform duration-200" style={{ transform: open ? "rotate(180deg)" : "none" }}>
          <Icon name="chevron" className="w-4 h-4" />
        </span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── test detection ────────────────────────────────────────────────────────

function TestDetection() {
  const [open, setOpen] = useState(true);
  const [payload, setPayload] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true); setResult(null);
    try {
      const res = await fetch(`${BASE}/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_ip: "127.0.0.1", payload, user_agent: navigator.userAgent }),
      });
      setResult(await res.json());
    } catch { setResult({ error: "Request failed" }); }
    setLoading(false);
  }

  const rColor = result?.verdict === "threat" ? "text-red-600 dark:text-red-400"
               : result?.verdict === "safe"   ? "text-emerald-600 dark:text-emerald-400"
               : result?.verdict === "blocked"? "text-amber-600 dark:text-amber-400"
               : "text-zinc-500";

  return (
    <Panel icon="search" title="Test Detection" open={open} onToggle={() => setOpen(o => !o)}>
      <div className="px-5 pb-5 space-y-3 border-t border-zinc-100 dark:border-zinc-800 pt-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input value={payload} onChange={e => setPayload(e.target.value)}
            placeholder="Enter a payload to analyze…" required className={input} />
          <motion.button type="submit" disabled={loading}
            whileTap={{ scale: 0.97 }}
            className="px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition
                       bg-indigo-600 hover:bg-indigo-500 text-white
                       disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap">
            {loading ? "…" : "Analyze"}
          </motion.button>
        </form>
        {result && (
          <p className={`text-sm font-medium ${rColor}`}>
            {result.error                  && `Error: ${result.error}`}
            {result.verdict === "safe"     && "Safe — no threat detected."}
            {result.verdict === "blocked"  && `Blocked — ${result.source_ip} is on the blocklist.`}
            {result.verdict === "threat"   && <><strong>Threat detected</strong> — {result.threat_type} ({result.severity}, {result.confidence}% confidence)</>}
          </p>
        )}
      </div>
    </Panel>
  );
}

// ── settings panel ───────────────────────────────────────────────────────

function Settings({ onToast }) {
  const [open,   setOpen]   = useState(false);
  const [cfg,    setCfg]    = useState({ target_url: "", rate_limit: 20, rate_window: 60 });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiFetch("/config").then(r => r.json())
      .then(d => setCfg(d)).catch(() => {});
  }, []);

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await apiFetch("/config", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_url: cfg.target_url,
          rate_limit: Number(cfg.rate_limit),
          rate_window: Number(cfg.rate_window),
        }),
      });
      const updated = await res.json();
      setCfg(updated);
      onToast?.("Settings saved");
    } catch { onToast?.("Failed to save settings"); }
    setSaving(false);
  }

  const numInput = "w-full bg-zinc-50 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-lg px-3.5 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition tabular-nums";

  return (
    <Panel icon="sliders" title="Proxy Settings" open={open} onToggle={() => setOpen(o => !o)}>
      <form onSubmit={handleSave} className="px-5 pb-5 space-y-4 border-t border-zinc-100 dark:border-zinc-800 pt-4">
        <div>
          <p className={`${label} mb-1.5`}>Target URL</p>
          <input value={cfg.target_url} onChange={e => setCfg(c => ({ ...c, target_url: e.target.value }))}
            placeholder="https://your-site.com" className={input} />
          <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-1.5">All proxy traffic is forwarded here.</p>
        </div>

        <div className="flex gap-3">
          <div className="flex-1">
            <p className={`${label} mb-1.5`}>Rate Limit</p>
            <input type="number" min="1" value={cfg.rate_limit}
              onChange={e => setCfg(c => ({ ...c, rate_limit: e.target.value }))}
              className={numInput} />
            <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-1.5">Max requests…</p>
          </div>
          <div className="flex-1">
            <p className={`${label} mb-1.5`}>Window (sec)</p>
            <input type="number" min="1" value={cfg.rate_window}
              onChange={e => setCfg(c => ({ ...c, rate_window: e.target.value }))}
              className={numInput} />
            <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-1.5">…per this window.</p>
          </div>
        </div>

        <motion.button type="submit" disabled={saving}
          whileTap={{ scale: 0.98 }}
          className="w-full py-2 rounded-lg text-sm font-medium cursor-pointer transition
                     bg-indigo-600 hover:bg-indigo-500 text-white
                     disabled:opacity-50 disabled:cursor-not-allowed">
          {saving ? "Saving…" : "Save Settings"}
        </motion.button>
      </form>
    </Panel>
  );
}

// ── header status pill ────────────────────────────────────────────────────

function StatusPill({ tone, dot, pulse, children, className = "" }) {
  const tones = {
    green: "text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/20",
    red:   "text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20",
    muted: "text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800/60 border-zinc-200 dark:border-zinc-700",
  };
  const dots = { green: "bg-emerald-500", red: "bg-red-500", muted: "bg-zinc-400" };
  return (
    <span className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-md border ${tones[tone]} ${className}`}>
      {pulse ? (
        <motion.span className={`w-1.5 h-1.5 rounded-full ${dots[tone]} inline-block`}
          animate={{ opacity: [1, 0.3, 1], scale: [1, 1.4, 1] }}
          transition={{ duration: 1.6, repeat: Infinity }} />
      ) : (
        <span className={`w-1.5 h-1.5 rounded-full ${dots[tone]}`} />
      )}
      {children}
    </span>
  );
}

// ── secondary header link/button ──────────────────────────────────────────

const headerBtn =
  "flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-medium transition cursor-pointer " +
  "text-zinc-600 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-800 " +
  "hover:bg-zinc-100 dark:hover:bg-zinc-800";

// ── main dashboard ────────────────────────────────────────────────────────

export default function Dashboard({ dark, setDark }) {
  const [connected, setConnected] = useState(null);
  const [wsStatus,  setWsStatus]  = useState("connecting");
  const [threats,   setThreats]   = useState([]);
  const [filter,    setFilter]    = useState("All");
  const [loading,   setLoading]   = useState(true);
  const [toasts,    setToasts]    = useState([]);
  const reduced = useReducedMotion();

  function addToast(msg) {
    const id = Date.now();
    setToasts(p => [...p, { id, message: msg }]);
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 3000);
  }

  function updateThreatStatus(id, status) {
    setThreats(p => p.map(t => t.id === id ? { ...t, status } : t));
  }

  const rowVariants = {
    initial: { opacity: 0, y: reduced ? 0 : -8 },
    animate: { opacity: 1, y: 0, transition: { duration: reduced ? 0 : 0.2, ease: "easeOut" } },
    exit:    { opacity: 0,        transition: { duration: reduced ? 0 : 0.15 } },
  };

  useEffect(() => {
    fetch(HEALTH_URL).then(r => r.json())
      .then(d => setConnected(d.status === "ok")).catch(() => setConnected(false));

    fetch(`${BASE}/threats`).then(r => r.json())
      .then(d => { setThreats(d); setLoading(false); }).catch(() => setLoading(false));

    const ws = new WebSocket(WS_URL);
    ws.onopen    = () => setWsStatus("live");
    ws.onclose   = () => setWsStatus("disconnected");
    ws.onerror   = () => setWsStatus("disconnected");
    ws.onmessage = e => {
      const msg = JSON.parse(e.data);
      if (msg.event === "new_threat")    { const { event, ...t } = msg; setThreats(p => [t, ...p]); }
      else if (msg.event === "status_update") setThreats(p => p.map(t => t.id === msg.id ? { ...t, status: msg.status } : t));
      else if (msg.event === "demo_reset")    setThreats([]);
    };
    return () => ws.close();
  }, []);

  const displayed = filter === "All" ? threats : threats.filter(t => t.status === filter.toLowerCase());

  const TH = "px-4 py-3 text-left text-[10px] font-semibold tracking-wider uppercase text-zinc-400 dark:text-zinc-500";
  const TD = "px-4 py-3 align-middle";

  return (
    <div className="page-bg relative">
      <ToastContainer toasts={toasts} />
      <div className="relative z-10">

        {/* ── header ── */}
        <header className="sticky top-0 z-30 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800">
          <div className="max-w-[1300px] mx-auto px-6 h-16 flex items-center justify-between gap-4">

            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
                <Icon name="shield" className="w-[18px] h-[18px]" />
              </div>
              <div className="leading-tight">
                <span className="font-semibold text-zinc-900 dark:text-white text-[15px] tracking-tight">ACSTD</span>
                <span className="hidden sm:inline text-zinc-400 dark:text-zinc-500 text-sm ml-2">AI Cyber Security Threat Detector</span>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap justify-end">
              {/* backend status */}
              <span className="hidden sm:inline-flex">
                <StatusPill tone={connected ? "green" : "red"}>
                  {connected ? "API Online" : "API Down"}
                </StatusPill>
              </span>

              {/* ws status */}
              {wsStatus === "live"
                ? <StatusPill tone="green" pulse>Live</StatusPill>
                : <StatusPill tone="muted">{wsStatus === "connecting" ? "Connecting…" : "Offline"}</StatusPill>}

              {/* demo site */}
              <a href={`${BASE}/proxy/login?demo=true`} target="_blank" rel="noreferrer" className={headerBtn}>
                <Icon name="zap" className="w-3.5 h-3.5" /><span className="hidden sm:inline">Demo</span>
              </a>

              {/* export */}
              <a href={`${BASE}/export`} download className={headerBtn}>
                <Icon name="download" className="w-3.5 h-3.5" /><span className="hidden sm:inline">Export</span>
              </a>

              {/* theme toggle */}
              <ThemeToggle dark={dark} setDark={setDark} />
            </div>
          </div>
        </header>

        {/* ── body ── */}
        <main className="max-w-[1300px] mx-auto px-6 py-8 space-y-6">

          <StatsBar threats={threats} />

          {/* chart + side panels */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
            <div className={`${card} lg:col-span-2 p-6`}>
              <p className={`${label} mb-4`}>Threats by Type</p>
              <ThreatChart threats={threats} />
            </div>
            <div className="flex flex-col gap-5">
              <TestDetection />
              <Settings onToast={addToast} />
            </div>
          </div>

          {/* threat table */}
          <div className={`${card} overflow-hidden`}>

            {/* toolbar */}
            <div className="px-5 py-3.5 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-100 dark:border-zinc-800">
              <h2 className="font-medium text-zinc-900 dark:text-white text-sm">
                Detected Threats
                <span className="ml-2 text-zinc-400 dark:text-zinc-500 font-normal tabular-nums">({displayed.length})</span>
              </h2>
              <div className="flex items-center gap-2 flex-wrap">
                {/* segmented filter control */}
                <div className="inline-flex p-0.5 rounded-lg bg-zinc-100 dark:bg-zinc-800/70 border border-zinc-200 dark:border-zinc-800">
                  {FILTERS.map(f => (
                    <button key={f} onClick={() => setFilter(f)}
                      className={`px-3 py-1 rounded-md text-xs font-medium transition cursor-pointer ${
                        filter === f
                          ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-white shadow-sm"
                          : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
                      }`}>
                      {f}
                    </button>
                  ))}
                </div>
                <button onClick={async () => {
                  await apiFetch("/demo/reset", { method: "POST" });
                  setThreats([]);
                  addToast("Demo reset — all threats cleared");
                }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer border transition
                             text-zinc-600 dark:text-zinc-300 border-zinc-200 dark:border-zinc-800
                             hover:bg-zinc-100 dark:hover:bg-zinc-800">
                  <Icon name="reset" className="w-3.5 h-3.5" /> Reset Demo
                </button>
              </div>
            </div>

            {/* content */}
            {loading ? <SkeletonTable /> : (
              <AnimatePresence mode="wait">
                <motion.div key={filter}
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                  transition={{ duration: reduced ? 0 : 0.15 }}>
                  {displayed.length === 0 ? (
                    <div className="py-16 flex flex-col items-center text-center">
                      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-400 dark:text-zinc-500">
                        <Icon name="search" className="w-5 h-5" />
                      </span>
                      <p className="mt-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">No threats to show</p>
                      <p className="mt-1 text-sm text-zinc-400 dark:text-zinc-500">
                        {filter === "All" ? "Detected threats will appear here in real time." : `No threats match the “${filter}” filter.`}
                      </p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse">
                        <thead>
                          <tr className="bg-zinc-50 dark:bg-zinc-800/40 border-b border-zinc-100 dark:border-zinc-800">
                            {["ID", "Timestamp", "Source IP", "Type", "Payload", "Severity", "Confidence", "Status", "Actions"].map(h => (
                              <th key={h} className={TH}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                          <AnimatePresence initial={false}>
                            {displayed.map(t => (
                              <motion.tr key={t.id}
                                variants={rowVariants} initial="initial" animate="animate" exit="exit"
                                layout="position"
                                whileHover={reduced ? {} : { backgroundColor: "rgba(99,102,241,0.04)" }}
                                className={`border-l-2 ${SEV[t.severity]?.left ?? "border-l-zinc-300 dark:border-l-zinc-700"}`}
                              >
                                <td className={`${TD} font-mono text-xs text-zinc-400 dark:text-zinc-500`}>#{t.id}</td>
                                <td className={`${TD} text-xs text-zinc-500 dark:text-zinc-400 whitespace-nowrap tabular-nums`}>{t.timestamp}</td>
                                <td className={`${TD} font-mono text-xs text-zinc-700 dark:text-zinc-300`}>{t.source_ip}</td>
                                <td className={`${TD} text-zinc-800 dark:text-zinc-200 font-medium whitespace-nowrap`}>{t.threat_type}</td>
                                <td className={`${TD} font-mono text-xs text-zinc-500 dark:text-zinc-400 max-w-[180px] truncate`}>{t.payload}</td>
                                <td className={TD}>
                                  <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-md capitalize ${SEV[t.severity]?.badge ?? ""}`}>
                                    <span className={`w-1.5 h-1.5 rounded-full ${SEV[t.severity]?.dot ?? "bg-zinc-400"}`} />
                                    {t.severity}
                                  </span>
                                </td>
                                <td className={TD}><ConfidenceBar value={t.confidence} /></td>
                                <td className={TD}><StatusBadge status={t.status} /></td>
                                <td className={TD}><ActionButtons threat={t} onUpdate={updateThreatStatus} onToast={addToast} /></td>
                              </motion.tr>
                            ))}
                          </AnimatePresence>
                        </tbody>
                      </table>
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
