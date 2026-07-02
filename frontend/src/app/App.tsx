import { BrowserRouter, Routes, Route } from "react-router";
import { Navbar } from "./components/Navbar";
import { Hero } from "./components/Hero";
import { Features } from "./components/Features";
import { HowItWorks } from "./components/HowItWorks";
import { Research } from "./components/Research";
import { LoginSignup } from "./components/LoginSignup";
import { UploadDashboard } from "./components/UploadDashboard";
import { ProcessingPipeline } from "./components/ProcessingPipeline";
import { ResultsScreen } from "./components/ResultsScreen";
import { GraphViewer } from "./components/GraphViewer";
import { Settings } from "./components/Settings";
import { Footer } from "./components/Footer";

function HomePage() {
  return (
    <>
      <Hero />
      <Features />
      <HowItWorks />
      <Research />
    </>
  );
}

function ContactPage() {
  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-24">
      <div className="max-w-2xl mx-auto glass-panel rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-4">
          Contact{" "}
          <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Us
          </span>
        </h1>
        <p className="text-muted-foreground mb-8">
          Have questions? We'd love to hear from you.
        </p>
        <form className="space-y-4">
          <div>
            <label className="block text-sm mb-2">Name</label>
            <input
              type="text"
              className="w-full px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
            />
          </div>
          <div>
            <label className="block text-sm mb-2">Email</label>
            <input
              type="email"
              className="w-full px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
            />
          </div>
          <div>
            <label className="block text-sm mb-2">Message</label>
            <textarea
              rows={6}
              className="w-full px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all resize-none"
            ></textarea>
          </div>
          <button className="w-full px-6 py-3 rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium hover:shadow-lg hover:shadow-primary/50 transition-all">
            Send Message
          </button>
        </form>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/features" element={<Features />} />
          <Route path="/how-it-works" element={<HowItWorks />} />
          <Route path="/research" element={<Research />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/login" element={<LoginSignup mode="login" />} />
          <Route path="/signup" element={<LoginSignup mode="signup" />} />
          <Route path="/demo" element={<UploadDashboard />} />
          <Route path="/upload" element={<UploadDashboard />} />
          <Route path="/processing" element={<ProcessingPipeline />} />
          <Route path="/results" element={<ResultsScreen />} />
          <Route path="/graph-viewer" element={<GraphViewer />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
