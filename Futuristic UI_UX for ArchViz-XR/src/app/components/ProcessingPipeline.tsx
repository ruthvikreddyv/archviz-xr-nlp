import { useState, useEffect } from "react";
import { CheckCircle, Circle, Loader2, X } from "lucide-react";
import { Link } from "react-router";
import { motion } from "motion/react";
import { loadStoredContract } from "../lib/api";

const steps = [
  { id: 1, name: "OCR Extraction", description: "Extracting text and structure from diagram" },
  { id: 2, name: "Concept Detection", description: "Identifying key concepts and entities" },
  { id: 3, name: "Relationship Mapping", description: "Discovering connections between concepts" },
  { id: 4, name: "LLM Explanation", description: "Generating natural language explanations" },
  { id: 5, name: "Knowledge Graph Generation", description: "Building interactive graph structure" },
  { id: 6, name: "AR/XR Preparation", description: "Optimizing for immersive visualization" },
];

export function ProcessingPipeline() {
  const [currentStep, setCurrentStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const hasContract = Boolean(loadStoredContract());

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (currentStep < steps.length) {
        setLogs((prev) => [...prev, `[ok] ${steps[currentStep].name} completed`]);
        setCurrentStep((prev) => prev + 1);
      }
    }, hasContract ? 450 : 2000);

    return () => window.clearInterval(interval);
  }, [currentStep, hasContract]);

  const isComplete = currentStep >= steps.length;

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-24">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold mb-2">
              {isComplete ? (
                <>
                  Processing{" "}
                  <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
                    Complete
                  </span>
                </>
              ) : (
                <>
                  Processing Your{" "}
                  <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
                    Diagram
                  </span>
                </>
              )}
            </h1>
            <p className="text-muted-foreground">
              {hasContract
                ? "Backend graph contract received. Preparing UI and AR views."
                : "Waiting for a generated graph contract from the backend."}
            </p>
          </div>

          <div className="glass-panel rounded-xl p-8 mb-6">
            <div className="space-y-6">
              {steps.map((step, index) => {
                const isActive = index === currentStep;
                const isDone = index < currentStep;

                return (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className={`flex items-start gap-4 p-4 rounded-lg transition-all ${
                      isActive ? "bg-primary/10 border border-primary/30" : ""
                    }`}
                  >
                    <div className="shrink-0">
                      {isDone ? (
                        <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                          <CheckCircle className="w-6 h-6 text-space-dark" />
                        </div>
                      ) : isActive ? (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                          <Loader2 className="w-6 h-6 text-space-dark animate-spin" />
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-full border-2 border-primary/30 flex items-center justify-center">
                          <Circle className="w-6 h-6 text-muted-foreground" />
                        </div>
                      )}
                    </div>

                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">{step.name}</h3>
                      <p className="text-sm text-muted-foreground">{step.description}</p>

                      {isActive && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          className="mt-3"
                        >
                          <div className="w-full bg-muted rounded-full h-1.5">
                            <motion.div
                              initial={{ width: "0%" }}
                              animate={{ width: "100%" }}
                              transition={{ duration: hasContract ? 0.45 : 2, ease: "linear" }}
                              className="h-1.5 rounded-full bg-gradient-to-r from-primary to-secondary"
                            />
                          </div>
                        </motion.div>
                      )}
                    </div>

                    <div className="text-sm font-medium">
                      {isDone ? (
                        <span className="text-primary">Done</span>
                      ) : isActive ? (
                        <span className="text-secondary">Processing...</span>
                      ) : (
                        <span className="text-muted-foreground">Pending</span>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          <div className="glass-panel rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Processing Logs</h3>
              <button
                onClick={() => setLogs([])}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            </div>
            <div className="bg-space-darker rounded-lg p-4 font-mono text-sm max-h-64 overflow-y-auto">
              {logs.map((log, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-primary mb-1"
                >
                  {log}
                </motion.div>
              ))}
              {!isComplete && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{hasContract ? "Preparing result screen..." : "Run upload or demo first..."}</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Link
              to="/upload"
              className="px-6 py-3 rounded-lg border border-primary/30 hover:border-primary/60 transition-all flex items-center gap-2"
            >
              <X className="w-5 h-5" />
              Back
            </Link>

            {isComplete && (
              <Link
                to="/results"
                className="px-6 py-3 rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium hover:shadow-lg hover:shadow-primary/50 transition-all"
              >
                View Results -&gt;
              </Link>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
