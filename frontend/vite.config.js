import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),

    VitePWA({
      disable: true,

      registerType: "autoUpdate",

      includeAssets: [
        "favicon.svg",
        "icons.svg",
      ],

      manifest: {
        name: "NextFarm VoiceLog",

        short_name: "VoiceLog",

        description:
          "Ứng dụng ghi nhật ký nông nghiệp bằng giọng nói và AI.",

        theme_color: "#2e7d32",

        background_color: "#ffffff",

        display: "standalone",

        start_url: "/",

        scope: "/",

        icons: [
          {
            src: "/pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },

          {
            src: "/pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },

      workbox: {
        globPatterns: [
          "**/*.{js,css,html,svg,png,ico}",
        ],
      },
    }),
  ],

  // Cho phép Vite Preview nhận request
  // từ Cloudflare Quick Tunnel.
  preview: {
    host: "0.0.0.0",

    allowedHosts: [
      ".trycloudflare.com",
    ],
  },
});