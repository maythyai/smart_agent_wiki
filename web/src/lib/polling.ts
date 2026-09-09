/**
 * Configurable REST polling interval (ms) — the fallback refresh cadence
 * used by dashboard hooks when the WebSocket real-time channel is
 * disconnected (ADR-016).
 *
 * WS messages (agent_status / workflow_progress / page_updated) already
 * invalidate the relevant react-query caches via useWebSocket, yielding
 * near-real-time updates while WS is up; this interval only governs the
 * polling fallback. Raise it (e.g. 60000) via VITE_POLL_INTERVAL_MS on
 * deployments with a reliable WS link to cut redundant REST traffic.
 */
export const POLL_INTERVAL_MS: number =
  Number(import.meta.env.VITE_POLL_INTERVAL_MS) || 15000;

/**
 * Dashboard statistics refresh interval (ms). Independent from
 * POLL_INTERVAL_MS because stats are a heavier endpoint and refresh at a
 * slower cadence (default 30s). Configurable via VITE_STATS_INTERVAL_MS.
 */
export const STATS_INTERVAL_MS: number =
  Number(import.meta.env.VITE_STATS_INTERVAL_MS) || 30000;
