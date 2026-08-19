import { useEffect, useRef, useState, useCallback } from 'react';
import { useIntegrationsStore } from '../stores/integrationsStore';
import { getAccessToken } from '../lib/api';
import type { ConnectionStatus, IntegrationWSMessage, ConnectorHealthData, SyncProgressData } from '../types/websocket';

// WebSocket URL construction
const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

// Exponential backoff settings (per T-16-06 mitigation)
const INITIAL_RECONNECT_DELAY = 1_000;
const MAX_RECONNECT_DELAY = 30_000;
const RECONNECT_MULTIPLIER = 2;

interface UseIntegrationWebSocketOptions {
  platforms?: string[];
  autoConnect?: boolean;
}

interface UseIntegrationWebSocketReturn {
  status: ConnectionStatus;
  subscribe: (platform: string) => void;
  unsubscribe: (platform: string) => void;
}

/**
 * React hook for integration dashboard WebSocket connection.
 * Provides real-time updates for connector health and sync progress.
 *
 * Features:
 * - Auto-connect on mount
 * - Exponential backoff reconnection (max 30s)
 * - Platform-based subscription filtering
 * - Store updates on received messages
 *
 * @param options Configuration options including platforms to subscribe and autoConnect
 * @returns WebSocket status, subscribe, and unsubscribe functions
 */
export function useIntegrationWebSocket(
  options: UseIntegrationWebSocketOptions = {}
): UseIntegrationWebSocketReturn {
  const { platforms, autoConnect = true } = options;

  const [status, setStatus] = useState<ConnectionStatus>('connecting');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const updateConnectorHealth = useIntegrationsStore((s) => s.updateConnectorHealth);
  const updateSyncProgress = useIntegrationsStore((s) => s.updateSyncProgress);

  /**
   * Calculate reconnection delay with exponential backoff
   * Caps at 30 seconds per T-16-06 mitigation
   */
  const getReconnectDelay = useCallback(() => {
    const delay = Math.pow(RECONNECT_MULTIPLIER, reconnectAttemptsRef.current) * INITIAL_RECONNECT_DELAY;
    return Math.min(delay, MAX_RECONNECT_DELAY);
  }, []);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus('connecting');
    // Attach the JWT access token as ?token= for team-mode auth (local mode
    // ignores it).
    const token = getAccessToken();
    const ws = new WebSocket(`${WS_URL}/integrations${token ? `?token=${encodeURIComponent(token)}` : ''}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      reconnectAttemptsRef.current = 0;

      // Subscribe to specified platforms
      if (platforms && platforms.length > 0) {
        platforms.forEach((p) => {
          ws.send(JSON.stringify({ action: 'subscribe', platform: p }));
        });
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg: IntegrationWSMessage = JSON.parse(event.data);

        switch (msg.type) {
          case 'connector_health':
            if (msg.platform && msg.data) {
              updateConnectorHealth(msg.platform, msg.data as ConnectorHealthData);
            }
            break;

          case 'sync_progress':
            if (msg.platform && msg.data) {
              updateSyncProgress(msg.platform, msg.data as SyncProgressData);
            }
            break;

          case 'ping':
            // Respond to ping with pong
            ws.send(JSON.stringify({ type: 'pong' }));
            break;

          case 'subscribed':
          case 'unsubscribed':
          case 'connection_status':
            // Informational messages, no action needed
            break;

          default:
            console.warn('Unknown integration WebSocket message type:', msg.type);
        }
      } catch (err) {
        console.error('Failed to parse integration WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      setStatus('disconnected');

      // Schedule reconnect with exponential backoff
      const delay = getReconnectDelay();
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttemptsRef.current++;
        connect();
      }, delay);
    };

    ws.onerror = () => {
      // Close on error, onclose will handle reconnection
      ws.close();
    };
  }, [platforms, updateConnectorHealth, updateSyncProgress, getReconnectDelay]);

  /**
   * Subscribe to a specific platform's updates
   */
  const subscribe = useCallback((platform: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'subscribe', platform }));
    }
  }, []);

  /**
   * Unsubscribe from a specific platform's updates
   */
  const unsubscribe = useCallback((platform: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'unsubscribe', platform }));
    }
  }, []);

  /**
   * Disconnect and cleanup
   */
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    status,
    subscribe,
    unsubscribe,
  };
}
