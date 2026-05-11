import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      "/fireant_data": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
});
