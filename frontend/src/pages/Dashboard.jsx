import { useEffect, useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

// ── constants ──────────────────────────────────────────────────────────────

const SEV_COLOR = { high: "#dc2626", medium: "#d97706", low: "#16a34a" };

const TYPE_COLOR = {
  "SQL Injection":         "#7c3aed",
  "XSS":                   "#db2777",
  "Path Traversal":        "#ea580c",
  "Command Injection":     "#dc2626",
  "Suspicious User-Agent": "#0891b2",
  "Anomalous Payload":     "#4f46e5",
};

const STATUS_STYLE = {
  new:     { background: "#dbeafe", color: "#1d4ed8" },
  blocked: { background: "#fee2e2", color: "#b91c1c" },
  ignored: { background: "#f3f4f6", color: "#6b7280" },
};

const FILTERS = ["All", "New", "Blocked", "Ignored"];

function parseUTC(ts) {
  return new Date(ts.replace(" ", "T") + "Z");
}

// ── small components ───────────────────────────────────────────────────────

function StatCard({ label, value, accent = "#3b82f6" }) {
  return (
    <div style={{
      background: "#fff", borderRadius: 10, padding: "1rem 1.5rem", flex: 1, minWidth: 130,
      boxShadow: "0 1px 4px rgba(0,0,0,.08)", borderTop: `3px solid ${accent}`,
    }}>
      <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color: "#0f172a", lineHeight: 1.2 }}>{value}</div>
    </div>
  );
}

function StatsBar({ threats }) {
  const s = useMemo(() => {
    const total    = threats.length;
    const blocked  = threats.filter(t => t.status === "blocked").length;
    const hourAgo  = new Date(Date.now() - 3_600_000);
    const lastHour = threats.filter(t => parseUTC(t.timestamp) > hourAgo).length;
    const counts   = {};
    threats.forEach(t => { counts[t.threat_type] = (counts[t.threat_type] ?? 0) + 1; });
    const topType  = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";
    return { total, blocked, lastHour, topType };
  }, [threats]);

  return (
    <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
      <StatCard label="Total Threats" value={s.total}    accent="#3b82f6" />
      <StatCard label="Blocked"       value={s.blocked}  accent="#dc2626" />
      <StatCard label="Last Hour"     value={s.lastHour} accent="#d97706" />
      <StatCard label="Top Attack"    value={s.topType}  accent="#7c3aed" />
    </div>
  );
}

function ThreatChart({ threats }) {
  const data = useMemo(() => {
    const counts = {};
    threats.forEach(t => { counts[t.threat_type] = (counts[t.threat_type] ?? 0) + 1; });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }, [threats]);

  if (data.length === 0) {
    return <p style={{ color: "#94a3b8", padding: "1rem 0", margin: 0 }}>No data yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(data.length * 44, 120)}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 32, top: 4, bottom: 4 }}>
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" width={155} tick={{ fontSize: 12, fill: "#374151" }} axisLine={false} tickLine={false} />
        <Tooltip
          cursor={{ fill: "#f8fafc" }}
          contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 13 }}
        />
        <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={26}>
          {data.map(entry => (
            <Cell key={entry.name} fill={TYPE_COLOR[entry.name] ?? "#3b82f6"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function ConfidenceBar({ value }) {
  if (value == null) return <span style={{ color: "#cbd5e1" }}>—</span>;
  const color = value >= 80 ? "#dc2626" : value >= 55 ? "#d97706" : "#16a34a";
  return (
    <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ width: 52, height: 7, background: "#e2e8f0", borderRadius: 4, overflow: "hidden", display: "inline-block" }}>
        <span style={{ display: "block", width: `${value}%`, height: "100%", background: color }} />
      </span>
      <span style={{ color, fontWeight: 700, fontSize: 12, minWidth: 34 }}>{value}%</span>
    </span>
  );
}

function StatusBadge({ status }) {
  const s = STATUS_STYLE[status] ?? STATUS_STYLE.new;
  return (
    <span style={{ ...s, padding: "2px 9px", borderRadius: 10, fontSize: 12, fontWeight: 600 }}>
      {status}
    </span>
  );
}

function ActionButtons({ threat, onUpdate }) {
  const [loading, setLoading] = useState(null);

  async function act(action) {
    setLoading(action);
    try {
      await fetch(`http://localhost:8000/threats/${threat.id}/${action}`, { method: "POST" });
      onUpdate(threat.id, action === "block" ? "blocked" : "ignored");
    } finally {
      setLoading(null);
    }
  }

  if (threat.status !== "new") return null;
  return (
    <span style={{ display: "flex", gap: 4 }}>
      <button onClick={() => act("block")}  disabled={!!loading} style={abtn("#b91c1c")}>
        {loading === "block"  ? "…" : "Block"}
      </button>
      <button onClick={() => act("ignore")} disabled={!!loading} style={abtn("#6b7280")}>
        {loading === "ignore" ? "…" : "Ignore"}
      </button>
    </span>
  );
}
function abtn(bg) {
  return { padding: "2px 10px", fontSize: 12, cursor: "pointer", borderRadius: 5,
           border: "none", background: bg, color: "#fff", fontWeight: 600 };
}

function TestDetection() {
  const [open,    setOpen]    = useState(true);
  const [payload, setPayload] = useState("");
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_ip: "127.0.0.1", payload, user_agent: navigator.userAgent }),
      });
      setResult(await res.json());
    } catch {
      setResult({ error: "Request failed" });
    }
    setLoading(false);
  }

  const rColor = result?.verdict === "threat"  ? "#dc2626"
               : result?.verdict === "safe"    ? "#16a34a"
               : result?.verdict === "blocked" ? "#b91c1c"
               : "#555";

  return (
    <div style={{ background: "#fff", borderRadius: 10, padding: "1.1rem 1.4rem",
                  boxShadow: "0 1px 4px rgba(0,0,0,.08)" }}>
      <div onClick={() => setOpen(o => !o)}
           style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
                    cursor: "pointer", userSelect: "none" }}>
        <span style={{ fontWeight: 600, fontSize: 14, color: "#0f172a" }}>🔍 Test Detection</span>
        <span style={{ fontSize: 12, color: "#94a3b8" }}>{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <div style={{ marginTop: 12 }}>
          <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8 }}>
            <input
              value={payload}
              onChange={e => setPayload(e.target.value)}
              placeholder="Type a payload and analyze…"
              style={{ flex: 1, padding: "7px 10px", fontSize: 13, border: "1px solid #cbd5e1",
                       borderRadius: 6, outline: "none" }}
              required
            />
            <button type="submit" disabled={loading}
              style={{ padding: "7px 16px", fontSize: 13, cursor: "pointer", borderRadius: 6,
                       border: "none", background: "#0f172a", color: "#fff", fontWeight: 600 }}>
              {loading ? "…" : "Analyze"}
            </button>
          </form>
          {result && (
            <div style={{ marginTop: 10, fontSize: 13, color: rColor, fontWeight: 500 }}>
              {result.error                 && `Error: ${result.error}`}
              {result.verdict === "safe"    && "✅ Safe — no threat detected."}
              {result.verdict === "blocked" && `🚫 Blocked — ${result.source_ip} is on the blocklist.`}
              {result.verdict === "threat"  &&
                <>⚠️ <strong>Threat detected</strong> — {result.threat_type} ({result.severity}, {result.confidence}% confidence)</>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── main dashboard ─────────────────────────────────────────────────────────

export default function Dashboard() {
  const [connected, setConnected] = useState(null);
  const [wsStatus,  setWsStatus]  = useState("connecting");
  const [threats,   setThreats]   = useState([]);
  const [filter,    setFilter]    = useState("All");

  function updateThreatStatus(id, status) {
    setThreats(prev => prev.map(t => t.id === id ? { ...t, status } : t));
  }

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then(r => r.json())
      .then(d => setConnected(d.status === "ok"))
      .catch(() => setConnected(false));

    fetch("http://localhost:8000/threats")
      .then(r => r.json())
      .then(setThreats)
      .catch(() => {});

    const ws = new WebSocket("ws://localhost:8000/ws");
    ws.onopen    = () => setWsStatus("live");
    ws.onclose   = () => setWsStatus("disconnected");
    ws.onerror   = () => setWsStatus("disconnected");
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.event === "new_threat") {
        const { event, ...threat } = msg;
        setThreats(prev => [threat, ...prev]);
      } else if (msg.event === "status_update") {
        setThreats(prev => prev.map(t => t.id === msg.id ? { ...t, status: msg.status } : t));
      }
    };
    return () => ws.close();
  }, []);

  const displayed = filter === "All"
    ? threats
    : threats.filter(t => t.status === filter.toLowerCase());

  return (
    <div style={{ minHeight: "100vh", background: "#f1f5f9", fontFamily: "system-ui, -apple-system, sans-serif" }}>

      {/* ── header ── */}
      <header style={{
        background: "#0f172a", color: "#fff", padding: "0 2rem", height: 54,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, zIndex: 10,
      }}>
        <span style={{ fontWeight: 700, fontSize: 17, letterSpacing: -0.3 }}>
          🛡 ACSTD
          <span style={{ fontWeight: 400, fontSize: 13, color: "#94a3b8", marginLeft: 10 }}>
            AI Cyber Security Threat Detector
          </span>
        </span>
        <div style={{ display: "flex", gap: 12, alignItems: "center", fontSize: 13 }}>
          <span style={{ color: connected ? "#4ade80" : "#f87171" }}>
            {connected ? "● Backend" : "○ Backend offline"}
          </span>
          <span style={{
            padding: "2px 10px", borderRadius: 10, fontSize: 12, fontWeight: 600,
            background: wsStatus === "live" ? "#16a34a" : "#475569", color: "#fff",
          }}>
            {wsStatus === "live" ? "● LIVE" : wsStatus === "connecting" ? "connecting…" : "○ offline"}
          </span>
        </div>
      </header>

      {/* ── body ── */}
      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "1.5rem 2rem 3rem" }}>

        <StatsBar threats={threats} />

        {/* chart + test detection */}
        <div style={{ display: "flex", gap: 16, marginBottom: 20, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div style={{
            flex: "1 1 380px", background: "#fff", borderRadius: 10,
            padding: "1.25rem 1.5rem", boxShadow: "0 1px 4px rgba(0,0,0,.08)",
          }}>
            <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase",
                          letterSpacing: 1, fontWeight: 600, marginBottom: 12 }}>
              Threats by Type
            </div>
            <ThreatChart threats={threats} />
          </div>
          <div style={{ flex: "1 1 260px" }}>
            <TestDetection />
          </div>
        </div>

        {/* filter + table */}
        <div style={{ background: "#fff", borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,.08)", overflow: "hidden" }}>

          {/* table toolbar */}
          <div style={{
            padding: "1rem 1.5rem", borderBottom: "1px solid #f1f5f9",
            display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10,
          }}>
            <span style={{ fontWeight: 600, fontSize: 15, color: "#0f172a" }}>
              Detected Threats{" "}
              <span style={{ fontWeight: 400, color: "#94a3b8" }}>({displayed.length})</span>
            </span>
            <div style={{ display: "flex", gap: 6 }}>
              {FILTERS.map(f => (
                <button key={f} onClick={() => setFilter(f)} style={{
                  padding: "4px 14px", fontSize: 13, borderRadius: 6, cursor: "pointer", fontWeight: 500,
                  transition: "all .15s",
                  border:      "1px solid",
                  borderColor: filter === f ? "#0f172a" : "#e2e8f0",
                  background:  filter === f ? "#0f172a" : "#fff",
                  color:       filter === f ? "#fff"    : "#475569",
                }}>
                  {f}
                </button>
              ))}
            </div>
          </div>

          {displayed.length === 0 ? (
            <p style={{ padding: "2.5rem", color: "#94a3b8", textAlign: "center", margin: 0 }}>
              No threats match this filter.
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{
                    background: "#f8fafc", textAlign: "left",
                    borderBottom: "2px solid #e2e8f0",
                    fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, color: "#64748b",
                  }}>
                    {["ID", "Timestamp", "Source IP", "Type", "Payload", "Sev", "Confidence", "Status", "Actions"].map(h => (
                      <th key={h} style={{ padding: "10px 14px", fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {displayed.map(t => (
                    <tr key={t.id} style={{
                      borderBottom: "1px solid #f1f5f9",
                      borderLeft: `3px solid ${SEV_COLOR[t.severity] ?? "#cbd5e1"}`,
                    }}>
                      <td style={td}><span style={{ color: "#94a3b8", fontFamily: "monospace" }}>#{t.id}</span></td>
                      <td style={{ ...td, whiteSpace: "nowrap", color: "#475569" }}>{t.timestamp}</td>
                      <td style={{ ...td, fontFamily: "monospace", fontSize: 12 }}>{t.source_ip}</td>
                      <td style={{ ...td, fontWeight: 500 }}>{t.threat_type}</td>
                      <td style={{ ...td, maxWidth: 190, overflow: "hidden", textOverflow: "ellipsis",
                                   whiteSpace: "nowrap", fontFamily: "monospace", fontSize: 12, color: "#475569" }}>
                        {t.payload}
                      </td>
                      <td style={{ ...td, color: SEV_COLOR[t.severity], fontWeight: 700,
                                   textTransform: "uppercase", fontSize: 11 }}>
                        {t.severity}
                      </td>
                      <td style={td}><ConfidenceBar value={t.confidence} /></td>
                      <td style={td}><StatusBadge status={t.status} /></td>
                      <td style={td}><ActionButtons threat={t} onUpdate={updateThreatStatus} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

const td = { padding: "10px 14px", verticalAlign: "middle" };
