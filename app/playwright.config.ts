import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  use: {
    baseURL: "http://127.0.0.1:4173",
  },
  webServer: {
    command:
      "./node_modules/.bin/svelte-kit sync && ./node_modules/.bin/vite build && ./node_modules/.bin/vite preview --host 127.0.0.1 --port 4173",
    port: 4173,
    reuseExistingServer: !process.env.CI,
  },
});
