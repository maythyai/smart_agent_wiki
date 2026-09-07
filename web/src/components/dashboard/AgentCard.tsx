import type { AgentStatus, AgentRosterEntry } from '../../types/api';

interface AgentCardProps {
  agent: AgentStatus;
  rosterEntry?: AgentRosterEntry;
  onClick?: () => void;
  isSelected?: boolean;
}

// Status badge colors per D-17~19 design
const statusColors: Record<AgentStatus['status'], string> = {
  idle: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 animate-pulse',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
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
 * - Status badge (color-coded + text label for accessibility)
 * - Current task description + progress bar (WS live status)
 * - Activity summary (calls from REST roster)
 * - Custom marker (for custom agent roles)
 *
 * When rosterEntry is provided (REST data), shows activity_summary.calls
 * and a custom badge. When activity_summary is null, shows "—".
 */
export function AgentCard({ agent, rosterEntry, onClick, isSelected }: AgentCardProps) {
  const { agent: name, status, task, progress } = agent;
  const calls = rosterEntry?.activity_summary?.calls;
  const isCustom = rosterEntry?.custom;

  const handleClick = onClick ?? undefined;

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer ${
        isSelected
          ? 'border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800'
          : 'border-gray-200 dark:border-gray-700'
      }`}
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && handleClick) {
          e.preventDefault();
          handleClick();
        }
      }}
      data-testid={`agent-card-${name}`}
    >
      {/* Header: Agent name + status badge */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900 dark:text-white truncate">{name}</h3>
          {isCustom && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">
              custom
            </span>
          )}
        </div>
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status]}`}
        >
          {status}
        </span>
      </div>

      {/* Model tier (REST roster data) */}
      {rosterEntry && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">
          {rosterEntry.model_tier}
        </p>
      )}

      {/* Current task (WS live status) */}
      {task && (
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2 truncate" title={task}>
          {task}
        </p>
      )}

      {/* Progress bar (shown for running tasks) */}
      {status === 'running' && progress !== undefined && (
        <div className="mt-2">
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(progress)}`}
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
        </div>
      )}

      {/* Activity summary (REST roster data) */}
      {rosterEntry && (
        <div className="mt-3 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-700 pt-2">
          <span>
            Calls: <span className="font-medium text-gray-700 dark:text-gray-200">{calls ?? '—'}</span>
          </span>
          {rosterEntry.activity_summary?.last_active_at && (
            <span className="truncate">
              Last: {new Date(rosterEntry.activity_summary.last_active_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      )}

      {/* Last update timestamp */}
      {!task && status === 'idle' && (
        <p className="text-xs text-gray-400 dark:text-gray-500 italic">No active task</p>
      )}
    </div>
  );
}

export default AgentCard;
