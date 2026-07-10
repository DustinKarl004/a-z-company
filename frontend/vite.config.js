import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

// Stamped once per build; compared against at runtime so open tabs can
// detect a new production deploy without the user needing to hard-refresh.
const buildVersion = String(Date.now())

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'write-version-file',
      writeBundle(options) {
        writeFileSync(
          resolve(options.dir, 'version.json'),
          JSON.stringify({ version: buildVersion })
        )
      },
    },
  ],
  define: {
    __APP_VERSION__: JSON.stringify(buildVersion),
  },
})
