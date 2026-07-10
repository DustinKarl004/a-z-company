const POLL_INTERVAL_MS = 60_000

// Set by vite.config.js at build time; compared against /version.json
// (written by the same build) to detect that a newer deploy exists.
const CURRENT_VERSION = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : null

export function startVersionCheck(onNewVersion) {
  if (!CURRENT_VERSION) return () => {}

  async function check() {
    try {
      const res = await fetch(`/version.json?t=${Date.now()}`, { cache: 'no-store' })
      if (!res.ok) return
      const { version } = await res.json()
      if (version && version !== CURRENT_VERSION) {
        onNewVersion()
      }
    } catch {
      // Network hiccup — just try again next interval.
    }
  }

  const intervalId = setInterval(check, POLL_INTERVAL_MS)
  return () => clearInterval(intervalId)
}
