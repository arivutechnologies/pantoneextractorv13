"use client";
import { useState } from "react";
import {
  ArrowUpRight,
  Check,
  FileText,
  LockKeyhole,
  LogOut,
  Palette,
  ShieldCheck,
  TimerReset,
  UploadCloud,
} from "lucide-react";
type Result = {
  id: string;
  name: string;
  createdAt: number;
  files: { label: string; href: string; ext: string }[];
};
function dataUrlToBlobUrl(dataUrl: string) {
  const [head, body] = dataUrl.split(",");
  const mime = head.match(/data:([^;]+)/)?.[1] || "application/octet-stream";
  const bytes = Uint8Array.from(atob(body), (c) => c.charCodeAt(0));
  return URL.createObjectURL(new Blob([bytes], { type: mime }));
}
const MAX_FILE_SIZE = 4 * 1024 * 1024;
export default function Home() {
  const [ok, setOk] = useState(false),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [file, setFile] = useState<File | null>(null),
    [result, setResult] = useState<Result | null>(null),
    [busy, setBusy] = useState(false),
    [progress, setProgress] = useState(0),
    [activity, setActivity] = useState<{ message: string; time: string }[]>([]),
    [error, setError] = useState("");
  const log = (message: string) =>
    setActivity((current) => [
      ...current,
      {
        message,
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      },
    ]);
  async function login(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const r = await fetch("/api/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (r.ok) setOk(true);
    else setError("Invalid credentials.");
  }
  async function upload() {
    if (!file) return;
    if (file.size > MAX_FILE_SIZE) {
      setError("This PDF is larger than 4 MB. Please choose a smaller file for Vercel Hobby.");
      return;
    }
    setBusy(true);
    setError("");
    setProgress(8);
    setActivity([]);
    log(
      `Upload received · ${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`,
    );
    const stages = [
      [22, "Reading PDF structure"],
      [44, "Extracting document colors"],
      [68, "Calculating Pantone matches"],
      [86, "Rendering PNG, PDF, and CSV reports"],
    ] as const;
    let stage = 0;
    const timer = setInterval(() => {
      if (stage >= stages.length) return;
      const [value, message] = stages[stage++];
      setProgress(value);
      log(message);
    }, 2500);
    const fd = new FormData();
    fd.append("file", file);
    const endpoint =
      process.env.NODE_ENV === "development" ? "/api/process" : "/api/extract";
    log(`Calling ${endpoint}`);
    const startedAt = Date.now();
    const r = await fetch(endpoint, { method: "POST", body: fd }),
      d = await r.json();
    clearInterval(timer);
    setBusy(false);
    if (!r.ok) {
      log(`Failed after ${((Date.now() - startedAt) / 1000).toFixed(1)}s`);
      setError(d.detail || d.error || "Processing failed.");
      return;
    }
    if (endpoint === "/api/extract")
      d.files = d.files.map(
        (f: { label: string; href: string; ext: string }) => ({
          ...f,
          href: dataUrlToBlobUrl(f.href),
        }),
      );
    setProgress(100);
    log(`Complete · ${((Date.now() - startedAt) / 1000).toFixed(1)}s elapsed`);
    setResult(d);
    setTimeout(() => setResult(null), 1800000);
  }
  if (!ok)
    return (
      <main
        className="app-shell noise"
        style={{ display: "grid", placeItems: "center", padding: 24 }}
      >
        <section style={{ width: "100%", maxWidth: 440 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 72,
            }}
          >
            <div>
              <span
                className="orange"
                style={{ fontWeight: 800, letterSpacing: 3, fontSize: 12 }}
              >
                PANTONE EXTRACTOR
              </span>
              <div style={{ fontSize: 12, color: "#827b71", marginTop: 8 }}>
                Private color intelligence workspace
              </div>
            </div>
            <LockKeyhole size={20} color="#ff6b2c" />
          </div>
          <div className="paper" style={{ padding: 36 }}>
            <div
              style={{
                fontSize: 12,
                letterSpacing: 2,
                fontWeight: 700,
                marginBottom: 16,
              }}
            >
              WELCOME BACK
            </div>
            <h1
              style={{
                fontSize: 42,
                lineHeight: 1,
                letterSpacing: -2,
                margin: "0 0 14px",
              }}
            >
              Match with
              <br />
              <span className="orange">precision.</span>
            </h1>
            <p style={{ color: "#665f56", lineHeight: 1.6, marginBottom: 32 }}>
              Sign in to extract source colors from PDFs and compare them across
              three Pantone libraries.
            </p>
            <form onSubmit={login} style={{ display: "grid", gap: 14 }}>
              <label style={{ fontSize: 12, fontWeight: 700 }}>
                EMAIL
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  type="email"
                  placeholder="you@studio.com"
                  style={{
                    display: "block",
                    width: "100%",
                    padding: 14,
                    marginTop: 7,
                    border: "1px solid #d5cfc3",
                    background: "#fbf8f1",
                  }}
                />
              </label>
              <label style={{ fontSize: 12, fontWeight: 700 }}>
                PASSWORD
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  type="password"
                  placeholder="••••••••"
                  style={{
                    display: "block",
                    width: "100%",
                    padding: 14,
                    marginTop: 7,
                    border: "1px solid #d5cfc3",
                    background: "#fbf8f1",
                  }}
                />
              </label>
              {error && (
                <div style={{ color: "#b83d20", fontSize: 13 }}>{error}</div>
              )}
              <button
                className="btn"
                style={{
                  background: "#11100f",
                  color: "#fff",
                  padding: 16,
                  textAlign: "left",
                  fontWeight: 700,
                  marginTop: 8,
                }}
              >
                Enter workspace{" "}
                <ArrowUpRight size={18} style={{ float: "right" }} />
              </button>
            </form>
          </div>
          <div
            style={{
              display: "flex",
              gap: 18,
              alignItems: "center",
              marginTop: 20,
              color: "#827b71",
              fontSize: 12,
            }}
          >
            <ShieldCheck size={15} color="#ff6b2c" /> Encrypted session · Files
            auto-delete after 30 min
          </div>
        </section>
      </main>
    );
  return (
    <main className="app-shell">
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "28px 5vw",
          borderBottom: "1px solid #2c2a27",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Palette className="orange" size={23} />
          <span style={{ fontWeight: 800, letterSpacing: 2, fontSize: 13 }}>
            PANTONE EXTRACTOR
          </span>
        </div>
        <button
          className="btn"
          onClick={() => setOk(false)}
          style={{
            background: "transparent",
            color: "#a59e93",
            display: "flex",
            gap: 8,
            alignItems: "center",
            fontSize: 13,
          }}
        >
          <LogOut size={16} /> Sign out
        </button>
      </header>
      <div style={{ maxWidth: 1120, margin: "0 auto", padding: "72px 5vw" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 30,
            alignItems: "end",
            marginBottom: 60,
          }}
        >
          <div>
            <div
              className="orange"
              style={{
                fontSize: 12,
                fontWeight: 800,
                letterSpacing: 3,
                marginBottom: 18,
              }}
            >
              COLOR EXTRACTION / 01
            </div>
            <h1
              style={{
                fontSize: "clamp(42px,7vw,86px)",
                lineHeight: 0.92,
                letterSpacing: -5,
                margin: 0,
              }}
            >
              Turn PDFs
              <br />
              <span style={{ color: "#8b857b" }}>into color.</span>
            </h1>
          </div>
          <p
            style={{
              maxWidth: 260,
              color: "#a59e93",
              lineHeight: 1.6,
              fontSize: 14,
            }}
          >
            Upload one PDF. We’ll surface the colors that matter, then find
            their closest Pantone references.
          </p>
        </div>
        <section
          className="paper"
          style={{
            padding: "clamp(24px,5vw,56px)",
            minHeight: 310,
            display: "grid",
            placeItems: "center",
            textAlign: "center",
          }}
        >
          {!file && !busy && !result && (
            <label style={{ cursor: "pointer", width: "100%" }}>
              <UploadCloud size={38} className="orange" />
              <h2
                style={{
                  fontSize: 28,
                  letterSpacing: -1,
                  margin: "18px 0 8px",
                }}
              >
                Drop your PDF here
              </h2>
              <p style={{ color: "#777066", margin: 0 }}>
                or click to browse · PDF only · up to 4 MB
              </p>
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => {
                  const selected = e.target.files?.[0] || null;
                  if (selected && selected.size > MAX_FILE_SIZE) {
                    setFile(null);
                    setError("This PDF is larger than 4 MB. Please choose a smaller file for Vercel Hobby.");
                    return;
                  }
                  setError("");
                  setFile(selected);
                }}
                style={{ display: "none" }}
              />
            </label>
          )}
          {file && !busy && !result && (
            <div>
              <FileText size={38} className="orange" />
              <h2 style={{ margin: "18px 0 6px" }}>{file.name}</h2>
              <p style={{ color: "#777066" }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB · Ready to process
              </p>
              <button
                className="btn"
                onClick={upload}
                style={{
                  background: "#ff6b2c",
                  color: "#11100f",
                  padding: "14px 24px",
                  fontWeight: 800,
                }}
              >
                Extract Pantone matches{" "}
                <ArrowUpRight
                  size={17}
                  style={{ verticalAlign: "middle", marginLeft: 8 }}
                />
              </button>
            </div>
          )}
          {busy && (
            <div style={{ width: "100%", maxWidth: 620, textAlign: "left" }}>
              <TimerReset size={38} className="orange" />
              <h2 style={{ margin: "18px 0 8px", textAlign: "center" }}>
                Processing your document…
              </h2>
              <p style={{ color: "#777066", textAlign: "center" }}>
                Vercel may take a little longer on the first request while the
                processing function starts.
              </p>
              <div
                style={{
                  height: 8,
                  background: "#d5cfc3",
                  margin: "26px 0 20px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${progress}%`,
                    background: "#ff6b2c",
                    transition: "width .5s ease",
                  }}
                />
              </div>
              <div
                style={{
                  display: "grid",
                  gap: 9,
                  color: "#665f56",
                  fontSize: 13,
                }}
              >
                {activity.map((item, index) => (
                  <div
                    key={`${item.time}-${index}`}
                    style={{ display: "flex", gap: 8, alignItems: "center" }}
                  >
                    <Check size={14} color="#ff6b2c" />
                    <span style={{ flex: 1 }}>{item.message}</span>
                    <time style={{ color: "#9a9287", fontSize: 11 }}>
                      {item.time}
                    </time>
                  </div>
                ))}
              </div>
              <button
                className="btn"
                onClick={() =>
                  navigator.clipboard?.writeText(
                    activity
                      .map((item) => `${item.time}  ${item.message}`)
                      .join("\n"),
                  )
                }
                style={{
                  background: "transparent",
                  border: "1px solid #d5cfc3",
                  padding: "9px 12px",
                  marginTop: 22,
                  fontSize: 12,
                }}
              >
                Copy activity log
              </button>
            </div>
          )}
          {result && (
            <div style={{ width: "100%" }}>
              <Check size={38} className="orange" />
              <h2 style={{ margin: "18px 0 8px" }}>Your files are ready.</h2>
              <p style={{ color: "#777066" }}>
                Download each format separately. Links expire in 30 minutes.
              </p>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(3,1fr)",
                  gap: 10,
                  marginTop: 24,
                }}
              >
                {result.files.map((f) => (
                  <a
                    key={f.ext}
                    href={f.href}
                    download={`pantone-report.${f.ext}`}
                    className="btn"
                    style={{
                      background: "#11100f",
                      color: "#fff",
                      padding: 16,
                      textDecoration: "none",
                      fontWeight: 700,
                      fontSize: 13,
                    }}
                  >
                    {f.label}
                    <ArrowUpRight size={15} style={{ float: "right" }} />
                  </a>
                ))}
              </div>
              <button
                className="btn"
                onClick={() => {
                  setFile(null);
                  setResult(null);
                }}
                style={{
                  background: "transparent",
                  marginTop: 22,
                  textDecoration: "underline",
                }}
              >
                Process another PDF
              </button>
            </div>
          )}
        </section>
        {error && <p style={{ color: "#ff8b67", marginTop: 18 }}>{error}</p>}
        <div
          style={{
            display: "flex",
            gap: 28,
            marginTop: 24,
            color: "#8f887e",
            fontSize: 12,
          }}
        >
          <span>
            <ShieldCheck size={14} /> Private by default
          </span>
          <span>
            <TimerReset size={14} /> Auto-delete in 30 minutes
          </span>
        </div>
      </div>
    </main>
  );
}
