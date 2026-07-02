import { Link } from "react-router";
import { Sparkles, Github, Twitter, Linkedin, Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="glass-panel border-t border-primary/20 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center neon-border">
                <Sparkles className="w-6 h-6 text-space-dark" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
                ArchViz-XR
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Transform research diagrams into interactive AR knowledge graphs with AI.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <Link to="/features" className="hover:text-primary transition-colors">
                  Features
                </Link>
              </li>
              <li>
                <Link to="/demo" className="hover:text-primary transition-colors">
                  Demo
                </Link>
              </li>
              <li>
                <Link to="/how-it-works" className="hover:text-primary transition-colors">
                  How It Works
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <Link to="/research" className="hover:text-primary transition-colors">
                  Research
                </Link>
              </li>
              <li>
                <a href="#docs" className="hover:text-primary transition-colors">
                  Documentation
                </a>
              </li>
              <li>
                <a href="#api" className="hover:text-primary transition-colors">
                  API Reference
                </a>
              </li>
              <li>
                <a href="#github" className="hover:text-primary transition-colors">
                  GitHub
                </a>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <Link to="/privacy" className="hover:text-primary transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms" className="hover:text-primary transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-primary transition-colors">
                  Contact
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-primary/20 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © 2026 ArchViz-XR. All rights reserved.
          </p>

          <div className="flex items-center gap-4">
            <a
              href="#github"
              className="w-10 h-10 rounded-lg glass-panel flex items-center justify-center hover:border-primary/50 transition-all"
            >
              <Github className="w-5 h-5" />
            </a>
            <a
              href="#twitter"
              className="w-10 h-10 rounded-lg glass-panel flex items-center justify-center hover:border-primary/50 transition-all"
            >
              <Twitter className="w-5 h-5" />
            </a>
            <a
              href="#linkedin"
              className="w-10 h-10 rounded-lg glass-panel flex items-center justify-center hover:border-primary/50 transition-all"
            >
              <Linkedin className="w-5 h-5" />
            </a>
            <a
              href="#email"
              className="w-10 h-10 rounded-lg glass-panel flex items-center justify-center hover:border-primary/50 transition-all"
            >
              <Mail className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
