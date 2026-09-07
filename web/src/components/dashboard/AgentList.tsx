import { useStore } from '../../stores';
import { AgentCard } from './AgentCard';
import type { AgentStatus, AgentRosterEntry } from '../../types/api';

interface AgentListProps {
  /** REST roster data from useAgents() hook */
  roster?: AgentRosterEntry[];
  /** Callback when an agent card is clicked */
  onSelectAgent?: (name: string | null) => void;
  /** Currently selected agent name */
  selectedAgent?: string | null;
}

/**
 * AgentList renders a grid of AgentCards sorted by status priority:
 * 1. Running (most important)
 * 2. Error (needs attention)
 * 3. Completed
 * 4. Idle
 *
 * When `roster` is provided (REST data), merges REST roster entries with
 * WS live status from dashboardStore. WS live status overrides the REST
 * status for real-time updates.
 *
 * When `roster` is not provided (backward compat), falls back to WS-only
 * agents from dashboardStore.
 */
export function AgentList({ roster, onSelectAgent, selectedAgent }: AgentListProps) {
  const wsAgents = useStore((state) => state.agents);

  // Build merged list: REST roster as base, overlay WS live status
  type MergedItem = { agent: AgentStatus; rosterEntry?: AgentRosterEntry };

  let items: MergedItem[];

  if (roster && roster.length > 0) {
    // REST roster as base, overlay WS live status
    items = roster.map((entry) => {
      const ws = wsAgents[entry.name];
      return {
        agent: {
          agent: entry.name,
          status: ws?.status ?? 'idle',
          task: ws?.task,
          progress: ws?.progress,
        },
        rosterEntry: entry,
      };
    });
    // Also include WS agents not in roster (transient/running)
    for (const [name, ws] of Object.entries(wsAgents)) {
      if (!roster.some((r) => r.name === name)) {
        items.push({ agent: ws });
      }
    }
  } else {
    // WS-only fallback (backward compat)
    items = Object.values(wsAgents).map((agent) => ({ agent }));
  }

  // Sort agents: running first, then error, completed, idle
  const sortedAgents = items.sort((a, b) => {
    const priority: Record<string, number> = {
      running: 0,
      error: 1,
      completed: 2,
      idle: 3,
    };
    return (priority[a.agent.status] ?? 4) - (priority[b.agent.status] ?? 4);
  });

  if (sortedAgents.length === 0) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">No agents registered</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
          Agent status will appear here when connected
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {sortedAgents.map(({ agent, rosterEntry }) => (
        <AgentCard
          key={agent.agent}
          agent={agent}
          rosterEntry={rosterEntry}
          onClick={onSelectAgent ? () => onSelectAgent(agent.agent) : undefined}
          isSelected={selectedAgent === agent.agent}
        />
      ))}
    </div>
  );
}

export default AgentList;
