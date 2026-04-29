import { useStore } from '../../stores';

type ConnectionStatusType = 'connecting' | 'connected' | 'disconnected';

interface ConnectionStatusProps {
  onReconnect?: () => void;
}

// Status dot colors per WebSocket state
const statusColors: Record<ConnectionStatusType, string> = {
  connecting: 'bg-yellow-400',
  connected: 'bg-green-500',
  disconnected: 'bg-red-500',
};

// Status labels for accessibility
const statusLabels: Record<ConnectionStatusType, string> = {
  connecting: 'Connecting...',
  connected: 'Connected',
  disconnected: 'Disconnected',
};

/**
 * ConnectionStatus displays WebSocket connection state with:
 * - Colored status dot (yellow/green/red)
 * - Connection status text
 * - Reconnect button (shown when disconnected)
 *
 * Integrates with useStore for connection status (per D-17~22).
 */
export function ConnectionStatus({ onReconnect }: ConnectionStatusProps) {
  const connectionStatus = useStore((state) => state.connectionStatus);

  // Map UI store status to component status
  const status: ConnectionStatusType = connectionStatus || 'disconnected';

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
      {/* Status indicator dot */}
      <div className="relative flex items-center justify-center">
        <div
          className={`w-3 h-3 rounded-full ${statusColors[status]} ${status === 'connecting' ? 'animate-pulse' : ''}`}
          aria-hidden="true"
        />
        {/* Pulse ring for connected state */}
        {status === 'connected' && (
          <div className="absolute w-3 h-3 rounded-full bg-green-500 opacity-50 animate-ping" />
        )}
      </div>

      {/* Status text */}
      <span className="text-sm font-medium text-gray-700">
        {statusLabels[status]}
      </span>

      {/* Reconnect button (only when disconnected) */}
      {status === 'disconnected' && onReconnect && (
        <button
          onClick={onReconnect}
          className="ml-2 px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
          aria-label="Reconnect to server"
        >
          Reconnect
        </button>
      )}
    </div>
  );
}

export default ConnectionStatus;
