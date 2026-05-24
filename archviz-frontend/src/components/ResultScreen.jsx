import { useState } from "react";

const s = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #0f0f1a 0%, #1a1030 100%)",
    padding: "2rem",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  header: {
    width: "100%",
    maxWidth: "640px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "2rem",
  },
  logo: {
    fontSize: "13px",
    letterSpacing: "3px",
    color: "#7F77DD",
    textTransform: "uppercase",
  },
  resetBtn: {
    fontSize: "12px",
    background: "none",
    border: "1px solid #222",
    padding: "6px 14px",
    borderRadius: "20px",
    cursor: "pointer",
    color: "#888",
  },
  stats: {
    display: "flex",
    gap: "10px",
    marginBottom: "1.5rem",
    width: "100%",
    maxWidth: "640px",
  },
  stat: (color) => ({
    flex: 1,
    background: "rgba(255,255,255,0.03)",
    border: `1px solid ${color}33`,
    borderRadius: "10px",
    padding: "12px",
    textAlign: "center",
  }),
  statNum: (color) => ({
    fontSize: "24px",
    fontWeight: "800",
    color: color,
  }),
  statLabel: {
    fontSize: "11px",
    color: "#555",
    marginTop: "2px",
  },
  card: {
    width: "100%",
    maxWidth: "640px",
    background: "rgba(255,255,255,0.03)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: "14px",
    padding: "1.4rem",
    marginBottom: "12px",
  },
  cardTitle: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#555",
    textTransform: "uppercase",
    letterSpacing: "1px",
    marginBottom: "10px",
  },
  explanation: {
    fontSize: "14px",
    color: "#ccc",
    lineHeight: "1.8",
  },
  quizQ: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#fff",
    marginBottom: "10px",
    lineHeight: "1.5",
  },
  option: (selected, correct, revealed) => ({
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px 14px",
    borderRadius: "8px",
    marginBottom: "6px",
    cursor: revealed ? "default" : "pointer",
    border: `1px solid ${
      !revealed ? "rgba(255,255,255,0.08)" :
      correct   ? "rgba(52,211,153,0.4)"   :
      selected  ? "rgba(239,68,68,0.4)"    :
                  "rgba(255,255,255,0.05)"
    }`,
    background:
      !revealed ? "rgba(255,255,255,0.02)" :
      correct   ? "rgba(52,211,153,0.08)"  :
      selected  ? "rgba(239,68,68,0.08)"   :
                  "rgba(255,255,255,0.01)",
    transition: "all 0.2s",
  }),
  optionText: (selected, correct, revealed) => ({
    fontSize: "13px",
    color:
      !revealed ? "#aaa"    :
      correct   ? "#34d399" :
      selected  ? "#f87171" :
                  "#444",
  }),
  navBtns: {
    display: "flex",
    justifyContent: "space-between",
    marginTop: "12px",
  },
  navBtn: (disabled) => ({
    fontSize: "12px",
    padding: "7px 16px",
    borderRadius: "8px",
    border: "1px solid #222",
    background: "none",
    color: disabled ? "#333" : "#888",
    cursor: disabled ? "default" : "pointer",
  }),
  arBtn: {
    width: "100%",
    maxWidth: "640px",
    padding: "16px",
    borderRadius: "12px",
    border: "none",
    background: "linear-gradient(135deg, #7c3aed, #1D9E75)",
    color: "#fff",
    fontSize: "15px",
    fontWeight: "700",
    cursor: "pointer",
    marginBottom: "12px",
    letterSpacing: "0.5px",
  },
  nodeList: {
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
  },
  nodeTag: (type) => ({
    fontSize: "11px",
    padding: "3px 10px",
    borderRadius: "20px",
    background:
      type === "component" ? "rgba(124,58,237,0.15)" :
      type === "process"   ? "rgba(245,158,11,0.15)" :
                             "rgba(107,114,128,0.15)",
    color:
      type === "component" ? "#a78bfa" :
      type === "process"   ? "#fbbf24" :
                             "#9ca3af",
    border: `1px solid ${
      type === "component" ? "rgba(124,58,237,0.3)" :
      type === "process"   ? "rgba(245,158,11,0.3)" :
                             "rgba(107,114,128,0.3)"
    }`,
  }),
};

// ── QuizCard ──────────────────────────────────────────────
function QuizCard({ quiz }) {
  const [current,     setCurrent]     = useState(0);
  const [selected,    setSelected]    = useState(null);
  const [revealed,    setRevealed]    = useState(false);
  const [score,       setScore]       = useState(0);
  const [done,        setDone]        = useState(false);
  const [userAnswers, setUserAnswers] = useState(Array(quiz.length).fill(null));

  const q = quiz[current];

  const handleSelect = (idx) => {
    if (revealed) return;
    setSelected(idx);
    setRevealed(true);
    // Track which answer the user chose for each question
    setUserAnswers((prev) => {
      const updated = [...prev];
      updated[current] = idx;
      return updated;
    });
    if (idx === q.answer) setScore((s) => s + 1);
  };

  const handleNext = () => {
    if (current < quiz.length - 1) {
      setCurrent((c) => c + 1);
      setSelected(null);
      setRevealed(false);
    } else {
      setDone(true);
    }
  };

  // ── Results screen with concept feedback ─────────────────
  if (done) {
    const wrongQuestions  = quiz.filter((q, i) => userAnswers[i] !== q.answer);
    const strongQuestions = quiz.filter((q, i) => userAnswers[i] === q.answer);

    return (
      <div style={{ padding: "0.5rem 0" }}>

        {/* Score header */}
        <div style={{ textAlign: "center", marginBottom: "1.2rem" }}>
          <div style={{ fontSize: "36px", marginBottom: "8px" }}>
            {score === quiz.length ? "🎉" : score >= quiz.length / 2 ? "👍" : "📚"}
          </div>
          <div style={{ fontSize: "28px", fontWeight: "800", color: "#34d399" }}>
            {score} / {quiz.length}
          </div>
          <div style={{ fontSize: "13px", color: "#666", marginTop: "4px" }}>
            {score === quiz.length
              ? "Perfect score! You understand this diagram fully."
              : score >= quiz.length / 2
              ? "Good understanding — review the highlighted concepts."
              : "Keep exploring the AR view to strengthen your understanding."}
          </div>
        </div>

        {/* Strong concepts */}
        {strongQuestions.length > 0 && (
          <div style={{ marginBottom: "12px" }}>
            <div style={{
              fontSize: "11px", fontWeight: "700", color: "#34d399",
              textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px"
            }}>
              ✓ Strong concepts
            </div>
            {strongQuestions.map((q, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "flex-start", gap: "10px",
                padding: "8px 12px", marginBottom: "6px", borderRadius: "8px",
                background: "rgba(52,211,153,0.06)",
                border: "1px solid rgba(52,211,153,0.2)"
              }}>
                <span style={{ color: "#34d399", fontSize: "13px", flexShrink: 0 }}>✓</span>
                <span style={{ fontSize: "12px", color: "#9ca3af", lineHeight: "1.5" }}>
                  {q.q}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Weak concepts — needs review */}
        {wrongQuestions.length > 0 && (
          <div>
            <div style={{
              fontSize: "11px", fontWeight: "700", color: "#f87171",
              textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px"
            }}>
              ⚠ Review these concepts
            </div>
            {wrongQuestions.map((q, i) => (
              <div key={i} style={{
                padding: "10px 12px", marginBottom: "8px", borderRadius: "8px",
                background: "rgba(239,68,68,0.06)",
                border: "1px solid rgba(239,68,68,0.2)"
              }}>
                <div style={{
                  display: "flex", alignItems: "flex-start",
                  gap: "10px", marginBottom: "6px"
                }}>
                  <span style={{ color: "#f87171", fontSize: "13px", flexShrink: 0 }}>✗</span>
                  <span style={{ fontSize: "12px", color: "#9ca3af", lineHeight: "1.5" }}>
                    {q.q}
                  </span>
                </div>
                <div style={{
                  marginLeft: "22px", padding: "6px 10px",
                  background: "rgba(52,211,153,0.08)",
                  borderRadius: "6px",
                  borderLeft: "2px solid #34d399"
                }}>
                  <span style={{ fontSize: "11px", color: "#34d399", fontWeight: "600" }}>
                    Correct answer:&nbsp;
                  </span>
                  <span style={{ fontSize: "11px", color: "#ccc" }}>
                    {q.options[q.answer]}
                  </span>
                </div>
              </div>
            ))}

            {/* Tip to go back to AR */}
            <div style={{
              marginTop: "10px", padding: "10px 12px",
              background: "rgba(167,139,250,0.08)",
              border: "1px solid rgba(167,139,250,0.2)",
              borderRadius: "8px",
              fontSize: "12px", color: "#a78bfa", lineHeight: "1.6"
            }}>
              💡 Open the AR viewer and explore these nodes — use voice Q&amp;A
              to ask about the concepts you missed.
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Active quiz question ──────────────────────────────────
  return (
    <div>
      <div style={{ fontSize: "11px", color: "#555", marginBottom: "10px" }}>
        Question {current + 1} of {quiz.length}
      </div>
      <div style={s.quizQ}>{q.q}</div>
      {q.options.map((opt, idx) => (
        <div
          key={idx}
          style={s.option(idx === selected, idx === q.answer, revealed)}
          onClick={() => handleSelect(idx)}
        >
          <span style={{ fontSize: "11px", color: "#444", width: "16px" }}>
            {String.fromCharCode(65 + idx)}
          </span>
          <span style={s.optionText(idx === selected, idx === q.answer, revealed)}>
            {opt}
          </span>
          {revealed && idx === q.answer && (
            <span style={{ marginLeft: "auto", color: "#34d399" }}>✓</span>
          )}
        </div>
      ))}
      {revealed && (
        <div style={s.navBtns}>
          <div />
          <button style={s.navBtn(false)} onClick={handleNext}>
            {current < quiz.length - 1 ? "Next →" : "See results"}
          </button>
        </div>
      )}
    </div>
  );
}

// ── ResultScreen ──────────────────────────────────────────
export default function ResultScreen({ contract, onReset }) {
  if (!contract) return null;

  const nodes = contract.nodes ?? [];
  const edges = contract.edges ?? [];
  const quiz = contract.quiz ?? [];
  const components = nodes.filter((n) => n.type === "component");
  const processes  = nodes.filter((n) => n.type === "process");
  const data       = nodes.filter((n) => n.type === "data");

  const openArViewer = () => {
    window.open("http://localhost:8000/ar/index.html", "_blank", "noopener,noreferrer");
  };

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div style={s.logo}>ArchViz-XR</div>
        <button style={s.resetBtn} onClick={onReset}>← New diagram</button>
      </div>

      {/* Stats */}
      <div style={s.stats}>
        <div style={s.stat("#a78bfa")}>
          <div style={s.statNum("#a78bfa")}>{nodes.length}</div>
          <div style={s.statLabel}>Nodes</div>
        </div>
        <div style={s.stat("#34d399")}>
          <div style={s.statNum("#34d399")}>{edges.length}</div>
          <div style={s.statLabel}>Edges</div>
        </div>
        <div style={s.stat("#fbbf24")}>
          <div style={s.statNum("#fbbf24")}>{quiz.length}</div>
          <div style={s.statLabel}>Quiz Qs</div>
        </div>
      </div>

      {/* Open in AR button */}
      <button style={s.arBtn} onClick={openArViewer}>
        🥽 &nbsp; Open in AR Viewer
      </button>

      {/* Explanation */}
      <div style={s.card}>
        <div style={s.cardTitle}>What this diagram shows</div>
        <div style={s.explanation}>{contract.explanation || "No explanation was generated."}</div>
      </div>

      {/* Nodes */}
      <div style={s.card}>
        <div style={s.cardTitle}>
          Concepts extracted — {nodes.length} nodes
        </div>
        <div style={{ marginBottom: "10px" }}>
          <div style={{ fontSize: "11px", color: "#555", marginBottom: "5px" }}>
            Components
          </div>
          <div style={s.nodeList}>
            {components.map((n) => (
              <span key={n.id} style={s.nodeTag("component")}>{n.label}</span>
            ))}
          </div>
        </div>
        <div style={{ marginBottom: "10px" }}>
          <div style={{ fontSize: "11px", color: "#555", marginBottom: "5px" }}>
            Processes
          </div>
          <div style={s.nodeList}>
            {processes.map((n) => (
              <span key={n.id} style={s.nodeTag("process")}>{n.label}</span>
            ))}
          </div>
        </div>
        <div>
          <div style={{ fontSize: "11px", color: "#555", marginBottom: "5px" }}>
            Data
          </div>
          <div style={s.nodeList}>
            {data.map((n) => (
              <span key={n.id} style={s.nodeTag("data")}>{n.label}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Quiz */}
      <div style={s.card}>
        <div style={s.cardTitle}>Test your understanding</div>
        {quiz.length > 0 ? (
          <QuizCard quiz={quiz} />
        ) : (
          <div style={s.explanation}>No quiz questions were generated.</div>
        )}
      </div>
    </div>
  );
}
