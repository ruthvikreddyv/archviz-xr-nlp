import { ScanText, Brain, Network, Glasses, Mic, ClipboardList } from "lucide-react";
import { motion } from "motion/react";

const features = [
  {
    icon: ScanText,
    title: "OCR-Based Understanding",
    description: "Advanced optical character recognition extracts text and structural information from any research diagram format.",
    color: "from-primary to-cyan-400",
  },
  {
    icon: Brain,
    title: "LLM Concept Extraction",
    description: "State-of-the-art language models identify concepts, relationships, and hierarchies from extracted text.",
    color: "from-secondary to-purple-400",
  },
  {
    icon: Network,
    title: "3D Knowledge Graphs",
    description: "Interactive 3D visualizations make complex relationships intuitive and explorable in real-time.",
    color: "from-neon-pink to-pink-400",
  },
  {
    icon: Glasses,
    title: "AR/XR Exploration",
    description: "Step inside your knowledge graph with immersive AR and XR experiences for deeper understanding.",
    color: "from-neon-orange to-amber-400",
  },
  {
    icon: Mic,
    title: "Voice-Based Tutoring",
    description: "Ask questions about any node or concept and receive AI-powered explanations through natural conversation.",
    color: "from-blue-400 to-primary",
  },
  {
    icon: ClipboardList,
    title: "Quiz Generation",
    description: "Automatically generate comprehension quizzes based on extracted concepts to reinforce learning.",
    color: "from-purple-400 to-secondary",
  },
];

export function Features() {
  return (
    <div className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl font-bold mb-4">
            Powerful{" "}
            <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
              Features
            </span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Everything you need to transform complex research diagrams into interactive learning experiences
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="glass-panel rounded-xl p-6 hover:border-primary/40 transition-all group"
            >
              <div
                className={`w-14 h-14 rounded-lg bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
              >
                <feature.icon className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
