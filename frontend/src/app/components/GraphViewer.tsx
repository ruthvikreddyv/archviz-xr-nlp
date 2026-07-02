import { ExternalLink, Maximize2, Network } from "lucide-react";
import { motion } from "motion/react";
import { getArViewerUrl } from "../lib/api";

export function GraphViewer() {
  const arViewerUrl = getArViewerUrl();

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-24">
      <div className="max-w-[1600px] mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-1">
                3D Knowledge{" "}
                <span className="bg-gradient-to-r from-primary via-secondary to-neon-pink bg-clip-text text-transparent">
                  Galaxy
                </span>
              </h1>
              <p className="text-sm text-muted-foreground">
                This view is the real Three.js/WebXR graph from archviz-ro/main.js.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <a
                href={arViewerUrl}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 rounded-lg border border-primary/30 hover:border-primary/60 transition-all flex items-center gap-2"
              >
                <ExternalLink className="w-5 h-5" />
                Open Full Screen
              </a>
            </div>
          </div>

          <div className="glass-panel rounded-xl overflow-hidden border border-primary/20">
            <div className="flex items-center justify-between px-5 py-3 border-b border-primary/20 bg-space-darker/70">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Network className="w-4 h-4 text-primary" />
                Live AR viewer mounted from backend /ar/index.html
              </div>
              <Maximize2 className="w-4 h-4 text-muted-foreground" />
            </div>

            <iframe
              title="ArchViz-XR AR Knowledge Graph"
              src={arViewerUrl}
              className="w-full h-[calc(100vh-220px)] min-h-[620px] bg-black"
              allow="xr-spatial-tracking; microphone; camera; fullscreen"
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
}
