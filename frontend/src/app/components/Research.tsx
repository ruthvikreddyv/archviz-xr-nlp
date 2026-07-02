import { BookOpen, GraduationCap, Microscope, Users, Presentation, FileSearch } from "lucide-react";
import { motion } from "motion/react";

const useCases = [
  {
    icon: BookOpen,
    title: "Research Paper Comprehension",
    description: "Transform complex academic diagrams into interactive visualizations for faster understanding of novel research concepts.",
    color: "from-primary to-cyan-400",
    stats: "85% faster comprehension",
  },
  {
    icon: GraduationCap,
    title: "Classroom Teaching",
    description: "Engage students with immersive 3D/AR visualizations of complex topics, making abstract concepts tangible and memorable.",
    color: "from-secondary to-purple-400",
    stats: "3.2x student engagement",
  },
  {
    icon: Microscope,
    title: "AI Architecture Analysis",
    description: "Decode neural network architectures, system designs, and ML pipelines with automatic concept extraction and relationship mapping.",
    color: "from-neon-pink to-pink-400",
    stats: "12K+ diagrams processed",
  },
  {
    icon: FileSearch,
    title: "Literature Review",
    description: "Build comprehensive knowledge graphs across multiple papers to identify connections, gaps, and research opportunities.",
    color: "from-neon-orange to-amber-400",
    stats: "50+ papers analyzed",
  },
  {
    icon: Users,
    title: "Peer Review & Evaluation",
    description: "Reviewers can quickly grasp complex methodologies and architectures, improving review quality and efficiency.",
    color: "from-blue-400 to-primary",
    stats: "40% faster reviews",
  },
  {
    icon: Presentation,
    title: "Conference Demos",
    description: "Create stunning presentations with interactive AR knowledge graphs that captivate audiences and communicate ideas effectively.",
    color: "from-purple-400 to-secondary",
    stats: "Perfect for hackathons",
  },
];

const testimonials = [
  {
    name: "Dr. Sarah Chen",
    role: "ML Researcher, Stanford",
    quote: "ArchViz-XR helped me understand a complex GNN architecture in minutes instead of hours. The 3D visualization made the relationships immediately clear.",
    avatar: "👩‍🔬",
  },
  {
    name: "Prof. James Kumar",
    role: "CS Professor, MIT",
    quote: "My students are finally excited about system architecture diagrams. The AR exploration mode is a game-changer for visual learners.",
    avatar: "👨‍🏫",
  },
  {
    name: "Alex Rodriguez",
    role: "PhD Candidate, Berkeley",
    quote: "Literature review became so much easier. I can now see connections between papers that I would have missed otherwise.",
    avatar: "🎓",
  },
];

export function Research() {
  return (
    <div className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl font-bold mb-4">
            Research &{" "}
            <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
              Use Cases
            </span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Transforming how researchers, educators, and students interact with complex diagrams
          </p>
        </motion.div>

        {/* Use Cases */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-20">
          {useCases.map((useCase, index) => (
            <motion.div
              key={useCase.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="glass-panel rounded-xl p-6 hover:border-primary/40 transition-all group"
            >
              <div
                className={`w-14 h-14 rounded-lg bg-gradient-to-br ${useCase.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}
              >
                <useCase.icon className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{useCase.title}</h3>
              <p className="text-muted-foreground mb-3">{useCase.description}</p>
              <div className="inline-block px-3 py-1 rounded-full bg-primary/20 border border-primary/30 text-xs text-primary font-medium">
                {useCase.stats}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Testimonials */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-20"
        >
          <h3 className="text-3xl font-bold text-center mb-12">
            What{" "}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Researchers
            </span>{" "}
            Say
          </h3>

          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={testimonial.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="glass-panel rounded-xl p-6"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-2xl">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <p className="font-semibold">{testimonial.name}</p>
                    <p className="text-xs text-muted-foreground">{testimonial.role}</p>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground italic">"{testimonial.quote}"</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Before/After Comparison */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="glass-panel rounded-xl p-8"
        >
          <h3 className="text-3xl font-bold text-center mb-8">
            Traditional vs{" "}
            <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              ArchViz-XR
            </span>
          </h3>

          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <div className="inline-block px-3 py-1 rounded-full bg-muted text-muted-foreground text-sm mb-4">
                Traditional Approach
              </div>
              <ul className="space-y-3">
                {[
                  "Manual diagram analysis",
                  "Static 2D representation",
                  "Text-heavy explanations",
                  "Limited interactivity",
                  "Hours of comprehension time",
                  "Difficult to share insights",
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-muted-foreground">
                    <span className="text-destructive mt-1">✗</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <div className="inline-block px-3 py-1 rounded-full bg-primary/20 text-primary text-sm mb-4">
                With ArchViz-XR
              </div>
              <ul className="space-y-3">
                {[
                  "AI-powered automatic extraction",
                  "Interactive 3D/AR visualization",
                  "LLM-generated explanations",
                  "Voice-based Q&A",
                  "Minutes to full understanding",
                  "Exportable knowledge graphs",
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-primary mt-1">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
