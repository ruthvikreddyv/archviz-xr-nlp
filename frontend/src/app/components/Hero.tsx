import { Link } from "react-router";
import {
  ArrowRight,
  Upload,
  Play,
  TrendingUp,
  Zap,
  Brain,
  FileText,
  ScanLine,
  Network,
  Glasses,
} from "lucide-react";
import { motion } from "motion/react";

export function Hero() {
  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-neon-pink/20 rounded-full blur-3xl animate-pulse delay-500" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            <div className="inline-block">
              <span className="px-4 py-2 rounded-full bg-gradient-to-r from-primary/20 to-secondary/20 border border-primary/30 text-sm">
                AI-Powered Research Comprehension
              </span>
            </div>

            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight">
              Turn Research{" "}
              <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent neon-glow">
                Diagrams
              </span>{" "}
              into AR Knowledge Graphs
            </h1>

            <p className="text-lg text-muted-foreground max-w-xl">
              ArchViz-XR uses OCR, NLP, and LLM technology to transform complex research paper
              diagrams into interactive 3D/AR knowledge graphs. Understand faster. Learn deeper.
              Explore in XR.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link
                to="/demo"
                className="group px-8 py-4 rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium hover:shadow-xl hover:shadow-primary/50 transition-all flex items-center justify-center gap-2"
              >
                <Play className="w-5 h-5" />
                Try Demo
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/upload"
                className="px-8 py-4 rounded-lg border border-primary/30 hover:border-primary/60 hover:bg-primary/10 transition-all flex items-center justify-center gap-2"
              >
                <Upload className="w-5 h-5" />
                Upload Diagram
              </Link>
            </div>

            <div className="grid grid-cols-3 gap-6 pt-8 border-t border-primary/20">
              <div>
                <div className="flex items-center gap-2 text-2xl font-bold text-primary">
                  <Brain className="w-6 h-6" />
                  50K+
                </div>
                <div className="text-sm text-muted-foreground">Nodes Extracted</div>
              </div>
              <div>
                <div className="flex items-center gap-2 text-2xl font-bold text-secondary">
                  <Zap className="w-6 h-6" />
                  12K+
                </div>
                <div className="text-sm text-muted-foreground">Papers Processed</div>
              </div>
              <div>
                <div className="flex items-center gap-2 text-2xl font-bold text-neon-orange">
                  <TrendingUp className="w-6 h-6" />
                  3.5x
                </div>
                <div className="text-sm text-muted-foreground">Faster Learning</div>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="glass-panel rounded-2xl p-6 neon-border">
              <PipelinePreview />
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function PipelinePreview() {
  const stages = [
    { label: "OCR", icon: ScanLine, color: "text-primary" },
    { label: "NLP", icon: Brain, color: "text-secondary" },
    { label: "Graph", icon: Network, color: "text-neon-pink" },
    { label: "XR", icon: Glasses, color: "text-neon-orange" },
  ];

  return (
    <div className="relative min-h-[520px] overflow-hidden rounded-xl border border-primary/20 bg-space-darker/80 p-5">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,217,255,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(0,217,255,0.06)_1px,transparent_1px)] bg-[size:34px_34px] opacity-40" />

      <div className="relative z-10 flex items-center justify-between border-b border-primary/20 pb-4">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-primary">Live Pipeline</p>
          <h3 className="mt-1 text-xl font-semibold">Diagram Comprehension</h3>
        </div>
        <div className="rounded-lg border border-primary/30 bg-primary/10 px-3 py-2 text-xs text-primary">
          23 nodes · 39 edges
        </div>
      </div>

      <div className="relative z-10 mt-6 grid gap-5 lg:grid-cols-[1fr_auto_1.15fr]">
        <div className="rounded-xl border border-primary/20 bg-space-dark/80 p-4">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <FileText className="h-4 w-4 text-primary" />
              Paper Diagram
            </div>
            <span className="text-xs text-muted-foreground">input.png</span>
          </div>

          <div className="relative aspect-[4/5] overflow-hidden rounded-lg border border-primary/10 bg-space-darker p-4">
            <motion.div
              animate={{ y: ["0%", "420%", "0%"] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="absolute left-0 right-0 top-4 h-0.5 bg-primary shadow-[0_0_24px_rgba(0,217,255,0.9)]"
            />
            <div className="space-y-3">
              <div className="h-4 w-2/3 rounded bg-primary/30" />
              <div className="grid grid-cols-2 gap-3">
                <div className="h-20 rounded-lg border border-secondary/30 bg-secondary/10" />
                <div className="h-20 rounded-lg border border-neon-pink/30 bg-neon-pink/10" />
              </div>
              <div className="h-3 w-full rounded bg-muted/30" />
              <div className="h-3 w-5/6 rounded bg-muted/20" />
              <div className="grid grid-cols-3 gap-2 pt-2">
                <div className="h-12 rounded border border-primary/20" />
                <div className="h-12 rounded border border-primary/20" />
                <div className="h-12 rounded border border-primary/20" />
              </div>
            </div>
          </div>
        </div>

        <div className="hidden items-center lg:flex">
          <motion.div
            animate={{ x: [0, 10, 0] }}
            transition={{ duration: 1.8, repeat: Infinity }}
            className="flex h-12 w-12 items-center justify-center rounded-full border border-primary/30 bg-primary/10"
          >
            <ArrowRight className="h-5 w-5 text-primary" />
          </motion.div>
        </div>

        <div className="rounded-xl border border-primary/20 bg-space-dark/80 p-4">
          <div className="mb-4 grid grid-cols-4 gap-2">
            {stages.map(({ label, icon: Icon, color }) => (
              <div key={label} className="rounded-lg border border-primary/10 bg-space-darker p-2 text-center">
                <Icon className={`mx-auto mb-1 h-4 w-4 ${color}`} />
                <p className="text-[10px] text-muted-foreground">{label}</p>
              </div>
            ))}
          </div>

          <div className="relative aspect-square rounded-lg border border-primary/10 bg-space-darker">
            <svg className="absolute inset-0 h-full w-full">
              {[
                ["50%", "50%", "22%", "30%"],
                ["50%", "50%", "75%", "28%"],
                ["50%", "50%", "28%", "72%"],
                ["50%", "50%", "78%", "70%"],
                ["22%", "30%", "75%", "28%"],
                ["28%", "72%", "78%", "70%"],
              ].map(([x1, y1, x2, y2], index) => (
                <motion.line
                  key={index}
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="url(#hero-edge-gradient)"
                  strokeWidth="2"
                  opacity="0.55"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.2, delay: index * 0.15, repeat: Infinity, repeatDelay: 3 }}
                />
              ))}
              <defs>
                <linearGradient id="hero-edge-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#00d9ff" />
                  <stop offset="100%" stopColor="#ec4899" />
                </linearGradient>
              </defs>
            </svg>

            {[
              { label: "Encoder", x: "50%", y: "50%", className: "h-20 w-20 from-primary to-secondary" },
              { label: "OCR", x: "22%", y: "30%", className: "h-12 w-12 from-primary to-cyan-400" },
              { label: "LLM", x: "75%", y: "28%", className: "h-12 w-12 from-secondary to-purple-400" },
              { label: "Quiz", x: "28%", y: "72%", className: "h-12 w-12 from-neon-orange to-amber-400" },
              { label: "XR", x: "78%", y: "70%", className: "h-12 w-12 from-neon-pink to-pink-400" },
            ].map((node, index) => (
              <motion.div
                key={node.label}
                animate={{ scale: index === 0 ? [1, 1.08, 1] : [1, 1.04, 1] }}
                transition={{ duration: 2.4, repeat: Infinity, delay: index * 0.2 }}
                className={`absolute flex -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-gradient-to-br ${node.className} text-[10px] font-bold text-white shadow-[0_0_28px_rgba(0,217,255,0.25)]`}
                style={{ left: node.x, top: node.y }}
              >
                {node.label}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
