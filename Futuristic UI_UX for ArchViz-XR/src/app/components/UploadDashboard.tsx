import { useState } from "react";
import { Upload, FileImage, FileText, CheckCircle, AlertCircle, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { motion } from "motion/react";
import { analyzeDiagram, loadDemoContract } from "../lib/api";

const demoExamples = [
  { id: 1, name: "Transformer Architecture", type: "AI/ML", preview: "AI" },
  { id: 2, name: "CNN Architecture", type: "Deep Learning", preview: "CV" },
  { id: 3, name: "Blockchain Flow", type: "System Design", preview: "BC" },
];

const recentUploads = [
  { id: 1, name: "Latest generated graph", status: "completed", date: "Saved locally" },
  { id: 2, name: "Transformer demo cache", status: "completed", date: "Backend /demo" },
  { id: 3, name: "Unsupported file example", status: "failed", date: "PNG, JPG, PDF only" },
];

export function UploadDashboard() {
  const navigate = useNavigate();
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    const validTypes = ["image/png", "image/jpeg", "application/pdf"];
    if (!validTypes.includes(file.type)) {
      setError("Please upload a PNG, JPG, or PDF file");
      return;
    }

    setSelectedFile(file);
    setError("");
    runAnalysis(file);
  };

  const runAnalysis = async (file: File) => {
    setUploadProgress(0);
    setIsProcessing(true);
    const interval = window.setInterval(() => {
      setUploadProgress((prev) => Math.min((prev ?? 0) + 8, 92));
    }, 350);

    try {
      await analyzeDiagram(file);
      setUploadProgress(100);
      navigate("/processing?source=upload");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      setUploadProgress(null);
    } finally {
      window.clearInterval(interval);
      setIsProcessing(false);
    }
  };

  const runDemo = async () => {
    setSelectedFile(null);
    setError("");
    setIsProcessing(true);
    setUploadProgress(35);

    try {
      await loadDemoContract();
      setUploadProgress(100);
      navigate("/processing?source=demo");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load demo");
      setUploadProgress(null);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-24">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">
              Upload{" "}
              <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
                Diagram
              </span>
            </h1>
            <p className="text-muted-foreground">
              Send your diagram to our OCR, NLP, LLM, and graph pipeline.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2">
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`glass-panel rounded-xl p-12 border-2 border-dashed transition-all ${
                  dragActive ? "border-primary bg-primary/10" : "border-primary/30"
                }`}
              >
                <input
                  type="file"
                  id="file-upload"
                  accept=".png,.jpg,.jpeg,.pdf"
                  onChange={handleChange}
                  className="hidden"
                  disabled={isProcessing}
                />

                {uploadProgress === null ? (
                  <label htmlFor="file-upload" className="flex flex-col items-center cursor-pointer">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center mb-4">
                      <Upload className="w-10 h-10 text-space-dark" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Drop your diagram here</h3>
                    <p className="text-muted-foreground text-center mb-4">or click to browse files</p>
                    <p className="text-sm text-muted-foreground">Supports PNG, JPG, PDF</p>
                  </label>
                ) : uploadProgress < 100 || isProcessing ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4">
                      <FileImage className="w-10 h-10 text-primary shrink-0" />
                      <div className="flex-1">
                        <p className="font-medium mb-1">
                          {selectedFile?.name || "Loading demo graph"}
                        </p>
                        <p className="text-xs text-muted-foreground mb-2">
                          Processing through the ArchViz-XR backend pipeline...
                        </p>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div
                            className="h-2 rounded-full bg-gradient-to-r from-primary to-secondary transition-all"
                            style={{ width: `${uploadProgress}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-sm text-muted-foreground">{uploadProgress}%</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center">
                    <CheckCircle className="w-16 h-16 text-primary mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">Graph Ready</h3>
                    <p className="text-muted-foreground mb-4">
                      Your real backend contract is saved and ready to explore.
                    </p>
                    <Link
                      to="/processing"
                      className="inline-block px-6 py-3 rounded-lg bg-gradient-to-r from-primary to-secondary text-space-dark font-medium"
                    >
                      Continue
                    </Link>
                  </div>
                )}
              </div>

              {error && (
                <div className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
                  {error}
                </div>
              )}
            </div>

            <div className="space-y-6">
              <div className="glass-panel rounded-xl p-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  Try Demo Examples
                </h3>
                <div className="space-y-3">
                  {demoExamples.map((example) => (
                    <button
                      key={example.id}
                      onClick={runDemo}
                      disabled={isProcessing}
                      className="w-full p-3 rounded-lg border border-primary/20 hover:border-primary/40 hover:bg-primary/5 transition-all text-left disabled:opacity-50"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold w-9 h-9 rounded-lg bg-primary/15 text-primary flex items-center justify-center">
                          {example.preview}
                        </span>
                        <div className="flex-1">
                          <p className="font-medium text-sm">{example.name}</p>
                          <p className="text-xs text-muted-foreground">{example.type}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-xl p-6">
            <h3 className="font-semibold mb-4">Recent Uploads</h3>
            <div className="space-y-3">
              {recentUploads.map((upload) => (
                <div
                  key={upload.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-primary/10 hover:border-primary/20 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium text-sm">{upload.name}</p>
                      <p className="text-xs text-muted-foreground">{upload.date}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {upload.status === "completed" ? (
                      <>
                        <CheckCircle className="w-5 h-5 text-primary" />
                        <Link
                          to="/results"
                          className="px-3 py-1 rounded-lg border border-primary/30 hover:border-primary/60 text-sm"
                        >
                          View
                        </Link>
                      </>
                    ) : (
                      <AlertCircle className="w-5 h-5 text-destructive" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
