import { Upload, ScanLine, Network, Box, MessageCircle, CheckCircle } from "lucide-react";
import { motion } from "motion/react";

const steps = [
  {
    icon: Upload,
    title: "Upload Diagram",
    description: "Drop your research diagram (PNG, JPG, or PDF) into the platform.",
    color: "from-primary to-cyan-400",
  },
  {
    icon: ScanLine,
    title: "Extract with OCR",
    description: "Advanced OCR technology extracts all text and structural elements.",
    color: "from-cyan-400 to-secondary",
  },
  {
    icon: Network,
    title: "Detect Concepts",
    description: "AI identifies concepts, entities, and their relationships.",
    color: "from-secondary to-neon-pink",
  },
  {
    icon: Box,
    title: "Generate Graph",
    description: "Transform concepts into an interactive 3D knowledge graph.",
    color: "from-neon-pink to-neon-orange",
  },
  {
    icon: MessageCircle,
    title: "Explore in 3D/AR",
    description: "Navigate your graph in immersive 3D or AR/XR environments.",
    color: "from-neon-orange to-amber-400",
  },
  {
    icon: CheckCircle,
    title: "Learn & Quiz",
    description: "Ask questions, get explanations, and test your understanding.",
    color: "from-amber-400 to-primary",
  },
];

export function HowItWorks() {
  return (
    <div className="py-20 relative">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-secondary/30 rounded-full blur-3xl"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl font-bold mb-4">
            How It{" "}
            <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
              Works
            </span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Six simple steps from diagram to interactive AR knowledge graph
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="relative"
            >
              <div className="glass-panel rounded-xl p-6 h-full hover:border-primary/40 transition-all">
                {/* Step Number */}
                <div className="absolute -top-4 -left-4 w-12 h-12 rounded-full bg-gradient-to-br from-space-dark to-space-darker border-2 border-primary flex items-center justify-center font-bold text-xl">
                  {index + 1}
                </div>

                <div
                  className={`w-16 h-16 rounded-lg bg-gradient-to-br ${step.color} flex items-center justify-center mb-4 mt-2`}
                >
                  <step.icon className="w-8 h-8 text-white" />
                </div>

                <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                <p className="text-muted-foreground">{step.description}</p>
              </div>

              {/* Connection Line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-primary/50 to-transparent"></div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
