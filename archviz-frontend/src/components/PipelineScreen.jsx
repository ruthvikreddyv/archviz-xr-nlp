import { useEffect, useState } from "react";

const STEPS = [
  { id: 1, label: "Extracting text from diagram",       icon: "🔍", dur: 1800 },
  { id: 2, label: "Finding concepts and relationships", icon: "🧠", dur: 1500 },
  { id: 3, label: "Building knowledge graph",           icon: "🕸",  dur: 1200 },
  { id: 4, label: "Mapping 3D coordinates",             icon: "📐", dur: 1000 },
  { id: 5, label: "Generating explanation and quiz",    icon: "✨", dur: 2000 },
];

const s = {
  page: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    background: "linear-gradient(135deg, #0f0f1a 0%, #1a1030 100%)",
    padding: "2rem",
  },
  title: {
    fontSize: "20px",
    fontWeight: "700",
    color: "#fff",
    marginBottom: "8px",
  },
  sub: {
    fontSize: "13px",
    color: "#666",
    marginBottom: "3rem",
  },
  steps: {
    width: "100%",
    maxWidth: "420px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  step: (status) => ({
    display: "flex",
    alignItems: "center",
    gap: "14px",
    padding: "14px 18px",
    borderRadius: "12px",
    border: `1px solid ${
      status === "done"    ? "rgba(52,211,153,0.3)" :
      status === "active"  ? "rgba(167,139,250,0.4)" :
                             "rgba(255,255,255,0.06)"
    }`,
    background:
      status === "done"    ? "rgba(52,211,153,0.06)" :
      status === "active"  ? "rgba(167,139,250,0.08)" :
                             "rgba(255,255,255,0.02)",
    transition: "all 0.4s ease",
  }),
  icon: {
    fontSize: "20px",
    width: "28px",
    textAlign: "center",
    flexShrink: 0,
  },
  stepLabel: (status) => ({
    fontSize: "13px",
    fontWeight: "500",
    color:
      status === "done"   ? "#34d399" :
      status === "active" ? "#a78bfa" :
                            "#444",
    flex: 1,
  }),
  statusIcon: (status) => ({
    fontSize: "14px",
    color:
      status === "done"   ? "#34d399" :
      status === "active" ? "#a78bfa" :
                            "#333",
  }),
  spinner: {
    width: "14px",
    height: "14px",
    border: "2px solid rgba(167,139,250,0.2)",
    borderTop: "2px solid #a78bfa",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
};

export default function PipelineScreen() {
  const [activeStep, setActiveStep] = useState(1);
  const [doneSteps, setDoneSteps] = useState([]);

  useEffect(() => {
    let current = 1;
    const runStep = () => {
      if (current > STEPS.length) return;
      setActiveStep(current);
      const dur = STEPS[current - 1].dur;
      setTimeout(() => {
        setDoneSteps((prev) => [...prev, current]);
        current++;
        runStep();
      }, dur);
    };
    runStep();
  }, []);

  const getStatus = (stepId) => {
    if (doneSteps.includes(stepId)) return "done";
    if (stepId === activeStep) return "active";
    return "pending";
  };

  return (
    <div style={s.page}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <div style={s.title}>Analyzing your diagram</div>
      <div style={s.sub}>This takes about 10–15 seconds</div>

      <div style={s.steps}>
        {STEPS.map((step) => {
          const status = getStatus(step.id);
          return (
            <div key={step.id} style={s.step(status)}>
              <div style={s.icon}>{step.icon}</div>
              <div style={s.stepLabel(status)}>{step.label}</div>
              <div style={s.statusIcon(status)}>
                {status === "done"   && "✓"}
                {status === "active" && <div style={s.spinner} />}
                {status === "pending" && "○"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}