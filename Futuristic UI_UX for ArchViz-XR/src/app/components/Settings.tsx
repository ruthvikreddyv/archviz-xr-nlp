import { useState } from "react";
import { User, Key, Palette, Save, Download, Trash2, Moon, Sun } from "lucide-react";
import { motion } from "motion/react";

export function Settings() {
  const [theme, setTheme] = useState("dark");
  const [apiKey, setApiKey] = useState("");

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-24">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">
              Settings &{" "}
              <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
                Profile
              </span>
            </h1>
            <p className="text-muted-foreground">Manage your account and preferences</p>
          </div>

          <div className="space-y-6">
            {/* Profile Settings */}
            <div className="glass-panel rounded-xl p-6">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <User className="w-5 h-5 text-primary" />
                Profile Information
              </h2>

              <div className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm mb-2">Full Name</label>
                    <input
                      type="text"
                      defaultValue="John Doe"
                      className="w-full px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-sm mb-2">Email</label>
                    <input
                      type="email"
                      defaultValue="john@example.com"
                      className="w-full px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm mb-2">Role</label>
                  <select className="w-full px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all">
                    <option>Student</option>
                    <option>Researcher</option>
                    <option>Educator</option>
                    <option>Reviewer</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm mb-2">Institution</label>
                  <input
                    type="text"
                    placeholder="e.g., Stanford University"
                    className="w-full px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
                  />
                </div>

                <button className="px-6 py-3 rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium hover:shadow-lg hover:shadow-primary/50 transition-all flex items-center gap-2">
                  <Save className="w-5 h-5" />
                  Save Changes
                </button>
              </div>
            </div>

            {/* API Settings */}
            <div className="glass-panel rounded-xl p-6">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Key className="w-5 h-5 text-primary" />
                API Configuration
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2">API Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk-..."
                      className="flex-1 px-4 py-3 rounded-lg bg-input-background border border-primary/20 focus:border-primary/60 outline-none transition-all"
                    />
                    <button className="px-4 py-3 rounded-lg border border-primary/30 hover:border-primary/60 transition-all">
                      Generate
                    </button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Used for custom model integrations and API access
                  </p>
                </div>

                <div className="p-4 rounded-lg bg-primary/10 border border-primary/30">
                  <p className="text-sm font-medium mb-2">API Usage This Month</p>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Requests</p>
                      <p className="font-semibold">1,247</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Diagrams</p>
                      <p className="font-semibold">42</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Quota</p>
                      <p className="font-semibold">85%</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Theme Settings */}
            <div className="glass-panel rounded-xl p-6">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Palette className="w-5 h-5 text-primary" />
                Appearance
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-3">Theme</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => setTheme("dark")}
                      className={`p-4 rounded-lg border transition-all ${
                        theme === "dark"
                          ? "border-primary bg-primary/10"
                          : "border-primary/20 hover:border-primary/40"
                      }`}
                    >
                      <Moon className="w-6 h-6 mx-auto mb-2" />
                      <p className="text-sm">Dark</p>
                    </button>
                    <button
                      onClick={() => setTheme("light")}
                      className={`p-4 rounded-lg border transition-all ${
                        theme === "light"
                          ? "border-primary bg-primary/10"
                          : "border-primary/20 hover:border-primary/40"
                      }`}
                    >
                      <Sun className="w-6 h-6 mx-auto mb-2" />
                      <p className="text-sm">Light</p>
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm mb-2">Accent Color</label>
                  <div className="flex gap-2">
                    {["#00d9ff", "#8b5cf6", "#ec4899", "#f97316"].map((color) => (
                      <button
                        key={color}
                        className="w-12 h-12 rounded-lg border-2 border-primary/30 hover:scale-110 transition-transform"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Animations</p>
                    <p className="text-xs text-muted-foreground">Enable UI animations</p>
                  </div>
                  <label className="relative inline-block w-12 h-6">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-12 h-6 bg-muted rounded-full peer-checked:bg-primary transition-all cursor-pointer"></div>
                    <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-all peer-checked:translate-x-6"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Particle Effects</p>
                    <p className="text-xs text-muted-foreground">Show animated particles in graph</p>
                  </div>
                  <label className="relative inline-block w-12 h-6">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-12 h-6 bg-muted rounded-full peer-checked:bg-primary transition-all cursor-pointer"></div>
                    <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-all peer-checked:translate-x-6"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* Data Management */}
            <div className="glass-panel rounded-xl p-6">
              <h2 className="text-xl font-semibold mb-6">Data Management</h2>

              <div className="space-y-3">
                <button className="w-full px-6 py-3 rounded-lg border border-primary/30 hover:border-primary/60 transition-all flex items-center justify-center gap-2">
                  <Download className="w-5 h-5" />
                  Export All Graphs
                </button>
                <button className="w-full px-6 py-3 rounded-lg border border-primary/30 hover:border-primary/60 transition-all flex items-center justify-center gap-2">
                  <Download className="w-5 h-5" />
                  Download Processing History
                </button>
                <button className="w-full px-6 py-3 rounded-lg border border-destructive/30 hover:border-destructive/60 hover:bg-destructive/10 text-destructive transition-all flex items-center justify-center gap-2">
                  <Trash2 className="w-5 h-5" />
                  Clear All Data
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
