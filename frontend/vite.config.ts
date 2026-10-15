import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

import { reticle } from '@reticlehq/vite-plugin';
export default defineConfig({
  plugins: [reticle({ port: 4400 }), react()],
  base: "./",
  build: {
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: false,
    emptyOutDir: true,
  },
  server: {
    port: 5173,
  },
});
