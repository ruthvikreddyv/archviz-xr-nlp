import { useEffect, useMemo, useState } from "react";
import {
  Box,
  Glasses,
  Download,
  MessageSquare,
  Network,
  Brain,
  ArrowRight,
  CheckCircle,
} from "lucide-react";
import { Link } from "react-router";
import { motion } from "motion/react";
import {
  fetchLatestContract,
  getArViewerUrl,
  loadStoredContract,
  type GraphContract,
} from "../lib/api";

export function ResultsScreen() {
  const [contract, setContract] = useState<GraphContract | null>(() => loadStoredContract());
  const [error, setError] = useState("");

  useEffect(() => {
    if (contract) return;
    fetchLatestContract()
      .then(setContract)
      .catch((err) => setError(err instanceof Error ? err.message : "No contract found"));
  }, [contract]);

  const degreeByNode = useMemo(() => {
    const degree: Record<string, number> = {};
    contract?.nodes.forEach((node) => {
      degree[node.id] = 0;
    });
    contract?.edges.forEach((edge) => {
      if (degree[edge.from] !== undefined) degree[edge.from] += 1;
      if (degree[edge.to] !== undefined) degree[edge.to] += 1;
    });
    return degree;
  }, [contract]);

  const concepts = contract?.nodes || [];
  const relationships = contract?.edges || [];
  const quizCards = contract?.quiz || [];

  const exportJson = () => {
    if (!contract) return;
    const blob = new Blob([JSON.stringify(contract, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "archviz-contract.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!contract && error) {
    return (
      <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-24">
        <div className="max-w-3xl mx-auto glass-panel rounded-xl p-8">
          <h1 className="text-3xl font-bold mb-3">No Graph Yet</h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Link
            to="/upload"
            className="inline-flex px-6 py-3 rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium"
          >
            Upload a Diagram
          </Link>
        </div>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-24">
        <div className="max-w-3xl mx-auto glass-panel rounded-xl p-8 text-muted-foreground">
          Loading latest graph contract...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-24">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">
              Processing{" "}
              <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
                Results
              </span>
            </h1>
            <p className="text-muted-foreground">
              Real backend output from the ArchViz-XR NLP pipeline.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="glass-panel rounded-xl p-6">
              <Network className="w-8 h-8 text-primary mb-2" />
              <div className="text-2xl font-bold">{concepts.length}</div>
              <div className="text-sm text-muted-foreground">Concepts</div>
            </div>
            <div className="glass-panel rounded-xl p-6">
              <ArrowRight className="w-8 h-8 text-secondary mb-2" />
              <div className="text-2xl font-bold">{relationships.length}</div>
              <div className="text-sm text-muted-foreground">Relationships</div>
            </div>
            <div className="glass-panel rounded-xl p-6">
              <Brain className="w-8 h-8 text-neon-pink mb-2" />
              <div className="text-2xl font-bold">{new Set(concepts.map((n) => n.type)).size}</div>
              <div className="text-sm text-muted-foreground">Node Types</div>
            </div>
            <div className="glass-panel rounded-xl p-6">
              <CheckCircle className="w-8 h-8 text-neon-orange mb-2" />
              <div className="text-2xl font-bold">{quizCards.length}</div>
              <div className="text-sm text-muted-foreground">Quiz Items</div>
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2 space-y-6">
              <div className="glass-panel rounded-xl p-6">
                <h2 className="text-xl font-semibold mb-4">Generated Explanation</h2>
                <p className="text-muted-foreground leading-relaxed">
                  {contract.explanation || "The pipeline generated a graph but no explanation was returned."}
                </p>
              </div>

              <div className="glass-panel rounded-xl p-6">
                <h2 className="text-xl font-semibold mb-4">Extracted Concepts</h2>
                <div className="grid sm:grid-cols-2 gap-3">
                  {concepts.slice(0, 18).map((concept) => (
                    <div
                      key={concept.id}
                      className="p-4 rounded-lg border border-primary/20 hover:border-primary/40 transition-all"
                    >
                      <h3 className="font-semibold mb-1">{concept.label}</h3>
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>{concept.type.replace("_", " ")}</span>
                        <span>{degreeByNode[concept.id] || 0} links</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-panel rounded-xl p-6">
                <h2 className="text-xl font-semibold mb-4">Relationship Map</h2>
                <div className="space-y-2 max-h-96 overflow-auto pr-2">
                  {relationships.slice(0, 32).map((rel, index) => {
                    const from = concepts.find((node) => node.id === rel.from)?.label || rel.from;
                    const to = concepts.find((node) => node.id === rel.to)?.label || rel.to;
                    return (
                      <div
                        key={`${rel.from}-${rel.to}-${index}`}
                        className="flex items-center gap-3 p-3 rounded-lg bg-space-darker"
                      >
                        <span className="font-medium text-primary truncate">{from}</span>
                        <ArrowRight className="w-4 h-4 text-muted-foreground shrink-0" />
                        <span className="text-sm px-2 py-1 rounded bg-secondary/20 text-secondary whitespace-nowrap">
                          {rel.label}
                        </span>
                        <ArrowRight className="w-4 h-4 text-muted-foreground shrink-0" />
                        <span className="font-medium text-neon-pink truncate">{to}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="glass-panel rounded-xl p-6">
                <h3 className="font-semibold mb-4">Explore Graph</h3>
                <div className="space-y-3">
                  <Link
                    to="/graph-viewer"
                    className="w-full px-4 py-3 rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium hover:shadow-lg hover:shadow-primary/50 transition-all flex items-center justify-center gap-2"
                  >
                    <Box className="w-5 h-5" />
                    Open UI Graph
                  </Link>
                  <a
                    href={getArViewerUrl()}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full px-4 py-3 rounded-lg border border-primary/30 hover:border-primary/60 hover:bg-primary/10 transition-all flex items-center justify-center gap-2"
                  >
                    <Glasses className="w-5 h-5" />
                    Launch AR Viewer
                  </a>
                  <Link
                    to="/graph-viewer"
                    className="w-full px-4 py-3 rounded-lg border border-primary/30 hover:border-primary/60 hover:bg-primary/10 transition-all flex items-center justify-center gap-2"
                  >
                    <MessageSquare className="w-5 h-5" />
                    Ask Question
                  </Link>
                  <button
                    onClick={exportJson}
                    className="w-full px-4 py-3 rounded-lg border border-primary/30 hover:border-primary/60 hover:bg-primary/10 transition-all flex items-center justify-center gap-2"
                  >
                    <Download className="w-5 h-5" />
                    Export JSON
                  </button>
                </div>
              </div>

              <div className="glass-panel rounded-xl p-6">
                <h3 className="font-semibold mb-4">Quiz Questions</h3>
                <div className="space-y-3">
                  {quizCards.length ? (
                    quizCards.map((item, index) => (
                      <div
                        key={index}
                        className="p-3 rounded-lg border border-primary/20 hover:border-primary/40 transition-all"
                      >
                        <p className="text-sm mb-2">{item.q}</p>
                        <p className="text-xs text-primary">
                          Answer: {item.options?.[item.answer] || "Not available"}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No quiz was generated.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
