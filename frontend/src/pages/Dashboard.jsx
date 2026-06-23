import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence, useReducedMotion, useMotionValue, useTransform, animate } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

// ── theme-aware primitives ────────────────────────────────────────────────

const card   = "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/60 rounded-2xl shadow-sm";
const input  = "w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-cyan-500/40 transition font-mono";
const label  = "text-[11px] font-semibold tracking-widest uppercase text-slate-400 dark:text-slate-500";

// ── colour maps ───────────────────────────────────────────────────────────

const SEV = {
  high:   { dot: "bg-red-500",     text: "text-red-500 dark:text-red-400",     badge: "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/20",   left: "border-l-red-500"   },
  medium: { dot: "bg-amber-500",   text: "text-amber-500 dark:text-amber-400", badge: "bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20", left: "border-l-amber-500" },
  low:    { dot: "bg-emerald-500", text: "text-emerald-500 dark:text-emerald-400", badge: "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20", left: "border-l-emerald-500" },
};

const STATUS_MOTION = {
  new:     { backgroundColor: "rgba(6,182,212,0.10)",   color: "#06b6d4", borderColor: "rgba(6,182,212,0.25)" },
  blocked: { backgroundColor: "rgba(239,68,68,0.10)",   color: "#ef4444", borderColor: "rgba(239,68,68,0.25)" },
  ignored: { backgroundColor: "rgba(148,163,184,0.10)", color: "#94a3b8", borderColor: "rgba(148,163,184,0.25)" },
};

const TYPE_COLOR = {
  "SQL Injection": "#7c3aed", "XSS": "#db2777",
  "Path Traversal": "#ea580c", "Command Injection": "#ef4444",
  "Suspicious User-Agent": "#0891b2", "Anomalous Payload": "#4f46e5",
};

const FILTERS = ["All", "New", "Blocked", "Ignored"];

function parseUTC(ts) { return new Date(ts.replace(" ", "T") + "Z"); }

// ── theme toggle ──────────────────────────────────────────────────────────

function ThemeToggle({ dark, setDark }) {
  return (
    <button
      onClick={() => setDark(d => !d)}
      title="Toggle theme"
      className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-medium
                 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700
                 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700
                 transition-all duration-200 cursor-pointer select-none"
    >
      <span className="text-base">{dark ? "☀️" : "🌙"}</span>
      <span className="hidden sm:inline">{dark ? "Light" : "Dark"}</span>
    </button>
  );
}

// ── animated number ───────────────────────────────────────────────────────

function AnimatedNumber({ value }) {
  const reduced = useReducedMotion();
  const mv = useMotionValue(0);
  const rounded = useTransform(mv, v => Math.round(v));
  useEffect(() => {
    const c = animate(mv, value, { duration: reduced ? 0 : 0.7, ease: "easeOut" });
    return c.stop;
  }, [value]);
  return <motion.span>{rounded}</motion.span>;
}

// ── stat card ─────────────────────────────────────────────────────────────

function StatCard({ label: lbl, value, icon, accent }) {
  return (
    <div className={`${card} flex-1 min-w-[140px] p-5 relative overflow-hidden`}>
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl" style={{ background: accent }} />
      <div className="flex items-center justify-between mb-3">
        <span className={`${label}`}>{lbl}</span>
        <span className="text-xl">{icon}</span>
      </div>
      <p className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
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
    <div className="flex gap-3 flex-wrap">
      <StatCard lbl="Total Threats" value={s.total}    icon="🛡" accent="#06b6d4" />
      <StatCard lbl="Blocked IPs"   value={s.blocked}  icon="🚫" accent="#ef4444" />
      <StatCard lbl="Last Hour"     value={s.lastHour} icon="⏱" accent="#f59e0b" />
      <StatCard lbl="Top Attack"    value={s.topType}  icon="⚠️" accent="#7c3aed" />
    </div>
  );
}

// ── chart ─────────────────────────────────────────────────────────────────

function ThreatChart({ threats }) {
  const reduced = useReducedMotion();
  const data = useMemo(() => {
    const counts = {};
    threats.forEach(t => { counts[t.threat_type] = (counts[t.threat_type] ?? 0) + 1; });
    return Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count);
  }, [threats]);

  if (!data.length) return <p className="text-slate-400 text-sm py-6 text-center">No threat data yet.</p>;

  return (
    <ResponsiveContainer width="100%" height={Math.max(data.length * 46, 120)}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 32, top: 4, bottom: 4 }}>
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={{ fill: "rgba(148,163,184,0.06)" }}
          contentStyle={{ background: "var(--tw-tooltip-bg, #1e293b)", border: "1px solid #334155", borderRadius: 12, color: "#f1f5f9", fontSize: 13, padding: "8px 14px" }}
        />
        <Bar dataKey="count" radius={[0, 8, 8, 0]} maxBarSize={22}
             isAnimationActive={!reduced} animationDuration={700} animationEasing="ease-out">
          {data.map(e => <Cell key={e.name} fill={TYPE_COLOR[e.name] ?? "#06b6d4"} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── confidence bar ────────────────────────────────────────────────────────

function ConfidenceBar({ value }) {
  if (value == null) return <span className="text-slate-400">—</span>;
  const color = value >= 80 ? "#ef4444" : value >= 55 ? "#f59e0b" : "#10b981";
  return (
    <span className="flex items-center gap-2">
      <span className="w-14 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden inline-block">
        <span style={{ width: `${value}%`, background: color }} className="block h-full rounded-full transition-all duration-500" />
      </span>
      <span style={{ color }} className="text-xs font-semibold tabular-nums w-8">{value}%</span>
    </span>
  );
}

// ── status badge ──────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const reduced = useReducedMotion();
  return (
    <motion.span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border"
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
    <div className="divide-y divide-slate-100 dark:divide-slate-800">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="px-5 py-4 flex items-center gap-4 animate-pulse">
          <div className="h-3 w-6 bg-slate-200 dark:bg-slate-800 rounded-full" />
          <div className="h-3 w-36 bg-slate-200 dark:bg-slate-800 rounded-full" />
          <div className="h-3 w-24 bg-slate-200 dark:bg-slate-800 rounded-full" />
          <div className="h-3 w-28 bg-slate-200 dark:bg-slate-800 rounded-full" />
          <div className="h-3 flex-1 bg-slate-200 dark:bg-slate-800 rounded-full" />
          <div className="h-3 w-12 bg-slate-200 dark:bg-slate-800 rounded-full" />
          <div className="h-3 w-16 bg-slate-200 dark:bg-slate-800 rounded-full" />
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
      initial={{ opacity: 0, y: reduced ? 0 : 16, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: reduced ? 0 : 8, scale: 0.95 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={`${card} px-4 py-3 flex items-center gap-3 text-sm font-medium
                  text-slate-700 dark:text-slate-200 shadow-lg min-w-[220px]`}
    >
      <span className="w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center text-white text-xs flex-shrink-0">✓</span>
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
      await fetch(`http://localhost:8000/threats/${threat.id}/${action}`, { method: "POST" });
      const s = action === "block" ? "blocked" : "ignored";
      onUpdate(threat.id, s);
      onToast?.(action === "block" ? `IP ${threat.source_ip} blocked` : `Threat #${threat.id} ignored`);
    } finally { setLoading(null); }
  }

  if (threat.status !== "new") return null;
  return (
    <span className="flex gap-2">
      <motion.button onClick={() => act("block")} disabled={!!loading}
        whileTap={reduced ? {} : { scale: 0.9 }}
        className="px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-all duration-150
                   bg-red-50 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20
                   text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/25
                   disabled:opacity-40 disabled:cursor-not-allowed shadow-sm">
        {loading === "block" ? "…" : "Block"}
      </motion.button>
      <motion.button onClick={() => act("ignore")} disabled={!!loading}
        whileTap={reduced ? {} : { scale: 0.9 }}
        className="px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-all duration-150
                   bg-slate-100 hover:bg-slate-200 dark:bg-slate-700/50 dark:hover:bg-slate-700
                   text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-600
                   disabled:opacity-40 disabled:cursor-not-allowed shadow-sm">
        {loading === "ignore" ? "…" : "Ignore"}
      </motion.button>
    </span>
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
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_ip: "127.0.0.1", payload, user_agent: navigator.userAgent }),
      });
      setResult(await res.json());
    } catch { setResult({ error: "Request failed" }); }
    setLoading(false);
  }

  const rColor = result?.verdict === "threat" ? "text-red-500 dark:text-red-400"
               : result?.verdict === "safe"   ? "text-emerald-600 dark:text-emerald-400"
               : result?.verdict === "blocked"? "text-orange-600 dark:text-orange-400"
               : "text-slate-500";

  return (
    <div className={card}>
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-4 cursor-pointer">
        <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">🔍 Test Detection</span>
        <span className="text-slate-400 text-xs">{open ? "▲" : "▼"}</span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-3 border-t border-slate-100 dark:border-slate-800 pt-4">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <input value={payload} onChange={e => setPayload(e.target.value)}
                  placeholder="Enter a payload to analyze…" required className={input} />
                <motion.button type="submit" disabled={loading}
                  whileTap={{ scale: 0.96 }}
                  className="px-4 py-2.5 rounded-xl text-sm font-semibold cursor-pointer transition-all
                             bg-cyan-500 hover:bg-cyan-400 text-white shadow-sm shadow-cyan-500/20
                             disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap">
                  {loading ? "…" : "Analyze"}
                </motion.button>
              </form>
              {result && (
                <p className={`text-sm font-medium ${rColor}`}>
                  {result.error                  && `Error: ${result.error}`}
                  {result.verdict === "safe"     && "✅ Safe — no threat detected."}
                  {result.verdict === "blocked"  && `🚫 Blocked — ${result.source_ip} is on the blocklist.`}
                  {result.verdict === "threat"   && <>⚠️ <strong>Threat detected</strong> — {result.threat_type} ({result.severity}, {result.confidence}% confidence)</>}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── settings panel ───────────────────────────────────────────────────────

function Settings({ onToast }) {
  const [open,   setOpen]   = useState(false);
  const [cfg,    setCfg]    = useState({ target_url: "", rate_limit: 20, rate_window: 60 });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/config").then(r => r.json())
      .then(d => setCfg(d)).catch(() => {});
  }, []);

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await fetch("http://localhost:8000/config", {
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

  const numInput = "w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-cyan-500/40 transition tabular-nums";

  return (
    <div className={card}>
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-4 cursor-pointer">
        <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">⚙️ Proxy Settings</span>
        <span className="text-slate-400 text-xs">{open ? "▲" : "▼"}</span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <form onSubmit={handleSave} className="px-5 pb-5 space-y-4 border-t border-slate-100 dark:border-slate-800 pt-4">

              <div>
                <p className={`${label} mb-1.5`}>Target URL</p>
                <input value={cfg.target_url} onChange={e => setCfg(c => ({ ...c, target_url: e.target.value }))}
                  placeholder="https://your-site.com" className={input} />
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">All proxy traffic is forwarded here.</p>
              </div>

              <div className="flex gap-3">
                <div className="flex-1">
                  <p className={`${label} mb-1.5`}>Rate Limit</p>
                  <input type="number" min="1" value={cfg.rate_limit}
                    onChange={e => setCfg(c => ({ ...c, rate_limit: e.target.value }))}
                    className={numInput} />
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Max requests…</p>
                </div>
                <div className="flex-1">
                  <p className={`${label} mb-1.5`}>Window (sec)</p>
                  <input type="number" min="1" value={cfg.rate_window}
                    onChange={e => setCfg(c => ({ ...c, rate_window: e.target.value }))}
                    className={numInput} />
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">…per this window.</p>
                </div>
              </div>

              <motion.button type="submit" disabled={saving}
                whileTap={{ scale: 0.96 }}
                className="w-full py-2.5 rounded-xl text-sm font-semibold cursor-pointer transition-all
                           bg-cyan-500 hover:bg-cyan-400 text-white shadow-sm shadow-cyan-500/20
                           disabled:opacity-50 disabled:cursor-not-allowed">
                {saving ? "Saving…" : "Save Settings"}
              </motion.button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

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
    initial: { opacity: 0, y: reduced ? 0 : -12 },
    animate: { opacity: 1, y: 0, transition: { duration: reduced ? 0 : 0.2, ease: "easeOut" } },
    exit:    { opacity: 0,        transition: { duration: reduced ? 0 : 0.15 } },
  };

  const glowAnim = reduced ? {} : {
    animate: { textShadow: ["0 0 0px rgba(239,68,68,0)", "0 0 8px rgba(239,68,68,0.6)", "0 0 0px rgba(239,68,68,0)"] },
    transition: { duration: 2.2, repeat: Infinity, ease: "easeInOut" },
  };

  useEffect(() => {
    fetch("http://localhost:8000/health").then(r => r.json())
      .then(d => setConnected(d.status === "ok")).catch(() => setConnected(false));

    fetch("http://localhost:8000/threats").then(r => r.json())
      .then(d => { setThreats(d); setLoading(false); }).catch(() => setLoading(false));

    const ws = new WebSocket("ws://localhost:8000/ws");
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

  const TH = "px-4 py-3.5 text-left text-[10px] font-semibold tracking-widest uppercase text-slate-400 dark:text-slate-500";
  const TD = "px-4 py-3.5 align-middle";

  return (
    <div className="page-bg relative">
      <ToastContainer toasts={toasts} />
      <div className="relative z-10">

        {/* ── header ── */}
        <header className="sticky top-0 z-30 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
          <div className="max-w-[1300px] mx-auto px-6 h-16 flex items-center justify-between gap-4">

            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-cyan-500 flex items-center justify-center shadow shadow-cyan-500/30">
                <span className="text-white text-sm">🛡</span>
              </div>
              <div>
                <span className="font-bold text-slate-900 dark:text-white text-base tracking-tight">ACSTD</span>
                <span className="hidden sm:inline text-slate-400 dark:text-slate-500 text-sm ml-2">AI Cyber Security Threat Detector</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              {/* backend status */}
              <span className={`hidden sm:flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-xl border ${
                connected
                  ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20"
                  : "bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 border-red-200 dark:border-red-500/20"
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-emerald-500" : "bg-red-500"}`} />
                {connected ? "API Online" : "API Down"}
              </span>

              {/* ws status */}
              <span className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border ${
                wsStatus === "live"
                  ? "bg-cyan-50 dark:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-200 dark:border-cyan-500/20"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-500 border-slate-200 dark:border-slate-700"
              }`}>
                {wsStatus === "live"
                  ? <>
                      <motion.span className="w-1.5 h-1.5 rounded-full bg-cyan-500 inline-block"
                        animate={{ opacity: [1, 0.2, 1], scale: [1, 1.5, 1] }}
                        transition={{ duration: 1.6, repeat: Infinity }} />
                      LIVE
                    </>
                  : <>{wsStatus === "connecting" ? "WS Connecting…" : "WS Offline"}</>
                }
              </span>

              {/* demo site */}
              <a href="http://localhost:8000/proxy/login?demo=true" target="_blank" rel="noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all
                           bg-violet-50 hover:bg-violet-100 dark:bg-violet-500/10 dark:hover:bg-violet-500/20
                           text-violet-600 dark:text-violet-400 border border-violet-200 dark:border-violet-500/25">
                ⚡ Demo
              </a>

              {/* export */}
              <a href="http://localhost:8000/export" download
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all
                           bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700
                           text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                ⬇ Export
              </a>

              {/* theme toggle */}
              <ThemeToggle dark={dark} setDark={setDark} />
            </div>
          </div>
        </header>

        {/* ── body ── */}
        <main className="max-w-[1300px] mx-auto px-6 py-8 space-y-6">

          <StatsBar threats={threats} />

          {/* chart + test detection */}
          <div className="flex gap-5 flex-wrap items-start">
            <div className={`${card} flex-1 min-w-[340px] p-6`}>
              <p className={`${label} mb-4`}>Threats by Type</p>
              <ThreatChart threats={threats} />
            </div>
            <div className="flex-1 min-w-[300px] max-w-[420px] flex flex-col gap-5">
              <TestDetection />
              <Settings onToast={addToast} />
            </div>
          </div>

          {/* threat table */}
          <div className={`${card} overflow-hidden`}>

            {/* toolbar */}
            <div className="px-6 py-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h2 className="font-semibold text-slate-900 dark:text-white text-base">
                  Detected Threats
                  <span className="ml-2 text-slate-400 dark:text-slate-500 font-normal text-sm">({displayed.length})</span>
                </h2>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {FILTERS.map(f => (
                  <button key={f} onClick={() => setFilter(f)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-150 cursor-pointer border ${
                      filter === f
                        ? "bg-cyan-500 text-white border-cyan-500 shadow-sm shadow-cyan-500/20"
                        : "bg-transparent text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
                    }`}>
                    {f}
                  </button>
                ))}
                <button onClick={async () => {
                  await fetch("http://localhost:8000/demo/reset", { method: "POST" });
                  setThreats([]);
                  addToast("Demo reset — all threats cleared");
                }}
                  className="px-3.5 py-1.5 rounded-xl text-xs font-semibold cursor-pointer border transition-all
                             bg-transparent text-violet-500 dark:text-violet-400 border-violet-300 dark:border-violet-500/40
                             hover:bg-violet-50 dark:hover:bg-violet-500/10">
                  ↺ Reset Demo
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
                    <div className="py-16 text-center">
                      <p className="text-4xl mb-3">🔍</p>
                      <p className="text-slate-400 dark:text-slate-500 text-sm">No threats match this filter.</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border-collapse">
                        <thead>
                          <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
                            {["ID", "Timestamp", "Source IP", "Type", "Payload", "Severity", "Confidence", "Status", "Actions"].map(h => (
                              <th key={h} className={TH}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          <AnimatePresence initial={false}>
                            {displayed.map(t => (
                              <motion.tr key={t.id}
                                variants={rowVariants} initial="initial" animate="animate" exit="exit"
                                layout="position"
                                whileHover={reduced ? {} : { backgroundColor: "rgba(6,182,212,0.03)" }}
                                className={`border-l-2 ${SEV[t.severity]?.left ?? "border-l-slate-300"}`}
                              >
                                <td className={`${TD} font-mono text-xs text-slate-400 dark:text-slate-500`}>#{t.id}</td>
                                <td className={`${TD} text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap`}>{t.timestamp}</td>
                                <td className={`${TD} font-mono text-xs text-slate-700 dark:text-slate-300`}>{t.source_ip}</td>
                                <td className={`${TD} text-slate-800 dark:text-slate-200 font-medium whitespace-nowrap`}>{t.threat_type}</td>
                                <td className={`${TD} font-mono text-xs text-slate-500 dark:text-slate-400 max-w-[180px] truncate`}>{t.payload}</td>
                                <td className={TD}>
                                  <motion.span
                                    className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg ${SEV[t.severity]?.badge ?? ""}`}
                                    {...(t.severity === "high" ? glowAnim : {})}
                                  >
                                    <span className={`w-1.5 h-1.5 rounded-full ${SEV[t.severity]?.dot ?? "bg-slate-400"}`} />
                                    {t.severity}
                                  </motion.span>
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
