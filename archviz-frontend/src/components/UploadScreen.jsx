import { useRef, useState } from "react";

const s = {
  page: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "2rem",
    background: "linear-gradient(135deg, #0f0f1a 0%, #1a1030 100%)",
  },
  logo: {
    fontSize: "13px",
    letterSpacing: "3px",
    color: "#7F77DD",
    textTransform: "uppercase",
    marginBottom: "10px",
  },
  title: {
    fontSize: "36px",
    fontWeight: "800",
    background: "linear-gradient(90deg, #a78bfa, #34d399)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    marginBottom: "8px",
    textAlign: "center",
  },
  subtitle: {
    fontSize: "14px",
    color: "#888",
    marginBottom: "3rem",
    textAlign: "center",
    maxWidth: "420px",
    lineHeight: "1.6",
  },
  dropzone: (dragging) => ({
    width: "100%",
    maxWidth: "480px",
    border: `2px dashed ${dragging ? "#a78bfa" : "#333"}`,
    borderRadius: "16px",
    padding: "3rem 2rem",
    textAlign: "center",
    cursor: "pointer",
    transition: "all 0.2s",
    background: dragging ? "rgba(167,139,250,0.05)" : "rgba(255,255,255,0.02)",
    marginBottom: "1rem",
  }),
  dropIcon: {
    fontSize: "40px",
    marginBottom: "12px",
  },
  dropText: {
    fontSize: "15px",
    color: "#ccc",
    marginBottom: "6px",
  },
  dropSub: {
    fontSize: "12px",
    color: "#555",
  },
  orDivider: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    width: "100%",
    maxWidth: "480px",
    margin: "1rem 0",
    color: "#444",
    fontSize: "12px",
  },
  orLine: {
    flex: 1,
    height: "1px",
    background: "#222",
  },
  demoBtn: {
    width: "100%",
    maxWidth: "480px",
    padding: "14px",
    borderRadius: "12px",
    border: "none",
    background: "linear-gradient(135deg, #7c3aed, #1D9E75)",
    color: "#fff",
    fontSize: "15px",
    fontWeight: "700",
    cursor: "pointer",
    letterSpacing: "0.5px",
    transition: "opacity 0.15s",
  },
  demoSub: {
    fontSize: "11px",
    color: "#666",
    marginTop: "8px",
    textAlign: "center",
  },
  error: {
    marginTop: "1rem",
    padding: "10px 16px",
    background: "rgba(239,68,68,0.1)",
    border: "1px solid rgba(239,68,68,0.3)",
    borderRadius: "8px",
    color: "#fca5a5",
    fontSize: "13px",
    maxWidth: "480px",
    textAlign: "center",
  },
};

export default function UploadScreen({ onUpload, onDemo, error }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleFile = (file) => {
    if (!file) return;
    const allowed = ["image/jpeg", "image/png", "image/jpg", "application/pdf"];
    if (!allowed.includes(file.type)) {
      alert("Please upload a JPG, PNG, or PDF file.");
      return;
    }
    onUpload(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div style={s.page}>
      <div style={s.logo}>ArchViz-XR</div>
      <div style={s.title}>See Research in 3D</div>
      <div style={s.subtitle}>
        Upload any academic diagram — transformer architectures, neural networks,
        blockchain flows — and watch it become an interactive AR experience.
      </div>

      {/* Drop zone */}
      <div
        style={s.dropzone(dragging)}
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <div style={s.dropIcon}>📄</div>
        <div style={s.dropText}>Drop your diagram here</div>
        <div style={s.dropSub}>or click to browse · JPG, PNG, PDF</div>
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      {/* OR divider */}
      <div style={s.orDivider}>
        <div style={s.orLine} />
        or
        <div style={s.orLine} />
      </div>

      {/* Demo button — most important */}
      <button style={s.demoBtn} onClick={onDemo}>
        ▶ &nbsp; Load Transformer Demo
      </button>
      <div style={s.demoSub}>
        Pre-loaded · instant · no processing needed
      </div>

      {error && <div style={s.error}>⚠ {error}</div>}
    </div>
  );
}