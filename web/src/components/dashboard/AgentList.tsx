import { useStore } from '../../stores';
import { AgentCard } from './AgentCard';
import type { AgentStatus } from '../../types/api';

/**
 * AgentList renders a grid of AgentCards sorted by status priority:
 * 1. Running (most important)
 * 2. Error (needs attention)
 * 3. Completed
 * 4. Idle
 *
 * Pulls agent data from dashboardStore (updated via WebSocket per D-17~19).
 */
export function AgentList() {
  const agents = useStore((state) => state.agents);

  // Sort agents: running first, then error, completed, idle
  const sortedAgents = Object.values(agents).sort((a, b) => {
    const priority: Record<AgentStatus['status'], number> = {
      running: 0,
      error: 1,
      completed: 2,
      idle: 3,
    };
    return (priority[a.status] ?? 4) - (priority[b.status] ?? 4);
  });

  if (sortedAgents.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-500">No agents registered</p>
        <p className="text-sm text-gray-400 mt-1">
          Agent status will appear here when connected
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {sortedAgents.map((agent) => (
        <AgentCard key={agent.agent} agent={agent} />
      ))}
    </div>
  );
}

export default AgentList;
