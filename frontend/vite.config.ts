import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Civic Pulse",
        short_name: "CivicPulse",
        theme_color: "#2563eb",
      },
    }),
  ],
});
