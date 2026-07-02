import { Link } from "react-router";
import { Menu, X, LogIn, Sparkles } from "lucide-react";
import { useState } from "react";

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-panel border-b border-primary/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center neon-border">
              <Sparkles className="w-6 h-6 text-space-dark" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent neon-glow">
              ArchViz-XR
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            <Link to="/" className="text-sm hover:text-primary transition-colors">
              Home
            </Link>
            <Link to="/features" className="text-sm hover:text-primary transition-colors">
              Features
            </Link>
            <Link to="/demo" className="text-sm hover:text-primary transition-colors">
              Demo
            </Link>
            <Link to="/how-it-works" className="text-sm hover:text-primary transition-colors">
              How It Works
            </Link>
            <Link to="/research" className="text-sm hover:text-primary transition-colors">
              Research
            </Link>
            <Link to="/contact" className="text-sm hover:text-primary transition-colors">
              Contact
            </Link>
          </div>

          {/* Desktop Actions */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              to="/login"
              className="px-4 py-2 text-sm rounded-lg border border-primary/30 hover:border-primary/60 transition-all flex items-center gap-2"
            >
              <LogIn className="w-4 h-4" />
              Login
            </Link>
            <Link
              to="/signup"
              className="px-4 py-2 text-sm rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium hover:shadow-lg hover:shadow-primary/50 transition-all"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-white/10"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-panel border-t border-primary/20">
          <div className="px-4 py-4 space-y-3">
            <Link to="/" className="block text-sm hover:text-primary transition-colors py-2">
              Home
            </Link>
            <Link to="/features" className="block text-sm hover:text-primary transition-colors py-2">
              Features
            </Link>
            <Link to="/demo" className="block text-sm hover:text-primary transition-colors py-2">
              Demo
            </Link>
            <Link to="/how-it-works" className="block text-sm hover:text-primary transition-colors py-2">
              How It Works
            </Link>
            <Link to="/research" className="block text-sm hover:text-primary transition-colors py-2">
              Research
            </Link>
            <Link to="/contact" className="block text-sm hover:text-primary transition-colors py-2">
              Contact
            </Link>
            <div className="pt-3 border-t border-primary/20 space-y-2">
              <Link
                to="/login"
                className="block px-4 py-2 text-sm rounded-lg border border-primary/30 text-center"
              >
                Login
              </Link>
              <Link
                to="/signup"
                className="block px-4 py-2 text-sm rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium text-center"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
