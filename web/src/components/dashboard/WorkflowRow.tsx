import type { WorkflowExecution } from '../../types/api';

interface WorkflowRowProps {
  workflow: WorkflowExecution;
  isExpanded?: boolean;
  onClick?: () => void;
  steps?: { name: string; agent: string; status: string }[];
  isLoadingSteps?: boolean;
}

// Status badge colors + text labels (accessibility: not just color)
const statusBadge: Record<string, string> = {
  running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  completed: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  pending: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  interrupted: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
};

/**
 * WorkflowRow displays a single workflow execution with:
 * - Status badge (color-coded + text label)
 * - Steps progress bar (steps_completed / steps_total)
 * - Live marker (in-memory workflow, not yet persisted)
 * - Click to expand step details
 */
export function WorkflowRow({
  workflow,
  isExpanded,
  onClick,
  steps,
  isLoadingSteps,
}: WorkflowRowProps) {
  const wf = workflow;
  const isLive = wf.status === 'running' && wf.finished_at === null;
  const progressPct =
    wf.steps_total > 0
      ? Math.min(100, (wf.steps_completed / wf.steps_total) * 100)
      : 0;

  const handleClick = onClick ?? undefined;

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg border p-3 shadow-sm transition-shadow ${
        isExpanded
          ? 'border-blue-400 dark:border-blue-600'
          : 'border-gray-200 dark:border-gray-700 hover:shadow-md'
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
      data-testid={`workflow-row-${wf.workflow_id}`}
    >
      {/* Row: status badge + workflow name + steps progress + live marker */}
      <div className="flex items-center gap-3">
        {/* Status badge */}
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            statusBadge[wf.status] ?? statusBadge.pending
          }`}
        >
          {wf.status}
        </span>

        {/* Workflow name */}
        <span className="text-sm font-medium text-gray-900 dark:text-white truncate flex-1">
          {wf.definition_name || wf.workflow}
        </span>

        {/* Steps progress text */}
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {wf.steps_completed}/{wf.steps_total} steps
        </span>

        {/* Live marker */}
        {isLive && (
          <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300">
            live
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="mt-2">
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all duration-300 ${
              wf.status === 'completed'
                ? 'bg-green-500'
                : wf.status === 'failed'
                  ? 'bg-red-500'
                  : 'bg-blue-500'
            }`}
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Expanded: step details */}
      {isExpanded && (
        <div className="mt-3 border-t border-gray-100 dark:border-gray-700 pt-3">
          {isLoadingSteps && (
            <p className="text-xs text-gray-400 dark:text-gray-500">Loading steps...</p>
          )}
          {steps && steps.length > 0 && (
            <div className="space-y-1">
              {steps.map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-xs"
                  data-testid={`workflow-step-${idx}`}
                >
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      statusBadge[step.status] ?? statusBadge.pending
                    }`}
                  >
                    {step.status}
                  </span>
                  <span className="text-gray-700 dark:text-gray-300 font-medium">
                    {step.name}
                  </span>
                  <span className="text-gray-400 dark:text-gray-500">
                    {step.agent}
                  </span>
                </div>
              ))}
            </div>
          )}
          {steps && steps.length === 0 && !isLoadingSteps && (
            <p className="text-xs text-gray-400 dark:text-gray-500">No step data available</p>
          )}
        </div>
      )}

      {/* Timestamp */}
      {wf.updated_at && (
        <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">
          {new Date(wf.updated_at).toLocaleString()}
        </p>
      )}
    </div>
  );
}

export default WorkflowRow;
