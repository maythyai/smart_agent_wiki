import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocket } from '../hooks/useWebSocket';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock WebSocket
class MockWebSocket {
  // Real WebSocket ready-state constants — the hook compares against
  // WebSocket.OPEN / WebSocket.CONNECTING, so the mock must define them
  // (otherwise `undefined === undefined` short-circuits connect()/send()).
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  static instances: MockWebSocket[] = [];

  url: string;
  readyState: number = WebSocket.CONNECTING;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((err: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);

    // Simulate async connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.();
    }, 10);
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.();
  }

  // Helper to simulate receiving messages
  simulateMessage(data: object) {
    this.onmessage?.({
      data: JSON.stringify(data),
    } as MessageEvent);
  }

  // Helper to simulate errors
  simulateError(error: Event) {
    this.onerror?.(error);
  }
}

// Mock global WebSocket
vi.stubGlobal('WebSocket', MockWebSocket);

// Mock the store
const mockStore = {
  setConnectionStatus: vi.fn(),
  updateAgent: vi.fn(),
  updateWorkflow: vi.fn(),
};

vi.mock('../stores', () => ({
  useStore: vi.fn((selector) => selector(mockStore)),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return React.createElement(QueryClientProvider, { client: queryClient }, children);
}

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Connection', () => {
    it('should connect automatically when autoConnect is true', async () => {
      const { result } = renderHook(() => useWebSocket({ autoConnect: true }), { wrapper });

      // Initially connecting
      expect(result.current.status).toBe('connecting');

      await waitFor(() => {
        expect(result.current.status).toBe('connected');
      });

      expect(mockStore.setConnectionStatus).toHaveBeenCalledWith('connected');
    });

    it('should not connect when autoConnect is false', () => {
      renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

      expect(MockWebSocket.instances.length).toBe(0);
    });

    it('should connect to correct URL with sessionId', async () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session', autoConnect: true }), { wrapper });

      await waitFor(() => {
        expect(MockWebSocket.instances.length).toBeGreaterThan(0);
      });

      expect(MockWebSocket.instances[0].url).toContain('test-session');
    });
  });

  describe('Message Handling', () => {
    it('should handle agent_status messages', async () => {
      renderHook(() => useWebSocket({ autoConnect: true }), { wrapper });

      await waitFor(() => {
        expect(MockWebSocket.instances.length).toBeGreaterThan(0);
      });

      const ws = MockWebSocket.instances[0];

      act(() => {
        ws.simulateMessage({
          type: 'agent_status',
          payload: { agent: 'Librarian', status: 'running', task: 'indexing' },
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockStore.updateAgent).toHaveBeenCalledWith({
        agent: 'Librarian',
        status: 'running',
        task: 'indexing',
      });
    });

    it('should handle workflow_progress messages', async () => {
      renderHook(() => useWebSocket({ autoConnect: true }), { wrapper });

      await waitFor(() => {
        expect(MockWebSocket.instances.length).toBeGreaterThan(0);
      });

      const ws = MockWebSocket.instances[0];

      act(() => {
        ws.simulateMessage({
          type: 'workflow_progress',
          payload: {
            workflow_id: 'wf-123',
            step: 'processing',
            total_steps: 5,
            current_step: 2,
            status: 'running',
          },
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockStore.updateWorkflow).toHaveBeenCalled();
    });

    it('should handle pong messages without action', async () => {
      renderHook(() => useWebSocket({ autoConnect: true }), { wrapper });

      await waitFor(() => {
        expect(MockWebSocket.instances.length).toBeGreaterThan(0);
      });

      const ws = MockWebSocket.instances[0];

      // Clear previous calls
      mockStore.updateAgent.mockClear();

      act(() => {
        ws.simulateMessage({
          type: 'pong',
          payload: {},
          timestamp: new Date().toISOString(),
        });
      });

      // Pong should not trigger any store updates
      expect(mockStore.updateAgent).not.toHaveBeenCalled();
    });
  });

  describe('Reconnection', () => {
    it('should provide reconnect function', async () => {
      const { result } = renderHook(() => useWebSocket({ autoConnect: true }), { wrapper });

      await waitFor(() => {
        expect(result.current.status).toBe('connected');
      });

      expect(typeof result.current.reconnect).toBe('function');

      act(() => {
        result.current.reconnect();
      });

      // Should create new WebSocket instance
      expect(MockWebSocket.instances.length).toBeGreaterThan(1);
    });
  });

  describe('Send Function', () => {
    it('should send data when connected', async () => {
      const { result } = renderHook(() => useWebSocket({ autoConnect: true }), { wrapper });

      await waitFor(() => {
        expect(result.current.status).toBe('connected');
      });

      const ws = MockWebSocket.instances[MockWebSocket.instances.length - 1];
      const sendSpy = vi.spyOn(ws, 'send');

      act(() => {
        result.current.send({ type: 'ping' });
      });

      expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({ type: 'ping' }));
    });

    it('should not send when disconnected', () => {
      const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

      // Should not throw when trying to send on disconnected socket
      expect(() => {
        result.current.send({ type: 'test' });
      }).not.toThrow();
    });
  });
});
