import { useState } from "react";
import { Mail, Lock, User, Github, ArrowRight } from "lucide-react";
import { Link } from "react-router";
import { motion } from "motion/react";

export function LoginSignup({ mode = "login" }: { mode?: "login" | "signup" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("student");

  const isLogin = mode === "login";

  return (
    <div className="min-h-screen flex items-center justify-center px-4 pt-16">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md"
      >
        <div className="glass-panel rounded-2xl p-8 neon-border">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-2">
              {isLogin ? "Welcome Back" : "Get Started"}
            </h2>
            <p className="text-muted-foreground">
              {isLogin
                ? "Sign in to continue exploring knowledge graphs"
                : "Create your account to start transforming diagrams"}
            </p>
          </div>

          {/* Social Login */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <button className="px-4 py-3 rounded-lg border border-primary/30 hover:border-primary/60 hover:bg-primary/10 transition-all flex items-center justify-center gap-2">
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Google
            </button>
            <button className="px-4 py-3 rounded-lg border border-primary/30 hover:border-primary/60 hover:bg-primary/10 transition-all flex items-center justify-center gap-2">
              <Github className="w-5 h-5" />
              GitHub
            </button>
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-primary/20"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-space-dark text-muted-foreground">Or continue with email</span>
            </div>
          </div>

          {/* Form */}
          <form className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm mb-2">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full pl-10 pr-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
                />
              </div>
            </div>

            {!isLogin && (
              <div>
                <label className="block text-sm mb-2">I am a...</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
                >
                  <option value="student">Student</option>
                  <option value="researcher">Researcher</option>
                  <option value="educator">Educator</option>
                  <option value="reviewer">Reviewer</option>
                </select>
              </div>
            )}

            {isLogin && (
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2">
                  <input type="checkbox" className="rounded border-primary/30" />
                  Remember me
                </label>
                <Link to="/forgot-password" className="text-primary hover:underline">
                  Forgot password?
                </Link>
              </div>
            )}

            <button
              type="submit"
              className="w-full py-3 rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium hover:shadow-lg hover:shadow-primary/50 transition-all flex items-center justify-center gap-2"
            >
              {isLogin ? "Sign In" : "Create Account"}
              <ArrowRight className="w-5 h-5" />
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-sm text-muted-foreground mt-6">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <Link
              to={isLogin ? "/signup" : "/login"}
              className="text-primary hover:underline font-medium"
            >
              {isLogin ? "Sign up" : "Sign in"}
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
