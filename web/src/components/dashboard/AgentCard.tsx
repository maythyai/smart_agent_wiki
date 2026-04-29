import type { AgentStatus } from '../../types/api';

interface AgentCardProps {
  agent: AgentStatus;
}

// Status badge colors per D-17~19 design
const statusColors: Record<AgentStatus['status'], string> = {
  idle: 'bg-gray-100 text-gray-600',
  running: 'bg-blue-100 text-blue-700 animate-pulse',
  completed: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',
};

// Progress bar gradient based on progress percentage
const getProgressColor = (progress?: number): string => {
  if (progress === undefined) return 'bg-gray-300';
  if (progress >= 80) return 'bg-green-500';
  if (progress >= 50) return 'bg-blue-500';
  if (progress >= 25) return 'bg-yellow-500';
  return 'bg-gray-400';
};

/**
 * AgentCard displays individual agent status with:
 * - Status badge (color-coded)
 * - Current task description
 * - Progress bar (if task is running)
 */
export function AgentCard({ agent }: AgentCardProps) {
  const { agent: name, status, task, progress } = agent;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Header: Agent name + status badge */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900 truncate">{name}</h3>
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status]}`}
        >
          {status}
        </span>
      </div>

      {/* Current task */}
      {task && (
        <p className="text-sm text-gray-600 mb-3 truncate" title={task}>
          {task}
        </p>
      )}

      {/* Progress bar (shown for running tasks) */}
      {status === 'running' && progress !== undefined && (
        <div className="mt-2">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(progress)}`}
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
        </div>
      )}

      {/* Last update timestamp */}
      {!task && status === 'idle' && (
        <p className="text-xs text-gray-400 italic">No active task</p>
      )}
    </div>
  );
}

export default AgentCard;
