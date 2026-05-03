import type { ConnectionStatus } from '../../types/websocket';

interface ConnectionIndicatorProps {
  status: ConnectionStatus;
}

/**
 * ConnectionIndicator displays WebSocket connection status.
 *
 * Visual states:
 * - connected: green dot, "Real-time updates active"
 * - connecting: yellow pulsing dot, "Connecting..."
 * - disconnected: red dot, "Disconnected - retrying"
 */
export function ConnectionIndicator({ status }: ConnectionIndicatorProps) {
  const statusConfig = {
    connected: {
      color: 'bg-green-500',
      animation: '',
      text: 'Real-time updates active',
    },
    connecting: {
      color: 'bg-yellow-500',
      animation: 'animate-pulse',
      text: 'Connecting...',
    },
    disconnected: {
      color: 'bg-red-500',
      animation: '',
      text: 'Disconnected - retrying',
    },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2" title={config.text}>
      <div className={`w-2 h-2 rounded-full ${config.color} ${config.animation}`} />
      <span className="text-xs text-gray-500">{config.text}</span>
    </div>
  );
}
