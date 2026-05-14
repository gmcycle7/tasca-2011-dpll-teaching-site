import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// When built for GitHub Pages, assets and routes must be prefixed with
// the repo name. Set VITE_BASE in the deploy workflow; in local dev the
// base falls back to "/".
const base = process.env.VITE_BASE || "/";

export default defineConfig({
  base,
  plugins: [react()],
  server: {
    port: 5173,
    open: false,
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        // Split heavy third-party libs into their own chunks so the
        // entry bundle stays small. The syntax highlighter is the
        // dominant cost; KaTeX is also non-trivial.
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("react-syntax-highlighter") ||
                id.includes("refractor") ||
                id.includes("prismjs")) {
              return "vendor-syntax";
            }
            if (id.includes("katex") || id.includes("react-katex")) {
              return "vendor-math";
            }
            if (id.includes("react-router")) {
              return "vendor-router";
            }
            if (id.includes("react-dom")) {
              return "vendor-react-dom";
            }
            if (id.includes("react")) {
              return "vendor-react";
            }
          }
        },
      },
    },
  },
});
