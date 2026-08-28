import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useStore } from '../stores';
import { getAccessToken } from '../lib/api';
import type { AgentStatus, WorkflowProgress } from '../types/api';
import type { ConnectionStatus, WSMessage } from '../types/websocket';

// Extended message type including 'pong' response is already in types/websocket.ts

interface UseWebSocketOptions {
  sessionId?: string;
  autoConnect?: boolean;
}

interface UseWebSocketReturn {
  status: ConnectionStatus;
  send: (data: unknown) => void;
  reconnect: () => void;
}

// WebSocket URL from env or default
const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

// Heartbeat interval (30 seconds per D-22)
const HEARTBEAT_INTERVAL = 30_000;

// Exponential backoff settings (per D-21)
const INITIAL_RECONNECT_DELAY = 1_000;
const MAX_RECONNECT_DELAY = 30_000;
const RECONNECT_MULTIPLIER = 2;

// F-WEB-02: stop reconnecting after this many failed attempts so a down
// server doesn't retry forever (and silently). Manual reconnect() resets it.
const MAX_RECONNECT_ATTEMPTS = 10;

/**
 * React hook for WebSocket connection management.
 * Provides auto-reconnect with exponential backoff and heartbeat.
 *
 * @param options Configuration options including sessionId and autoConnect
 * @returns WebSocket status, send function, and reconnect trigger
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { sessionId = 'default', autoConnect = true } = options;

  const [status, setStatus] = useState<ConnectionStatus>('disconnected');

  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const queryClient = useQueryClient();
  const setConnectionStatus = useStore((s) => s.setConnectionStatus);
  const updateAgent = useStore((s) => s.updateAgent);
  const updateWorkflow = useStore((s) => s.updateWorkflow);

  /**
   * Clear heartbeat interval
   */
  const clearHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
  }, []);

  /**
   * Start heartbeat ping every 30 seconds
   */
  const startHeartbeat = useCallback(() => {
    clearHeartbeat();
    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL);
  }, [clearHeartbeat]);

  /**
   * Calculate reconnection delay with exponential backoff
   */
  const getReconnectDelay = useCallback(() => {
    const delay = Math.pow(RECONNECT_MULTIPLIER, reconnectAttemptsRef.current) * INITIAL_RECONNECT_DELAY;
    return Math.min(delay, MAX_RECONNECT_DELAY);
  }, []);

  /**
   * Handle incoming WebSocket message
   */
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WSMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'pong':
            // Heartbeat response, no action needed
            break;

          case 'agent_status': {
            const agentStatus = message.payload as unknown as AgentStatus;
            updateAgent(agentStatus);
            queryClient.invalidateQueries({ queryKey: ['agents'] });
            break;
          }

          case 'workflow_progress': {
            const workflowProgress = message.payload as unknown as WorkflowProgress;
            updateWorkflow(workflowProgress);
            queryClient.invalidateQueries({ queryKey: ['agents'] });
            break;
          }

          case 'page_updated': {
            // Invalidate page and graph queries
            const slug = message.payload.slug as string | undefined;
            if (slug) {
              queryClient.invalidateQueries({ queryKey: ['page', slug] });
            }
            queryClient.invalidateQueries({ queryKey: ['graph'] });
            break;
          }

          default:
            console.warn('Unknown WebSocket message type:', message.type);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    },
    [updateAgent, updateWorkflow, queryClient]
  );

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus('connecting');
    setConnectionStatus('connecting');

    // Attach the JWT access token as ?token= so team-mode servers accept the
    // upgrade (local mode ignores it). Without this the WS is rejected in
    // team deployments.
    const token = getAccessToken();
    const url = `${WS_URL}/${sessionId}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;

      // Refetch agents on reconnect
      queryClient.invalidateQueries({ queryKey: ['agents'] });

      // Start heartbeat
      startHeartbeat();
    };

    ws.onclose = () => {
      setStatus('disconnected');
      setConnectionStatus('disconnected');
      clearHeartbeat();

      // F-WEB-02: cap reconnect attempts so a down server doesn't retry
      // forever and silently. Manual reconnect() resets the counter.
      if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
        return;
      }

      // Schedule reconnect with exponential backoff
      const delay = getReconnectDelay();
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttemptsRef.current++;
        connect();
      }, delay);
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    ws.onmessage = handleMessage;
  }, [
    sessionId,
    setConnectionStatus,
    queryClient,
    startHeartbeat,
    clearHeartbeat,
    getReconnectDelay,
    handleMessage,
  ]);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    clearHeartbeat();

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, [clearHeartbeat]);

  /**
   * Send data through WebSocket
   */
  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  /**
   * Manual reconnect trigger
   */
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    connect();
  }, [disconnect, connect]);

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
    send,
    reconnect,
  };
}
