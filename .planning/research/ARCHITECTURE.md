# Architecture Research

**Domain:** Intelligent multi-agent knowledge management platform (LLM Wiki)
**Researched:** 2026-04-27 (Phase 03 Collaboration & Visualization update)
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
+=========================================================================+
|                          Driving Adapters                                 |
|  CLI (Typer)  |  MCP Server  |  Web UI  |  16+ Agent Compat Layer       |
+=======+============+==============+===========+==========================+
        |            |              |           |
+=======v============v==============v===========v==========================+
|                          API Gateway Layer                                 |
|    Auth | Rate Limit | Route | Context Compile | Crypto Audit             |
+====+=======+============+==========+=========+===========================+
     |       |            |          |         |
+----v--+ +--v------+ +---v-----+ +--v------+ +v-------------------------+
|Ingest | |Query    | |Govern   | |Learn    | |Collaborate [Phase 03]    |
|Engine | |Engine   | |Engine   | |Engine   | |Engine                    |
|       | |         | |+Cedar   | |+FSRS    | |+A2A/YAML/6 Agents        |
+----+--+ +--+------+ +--+------+------+ +--+--+----------+---------------+
     |       |            |             |        |             |
+====v=======v============v=============v========v=============v============+
|                      Event Bus (asyncio.Queue + SQLite)                    |
+====+=======+============+=============+========+===========================+
     |       |            |             |        |
+====v=======v============v=============v========v===========================+
|                      Write Queue (Outbox Pattern)                          |
|           Durable SQLite outbox -> parallel dispatch to sinks              |
+====+=======+============+=============v========v===========================+
     |       |            |             |        |
+----v---+ +-v--------+ +-v----------+ +-v------+v--+ +-------v------+
|Vault   | |Claims DB | |Wiki Pages | |FTS5    | |Vector| |WIP File |
|(Git)   | |(SQLite)  | |(Markdown) | |Index   | |(opt) | |(.yaml)  |
+--------+ +----------+ +-----------+ +--------+ +------+ +---------+
```

The system follows a **Hexagonal (Ports and Adapters) architecture**. Driving adapters (CLI, MCP, Web) call inward through domain protocols into the five engines. Engines write outward through a single Write Queue to multiple storage sinks. This separation means the same engine logic serves all user interfaces without duplication, and storage backends can be swapped without touching business logic.

---

## Phase 03: Collaboration & Visualization Architecture

### Overview

Phase 03 adds multi-agent orchestration and Web UI layers to the existing hexagonal architecture. The key integration principle is that **new components are either new driving adapters (Web UI) or extensions to existing engines (Collaborate Engine)** — no architectural changes to the core hexagon.

### Integration with Existing Architecture

```
                         [NEW IN PHASE 03]
+=========================================================================+
|                          Driving Adapters                                 |
|  CLI (Typer)  |  MCP Server  |  [Web UI (React)]  |  16+ Agent Compat   |
+=======+============+==============+================+======================+
        |            |              |                |
        |            |              | [NEW]          |
        |            |              v                |
        |            |     +--------+---------+      |
        |            |     |  FastAPI Server  |      |
        |            |     |  (27 endpoints)  |      |
        |            |     |  + WebSocket     |      |
        |            |     +--------+---------+      |
        |            |              |                |
        |            |              | Uses same      |
        |            |              | Engine Layer   |
        |            |              |                |
+=======v============v==============v================v======================+
|                          Engine Layer (Unchanged)                          |
|   Ingest  |  Query  |  Govern  |  Learn  |  [Collaborate (Extended)]     |
+===========================================================================+
```

**Integration Points:**

| Existing Component | Phase 03 Addition | Integration Pattern |
|--------------------|-------------------|---------------------|
| API Gateway Layer | FastAPI Web Server | New driving adapter, calls same engine protocols |
| Govern Engine | Cedar Policy Engine | Policy evaluation via protocol, Guardian agent uses |
| Write Queue | WebSocket Broadcast | New event sink for real-time UI updates |
| Event Bus | Web UI Subscription | UI subscribes to relevant events via WebSocket |
| MCP Server | Collaborate Tools | New `saw_workflow` tool wraps Collaborate Engine |

---

### Component: FastAPI Web Server (New Driving Adapter)

**Responsibility:** HTTP REST API + WebSocket server for Web UI. Third driving adapter alongside CLI and MCP.

**Integration Pattern:**

```python
# drivers/web/app.py - Application Factory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app(
    ingest: IngestPipeline,
    query: QueryEngine,
    govern: Governor,
    learn: LearnEngine,
    collaborate: CollaborateEngine,
    event_bus: EventBus,
) -> FastAPI:
    app = FastAPI(title="Smart Agent Wiki", version="1.1.0")
    
    # Inject engine dependencies via app.state
    app.state.engines = EngineContainer(
        ingest=ingest,
        query=query,
        govern=govern,
        learn=learn,
        collaborate=collaborate,
    )
    app.state.event_bus = event_bus
    
    # Register routes
    app.include_router(ingest_router, prefix="/api/ingest")
    app.include_router(query_router, prefix="/api/query")
    app.include_router(govern_router, prefix="/api/govern")
    app.include_router(learn_router, prefix="/api/learn")
    app.include_router(collaborate_router, prefix="/api/collaborate")
    app.include_router(graph_router, prefix="/api/graph")
    app.include_router(websocket_router, prefix="/ws")
    
    return app
```

**Key Design Decisions:**

1. **Same Engine Layer**: Web routes call the same engine protocols as CLI and MCP — no duplication of business logic.
2. **Dependency Injection**: Engines are injected at app creation, enabling testing with mock engines.
3. **WebSocket Support**: Real-time updates for agent progress, query results, and knowledge graph changes.

**REST Endpoints (27 total):**

| Endpoint Group | Endpoints | Engine |
|----------------|-----------|--------|
| `/api/ingest/*` | POST /document, POST /url, GET /status/{id} | Ingest |
| `/api/query/*` | POST /search, POST /query, POST /compile | Query |
| `/api/govern/*` | GET /conflicts, POST /resolve, GET /lint, GET /audit | Govern |
| `/api/learn/*` | POST /feedback, GET /status, POST /prune | Learn |
| `/api/collaborate/*` | POST /workflow, GET /agents, POST /dispatch | Collaborate |
| `/api/graph/*` | GET /nodes, GET /edges, GET /subgraph/{id} | Query (Graph) |
| `/api/wiki/*` | GET /pages, GET /page/{id}, PUT /page/{id} | Query + Write Queue |

---

### Component: WebSocket Handler (Real-Time Updates)

**Responsibility:** Push real-time events to connected Web UI clients for agent progress, query completion, and knowledge graph changes.

**Architecture:**

```
+----------------+     +------------------+     +------------------+
|  Engine Layer  | --> |   Event Bus      | --> | WebSocket Manager|
|  (publish)     |     |  (asyncio.Queue) |     | (broadcast)      |
+----------------+     +------------------+     +--------+---------+
                                                         |
                                                         v
                                                +--------+---------+
                                                |  Connected       |
                                                |  WebSocket       |
                                                |  Clients         |
                                                +------------------+
```

**Implementation:**

```python
# drivers/web/websocket.py
from fastapi import WebSocket
from typing import Dict, Set
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Keyed by session_id for targeted broadcasts
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        self.active_connections[session_id].discard(websocket)
    
    async def broadcast(self, session_id: str, event: dict):
        """Broadcast event to all connections for a session."""
        if session_id in self.active_connections:
            message = json.dumps(event)
            for connection in self.active_connections[session_id]:
                await connection.send_text(message)

# Event subscription handler
async def event_broadcaster(
    event_bus: EventBus,
    manager: ConnectionManager,
    session_id: str
):
    """Subscribe to event bus and broadcast to WebSocket clients."""
    async for event in event_bus.subscribe(session_id):
        await manager.broadcast(session_id, {
            "type": event.type,
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat()
        })
```

**Event Types for WebSocket:**

| Event Type | Trigger | UI Action |
|------------|---------|-----------|
| `AgentProgress` | Agent step completion | Update progress bar |
| `QueryCompleted` | Query finished | Display results |
| `IngestProgress` | Document processing stage | Update status |
| `ContradictionFound` | Governance detected conflict | Show alert |
| `GraphUpdated` | Entity/relation changed | Refresh graph visualization |
| `WorkflowStep` | Workflow step completed | Update workflow status |

---

### Component: Collaborate Engine (Extended)

**Responsibility:** Multi-agent orchestration with 6 role-based agents, YAML workflow parsing, A2A protocol for inter-agent communication.

**Architecture Extension:**

```
engines/collaborate/
+-- orchestrator.py        # Main CollaborateEngine orchestrator
+-- agents/                # 6 agent role implementations
|   +-- base.py            # AgentProtocol + BaseAgent
|   +-- librarian.py       # Index + classification (Haiku)
|   +-- writer.py          # Page creation + editing (Sonnet)
|   +-- critic.py          # Quality review + contradiction (Sonnet)
|   +-- linker.py          # Cross-reference discovery (Haiku)
|   +-- scholar.py         # Deep reasoning + synthesis (Opus)
|   +-- guardian.py        # Policy + security (zero-LLM rules)
+-- workflow_parser.py     # YAML workflow definition parser
+-- workflow_executor.py   # Step-by-step execution with gates [NEW]
+-- a2a_protocol.py        # A2A message passing [NEW]
+-- dispatcher.py          # Agent dispatch with model routing
+-- context_builder.py     # Build agent context from KB [NEW]
```

**Protocol Definition:**

```python
# domain/protocols.py
class AgentProtocol(Protocol):
    """Protocol for all agent implementations."""
    
    @property
    def name(self) -> str: ...
    @property
    def model_tier(self) -> Literal["haiku", "sonnet", "opus", "rule"]: ...
    
    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list[Tool],
    ) -> AgentResult: ...

class CollaborateEngine(Protocol):
    """Protocol for multi-agent orchestration."""
    
    async def dispatch_agent(
        self,
        agent_name: str,
        task: AgentTask,
        context: AgentContext,
    ) -> AgentResult: ...
    
    async def execute_workflow(
        self,
        workflow_path: Path,
        inputs: dict,
    ) -> WorkflowResult: ...
    
    async def check_policy(
        self,
        agent: str,
        action: str,
        resource: str,
    ) -> PolicyDecision: ...
```

**A2A Protocol Implementation:**

The A2A (Agent-to-Agent) protocol enables structured communication between agents. Messages are passed through the Collaborate Engine, which routes them and logs the interaction.

```python
# engines/collaborate/a2a_protocol.py
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import uuid

class MessageType(Enum):
    REQUEST = "request"      # Request action from another agent
    RESPONSE = "response"    # Response to a request
    BROADCAST = "broadcast"  # One-way notification
    QUERY = "query"          # Query for information
    RESULT = "result"        # Result of a query

@dataclass
class A2AMessage:
    """Agent-to-Agent message format."""
    message_id: str
    from_agent: str
    to_agent: str | list[str]  # Single agent or broadcast
    message_type: MessageType
    payload: dict
    correlation_id: str | None = None  # For request/response pairing
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if not self.message_id:
            self.message_id = str(uuid.uuid4())

@dataclass
class A2AResult:
    """Result of an A2A message delivery."""
    success: bool
    message_id: str
    response: A2AMessage | None = None
    error: str | None = None

# Implementation in orchestrator
class CollaborateEngineImpl:
    async def send_a2a_message(self, message: A2AMessage) -> A2AResult:
        """Route A2A message to target agent(s)."""
        # 1. Log message for audit trail
        await self._log_a2a_message(message)
        
        # 2. Route to target agent(s)
        if isinstance(message.to_agent, list):
            # Broadcast to multiple agents
            results = await asyncio.gather(*[
                self._deliver_to_agent(agent, message)
                for agent in message.to_agent
            ])
            return A2AResult(success=True, message_id=message.message_id)
        else:
            # Direct message to single agent
            return await self._deliver_to_agent(message.to_agent, message)
    
    async def _deliver_to_agent(
        self, 
        agent_name: str, 
        message: A2AMessage
    ) -> A2AResult:
        """Deliver message to specific agent."""
        agent = self._agents.get(agent_name)
        if not agent:
            return A2AResult(
                success=False, 
                message_id=message.message_id,
                error=f"Agent {agent_name} not found"
            )
        
        # Convert message to agent task
        task = AgentTask(
            type="a2a_message",
            payload=message.payload,
            correlation_id=message.correlation_id,
        )
        result = await agent.execute(task, self._build_context())
        
        return A2AResult(
            success=True,
            message_id=message.message_id,
            response=A2AMessage(
                message_id=str(uuid.uuid4()),
                from_agent=agent_name,
                to_agent=message.from_agent,
                message_type=MessageType.RESPONSE,
                payload=result.payload,
                correlation_id=message.message_id,
            )
        )
```

**YAML Workflow Executor:**

```python
# engines/collaborate/workflow_executor.py
from dataclasses import dataclass
from typing import Any, Callable
import yaml
import asyncio

@dataclass
class WorkflowStep:
    agent: str
    action: str
    input_key: str
    output_key: str
    gates: list[dict] | None = None
    condition: str | None = None

@dataclass
class WorkflowResult:
    workflow_id: str
    status: str  # "running", "completed", "failed"
    steps_completed: int
    outputs: dict[str, Any]
    errors: list[str]

class WorkflowExecutor:
    """Execute YAML-defined workflows step by step."""
    
    def __init__(
        self,
        collaborate_engine: CollaborateEngine,
        govern_engine: Governor,
    ):
        self._collaborate = collaborate_engine
        self._govern = govern_engine
    
    async def execute(
        self,
        workflow_path: Path,
        inputs: dict,
    ) -> WorkflowResult:
        """Execute a YAML workflow file."""
        with open(workflow_path) as f:
            workflow_def = yaml.safe_load(f)
        
        workflow_id = str(uuid.uuid4())
        context = dict(inputs)  # Copy inputs as starting context
        steps_completed = 0
        errors = []
        
        for step_def in workflow_def.get("steps", []):
            step = WorkflowStep(**step_def)
            
            # Check condition if present
            if step.condition and not self._eval_condition(step.condition, context):
                continue
            
            # Check gates before execution
            if step.gates:
                gate_result = await self._check_gates(step.gates, context)
                if not gate_result.passed:
                    errors.append(f"Gate failed at step {step.agent}.{step.action}: {gate_result.reason}")
                    break
            
            # Execute agent action
            try:
                result = await self._collaborate.dispatch_agent(
                    step.agent,
                    AgentTask(type=step.action, payload=context.get(step.input_key, {})),
                    self._build_agent_context(context),
                )
                
                context[step.output_key] = result.payload
                steps_completed += 1
                
                # Publish progress event
                await self._event_bus.publish(WorkflowStepEvent(
                    workflow_id=workflow_id,
                    step=f"{step.agent}.{step.action}",
                    status="completed",
                    output_key=step.output_key,
                ))
                
            except Exception as e:
                errors.append(f"Error in step {step.agent}.{step.action}: {str(e)}")
                break
        
        return WorkflowResult(
            workflow_id=workflow_id,
            status="completed" if not errors else "failed",
            steps_completed=steps_completed,
            outputs={k: v for k, v in context.items() if k not in inputs},
            errors=errors,
        )
    
    async def _check_gates(self, gates: list[dict], context: dict) -> GateResult:
        """Evaluate workflow gates using Govern Engine."""
        for gate in gates:
            # Example gate: {"confidence": ">= 3"}
            for key, condition in gate.items():
                value = context.get(key)
                if not self._eval_condition(f"{key} {condition}", context):
                    return GateResult(passed=False, reason=f"{key} failed condition")
        return GateResult(passed=True)
```

---

### Component: Policy Engine Integration (Cedar)

**Responsibility:** Evaluate agent actions against Cedar policies before execution. Guardian agent uses policy engine for zero-LLM security checks.

**Integration with Govern Engine:**

```python
# adapters/crypto/cedar_policy.py
from typing import Protocol
import subprocess
import json

class PolicyEngine(Protocol):
    """Protocol for policy evaluation engine."""
    
    def is_authorized(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> bool: ...
    
    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> PolicyDecision: ...

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str | None = None
    policy_id: str | None = None

class CedarPolicyAdapter:
    """Cedar policy engine adapter with Python binding and CLI fallback."""
    
    def __init__(self, policy_path: Path, schema_path: Path | None = None):
        self._policy_path = policy_path
        self._schema_path = schema_path
        self._use_cli = False
        
        # Try cedar-python binding first
        try:
            from cedar import PolicySet, Authorizer
            self._policy_set = PolicySet.from_file(str(policy_path))
            self._authorizer = Authorizer()
        except ImportError:
            # Fallback to CLI
            self._use_cli = True
    
    def is_authorized(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> bool:
        return self.evaluate(principal, action, resource, context).allowed
    
    def evaluate(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> PolicyDecision:
        if self._use_cli:
            return self._evaluate_cli(principal, action, resource, context)
        return self._evaluate_binding(principal, action, resource, context)
    
    def _evaluate_binding(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> PolicyDecision:
        """Use cedar-python binding."""
        from cedar import Request, Entity
        request = Request(
            principal=Entity(principal),
            action=Entity(action),
            resource=Entity(resource),
            context=context or {},
        )
        decision = self._authorizer.is_authorized(request, self._policy_set)
        return PolicyDecision(
            allowed=decision.decision == "Allow",
            reason=decision.reason,
            policy_id=decision.policy_id,
        )
    
    def _evaluate_cli(
        self,
        principal: str,
        action: str,
        resource: str,
        context: dict | None = None,
    ) -> PolicyDecision:
        """Fallback to Cedar CLI."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            json.dump({
                "principal": principal,
                "action": action,
                "resource": resource,
                "context": context or {},
            }, f)
            f.flush()
            
            result = subprocess.run(
                ["cedar", "authorize", "--policies", str(self._policy_path),
                 "--request-json", f.name] + 
                (["--schema", str(self._schema_path)] if self._schema_path else []),
                capture_output=True,
                text=True,
            )
            
            return PolicyDecision(
                allowed=result.returncode == 0,
                reason=result.stderr if result.returncode != 0 else None,
            )
```

**Cedar Policy Examples for Agent Authorization:**

```cedar
// policies/agent_policies.cedar

// Permit Librarian to perform indexing actions
@id("permit-librarian-index")
permit(
    principal == Agent::"Librarian",
    action in [Action::"saw_ingest", Action::"saw_search"],
    resource
);

// Permit Writer to create and edit wiki pages
@id("permit-writer-edit")
permit(
    principal == Agent::"Writer",
    action in [Action::"saw_query", Action::"saw_compile"],
    resource
);

// Forbid Writer from verifying claims (must be Critic or Guardian)
@id("forbid-writer-verify")
forbid(
    principal == Agent::"Writer",
    action == Action::"saw_verify",
    resource
);

// Forbid dangerous bash commands from any agent
@id("forbid-dangerous-commands")
forbid(
    principal,
    action == Action::"Bash",
    resource
)
when {
    context has parameters &&
    context.parameters.command like "*rm -rf*" ||
    context.parameters.command like "*mkfs*"
};

// Rate limit: forbid if step_count exceeds 100
@id("rate-limit")
forbid(
    principal,
    action,
    resource
)
when {
    resource has step_count &&
    resource.step_count > 100
};
```

**Integration in Guardian Agent:**

```python
# engines/collaborate/agents/guardian.py
class GuardianAgent:
    """Zero-LLM policy enforcement agent."""
    
    def __init__(self, policy_engine: PolicyEngine):
        self._policy = policy_engine
    
    @property
    def name(self) -> str:
        return "Guardian"
    
    @property
    def model_tier(self) -> Literal["rule"]:
        return "rule"
    
    async def execute(
        self,
        task: AgentTask,
        context: AgentContext,
        tools: list[Tool],
    ) -> AgentResult:
        """Execute policy check - no LLM needed."""
        action = task.payload.get("action")
        resource = task.payload.get("resource", "*")
        session_context = task.payload.get("context", {})
        
        decision = self._policy.evaluate(
            principal=f'Agent::"{context.calling_agent}"',
            action=f'Action::"{action}"',
            resource=f'Resource::"{resource}"',
            context=session_context,
        )
        
        return AgentResult(
            success=decision.allowed,
            payload={
                "allowed": decision.allowed,
                "reason": decision.reason,
                "policy_id": decision.policy_id,
            },
        )
```

---

### Component: React Frontend (Web UI)

**Responsibility:** Knowledge graph visualization, wiki page editing, search interface, dashboard.

**Architecture:**

```
web/
+-- src/
|   +-- components/
|   |   +-- ui/              # Base UI components (shadcn/ui)
|   |   +-- graph/           # Cytoscape.js graph visualization
|   |   |   +-- KnowledgeGraph.tsx
|   |   |   +-- GraphControls.tsx
|   |   |   +-- NodeDetails.tsx
|   |   +-- editor/          # Milkdown WYSIWYG editor
|   |   |   +-- WikiEditor.tsx
|   |   |   +-- ClaimReference.tsx
|   |   +-- search/          # Search interface
|   |   |   +-- SearchBar.tsx
|   |   |   +-- SearchResults.tsx
|   |   +-- dashboard/       # Main dashboard
|   |   +-- workflow/        # Workflow visualization [Phase 03]
|   +-- stores/              # Zustand state stores
|   |   +-- authStore.ts
|   |   +-- graphStore.ts
|   |   +-- searchStore.ts
|   |   +-- editorStore.ts
|   |   +-- workflowStore.ts [Phase 03]
|   +-- hooks/
|   |   +-- useWebSocket.ts
|   |   +-- useGraph.ts
|   |   +-- useSearch.ts
|   +-- lib/
|   |   +-- api.ts           # FastAPI client
|   |   +-- mcp-client.ts    # MCP client for agent integration
|   +-- pages/
|       +-- Dashboard.tsx
|       +-- Search.tsx
|       +-- Graph.tsx
|       +-- WikiPage.tsx
|       +-- Workflow.tsx [Phase 03]
```

**State Management (Zustand Slices Pattern):**

```typescript
// stores/graphStore.ts
import { create, StateCreator } from 'zustand';

interface GraphNode {
  id: string;
  label: string;
  type: 'concept' | 'entity' | 'document';
  confidence: number;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'supports' | 'contradicts' | 'relates';
}

interface GraphSlice {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: string | null;
  setNodes: (nodes: GraphNode[]) => void;
  setEdges: (edges: GraphEdge[]) => void;
  selectNode: (id: string | null) => void;
  addNode: (node: GraphNode) => void;
}

interface GraphActionsSlice {
  fetchGraph: () => Promise<void>;
  expandNode: (nodeId: string) => Promise<void>;
}

type GraphStore = GraphSlice & GraphActionsSlice;

const createGraphSlice: StateCreator<GraphStore, [], [], GraphSlice> = (set) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  selectNode: (id) => set({ selectedNode: id }),
  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),
});

const createGraphActionsSlice: StateCreator<GraphStore, [], [], GraphActionsSlice> = (set, get) => ({
  fetchGraph: async () => {
    const response = await fetch('/api/graph/nodes');
    const data = await response.json();
    set({ nodes: data.nodes, edges: data.edges });
  },
  expandNode: async (nodeId) => {
    const response = await fetch(`/api/graph/subgraph/${nodeId}`);
    const data = await response.json();
    set((state) => ({
      nodes: [...state.nodes, ...data.nodes],
      edges: [...state.edges, ...data.edges],
    }));
  },
});

export const useGraphStore = create<GraphStore>()((...a) => ({
  ...createGraphSlice(...a),
  ...createGraphActionsSlice(...a),
}));
```

**WebSocket Hook for Real-Time Updates:**

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from 'react';
import { useGraphStore } from '../stores/graphStore';
import { useWorkflowStore } from '../stores/workflowStore';

interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

export function useWebSocket(sessionId: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const addNode = useGraphStore((s) => s.addNode);
  const updateWorkflowStep = useWorkflowStore((s) => s.updateStep);

  const connect = useCallback(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
    
    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'GraphUpdated':
          addNode(message.payload.node);
          break;
        case 'WorkflowStep':
          updateWorkflowStep(message.payload);
          break;
        case 'AgentProgress':
          // Update agent progress UI
          break;
        case 'QueryCompleted':
          // Display query results
          break;
      }
    };

    ws.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

    wsRef.current = ws;
  }, [sessionId, addNode, updateWorkflowStep]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const send = useCallback((message: any) => {
    wsRef.current?.send(JSON.stringify(message));
  }, []);

  return { send };
}
```

**Cytoscape.js Graph Visualization:**

```typescript
// components/graph/KnowledgeGraph.tsx
import { useEffect, useRef } from 'react';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import { useGraphStore } from '../../stores/graphStore';

const GRAPH_STYLE = [
  {
    selector: 'node',
    style: {
      'background-color': '#666',
      'label': 'data(label)',
      'font-size': 12,
    },
  },
  {
    selector: 'node[type="concept"]',
    style: { 'background-color': '#4CAF50' },
  },
  {
    selector: 'node[type="entity"]',
    style: { 'background-color': '#2196F3' },
  },
  {
    selector: 'node[type="document"]',
    style: { 'background-color': '#9E9E9E' },
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#ccc',
      'curve-style': 'bezier',
    },
  },
  {
    selector: 'edge[type="contradicts"]',
    style: { 'line-color': '#F44336', 'line-style': 'dashed' },
  },
];

export function KnowledgeGraph() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const { nodes, edges, selectNode, expandNode } = useGraphStore();

  useEffect(() => {
    if (!containerRef.current) return;

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: { nodes, edges },
      style: GRAPH_STYLE,
      layout: { name: 'cose', animate: true },
    });

    // Click handler for node selection
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target as NodeSingular;
      selectNode(node.id());
    });

    // Double-click for expansion
    cyRef.current.on('dblclick', 'node', async (evt) => {
      const node = evt.target as NodeSingular;
      await expandNode(node.id());
    });

    return () => cyRef.current?.destroy();
  }, []);

  // Update elements when store changes
  useEffect(() => {
    if (cyRef.current) {
      cyRef.current.batch(() => {
        cyRef.current!.elements().remove();
        cyRef.current!.add({ nodes, edges });
      });
      cyRef.current.layout({ name: 'cose', animate: true }).run();
    }
  }, [nodes, edges]);

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full min-h-[600px]"
    />
  );
}
```

---

### Data Flow: Agent Workflow Execution

```
User triggers workflow via Web UI
           |
           v
+----------+-----------+
|  WorkflowExecutor    |
|  (orchestrates)      |
+----------+-----------+
           |
           v
    Parse YAML workflow
           |
           v
+----------+-----------+     +------------------+
|  For each step:      | --> | Guardian Agent   |
|  1. Check gates      |     | (Policy Engine)  |
|  2. Check policy     |     +------------------+
|  3. Dispatch agent   |
+----------+-----------+
           |
           v
+----------+-----------+
|  AgentDispatcher     |
|  (model routing)     |
+----------+-----------+
           |
     +-----+-----+
     |           |
     v           v
+----+----+ +----+----+
| Haiku   | | Sonnet  |
| (cheap) | | (mid)   |
+----+----+ +----+----+
     |           |
     +-----+-----+
           |
           v
+----------+-----------+
|  LLM (LiteLLM)       |
+----------+-----------+
           |
           v
+----------+-----------+
|  AgentResult         |
+----------+-----------+
           |
           v
+----------+-----------+
|  WriteQueue          |
|  (if KB mutation)    |
+----------+-----------+
           |
           v
+----------+-----------+
|  EventBus            |
|  -> WebSocket        |
|  -> UI update        |
+----------------------+
```

---

### Build Order (Phase 03 Specific)

Phase 03 builds on Phase 1 & 2. The following order respects dependencies:

```
Phase 03A: Multi-Agent Foundation (Weeks 16-18)
================================================
1. engines/collaborate/agents/base.py
   -- AgentProtocol definition + BaseAgent class
   -- All agents depend on this

2. adapters/crypto/cedar_policy.py
   -- PolicyEngine protocol + Cedar implementation
   -- Guardian agent depends on this

3. engines/collaborate/agents/guardian.py
   -- Zero-LLM policy enforcement
   -- Other agents checked by Guardian

4. engines/collaborate/a2a_protocol.py
   -- A2A message types + routing logic
   -- Inter-agent communication

5. engines/collaborate/workflow_executor.py
   -- YAML workflow parsing + execution
   -- Depends on agents + Guardian

6. engines/collaborate/orchestrator.py (UPDATE)
   -- Add workflow execution entry point
   -- Wire A2A protocol

   -- VERIFICATION: YAML workflow runs end-to-end

Phase 03B: Web UI Foundation (Weeks 18-19)
===========================================
7. drivers/web/app.py
   -- FastAPI application factory
   -- Depends on all engines (existing)

8. drivers/web/routes/*.py
   -- REST endpoints by engine
   -- Depend on app.py + engine protocols

9. drivers/web/websocket.py
   -- WebSocket connection manager
   -- Depends on event bus

10. drivers/web/middleware/*.py
    -- Auth, CORS, error handling
    -- Depend on app.py

   -- VERIFICATION: REST API + WebSocket work

Phase 03C: React Frontend (Weeks 19-21)
========================================
11. web/src/stores/*.ts
    -- Zustand stores with slices pattern
    -- Independent of backend

12. web/src/hooks/useWebSocket.ts
    -- WebSocket hook for real-time updates
    -- Depends on stores

13. web/src/components/graph/KnowledgeGraph.tsx
    -- Cytoscape.js visualization
    -- Depends on graphStore

14. web/src/components/editor/WikiEditor.tsx
    -- Milkdown WYSIWYG editor
    -- Depends on editorStore

15. web/src/components/search/*.tsx
    -- Search interface
    -- Depends on searchStore

16. web/src/pages/*.tsx
    -- Route pages (Dashboard, Graph, WikiPage)
    -- Depend on all components

17. drivers/web/routes/graph_router.py
    -- Graph API endpoints for Cytoscape
    -- Depends on Query engine

   -- VERIFICATION: Full Web UI functional
```

---

## Component Responsibilities (Updated)

| Component | Responsibility | Implementation | Phase |
|-----------|----------------|----------------|-------|
| **CLI (Typer)** | Primary developer interface. `init/ingest/query/lint/verify/status/prune` commands. | Typer app with Rich output. Calls engine layer directly. | 1A |
| **MCP Server (FastMCP)** | Agent integration protocol. 23 tools mapping 1:1 to engine operations. | FastMCP `@mcp.tool` decorators wrapping engine protocols. | 1B, 2B |
| **Web API (FastAPI)** | HTTP + WebSocket interface for Web UI. 27 REST endpoints, cursor pagination, RFC 7807 errors. | FastAPI with Pydantic v2, uvicorn ASGI. Shares engine layer. | **3B** |
| **WebSocket Handler** | Real-time UI updates for agent progress, query results, graph changes. | FastAPI WebSocket with ConnectionManager. Subscribes to Event Bus. | **3B** |
| **Ingest Engine** | Document intake pipeline: classify, extract, fuse, validate, enqueue writes. | 5-stage pipeline. Zero-LLM for structured, LiteLLM for unstructured. | 1A |
| **Query Engine** | Answer questions with source provenance. 5 modes + Tree Mode. | LiteLLM + FTS5 + NetworkX. Context compilation with token budget. | 1A |
| **Govern Engine** | Trust and integrity. Confidence, contradiction, freshness, Cedar policy. | Contradiction detection + Cedar policy evaluation. | 2A |
| **Learn Engine** | Self-improvement. Training period, FSRS, distillation, expiry. | FSRS library + pattern mining for SOPs. | 2B |
| **Collaborate Engine** | Multi-agent orchestration. 6 agents, A2A protocol, YAML workflows. | WorkflowExecutor + AgentDispatcher + A2A routing. | **3A** |
| **Policy Engine (Cedar)** | Evaluate agent actions against authorization policies. | cedar-python binding with CLI fallback. Guardian uses for checks. | **3A** |
| **Write Queue** | Single write entry point. Durable SQLite outbox with parallel dispatch. | Outbox pattern -> multiple sinks. Guarantees at-least-once. | 1A |
| **Event Bus** | Async inter-engine communication. Decouples engines. | asyncio.Queue + SQLite for crash recovery. | 1B |
| **React Frontend** | Knowledge graph visualization, wiki editing, search, dashboard. | React 19 + Cytoscape.js + Milkdown + Zustand. | **3C** |

---

## Integration Points Summary

### New Components Added in Phase 03

| Component | Type | Depends On | Used By |
|-----------|------|------------|---------|
| FastAPI Web Server | Driving Adapter | All engines, Event Bus | Web UI |
| WebSocket Handler | Driving Adapter | Event Bus | Web UI |
| Collaborate Engine Extensions | Engine Extension | Govern, Query, Write Queue | MCP, Web API |
| A2A Protocol | Internal Protocol | Collaborate Engine | Agents |
| Workflow Executor | Engine Component | Collaborate, Govern | MCP, Web API |
| Cedar Policy Adapter | Driven Adapter | Cedar CLI/binding | Guardian Agent |
| React Frontend | Driving Adapter | Web API, WebSocket | End User |

### Existing Components Modified

| Component | Modification | Rationale |
|-----------|--------------|-----------|
| Collaborate Engine | Add A2A, workflow executor, context builder | Phase 03 multi-agent features |
| Govern Engine | Policy engine integration point | Cedar policy evaluation for agents |
| Event Bus | WebSocket sink subscription | Real-time UI updates |
| Write Queue | WebSocket broadcast on write | Notify UI of data changes |

---

## Architectural Patterns (Phase 03 Additions)

### Pattern 5: Agent Orchestration Pattern

**What:** The Collaborate Engine orchestrates multiple agents through a dispatcher that routes tasks to the appropriate agent based on task type and model tier requirements. Guardian agent acts as a gate for all agent actions.

**When to use:** Any multi-step knowledge operation requiring different capabilities (indexing, writing, reviewing, reasoning).

**Trade-offs:**
- Pro: Clear separation of agent responsibilities
- Pro: Model cost optimization (Haiku for volume, Opus for depth)
- Pro: Policy enforcement at orchestration layer
- Con: Increased complexity over single-agent approach
- Con: A2A message routing adds latency

**Example:**
```python
# Workflow: Literature Review
async def literature_review(topic: str) -> WikiPage:
    # Step 1: Search (Librarian/Haiku)
    papers = await collaborate.dispatch_agent("Librarian", 
        AgentTask(type="search", payload={"query": topic}))
    
    # Step 2: Extract claims (Writer/Sonnet)
    claims = await collaborate.dispatch_agent("Writer",
        AgentTask(type="extract", payload={"papers": papers}))
    
    # Step 3: Review quality (Critic/Sonnet)
    reviewed = await collaborate.dispatch_agent("Critic",
        AgentTask(type="review", payload={"claims": claims}))
    
    # Step 4: Synthesize (Scholar/Opus)
    synthesis = await collaborate.dispatch_agent("Scholar",
        AgentTask(type="synthesize", payload={"claims": reviewed}))
    
    return synthesis
```

### Pattern 6: Real-Time UI Synchronization

**What:** WebSocket connection maintains real-time sync between backend events and frontend state. Event Bus publishes events; WebSocket Manager broadcasts to connected clients; Zustand stores update on message receipt.

**When to use:** Any feature requiring immediate visual feedback: agent progress, query results, graph changes.

**Trade-offs:**
- Pro: Immediate user feedback
- Pro: No polling overhead
- Pro: Natural fit for agent progress tracking
- Con: WebSocket connection management complexity
- Con: Must handle reconnection gracefully

---

## Critical Architecture Risks (Phase 03 Additions)

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Cedar Python binding immaturity (v0.1.4)** | HIGH | Architecture includes CLI fallback. Guardian agent abstracts policy engine behind Protocol. |
| **WebSocket connection scalability** | MEDIUM | ConnectionManager uses session_id for targeted broadcasts. For team mode, consider Redis pub/sub. |
| **Cytoscape.js performance with large graphs** | MEDIUM | Use `cy.batch()` for updates. Implement lazy loading via `expandNode()`. Consider WebGL renderer for >1000 nodes. |
| **A2A message ordering** | LOW | Messages include correlation_id for request/response pairing. Event Bus ensures ordering within session. |
| **Agent workflow timeout** | MEDIUM | WorkflowExecutor implements step timeout. Failed steps can be retried. State persisted in workflow context. |

---

## Sources

- Design document: `docs/smart_agent_wiki_design.md` -- Full architecture with 5 engine specifications
- FastAPI WebSocket documentation: https://fastapi.tiangolo.com/advanced/websockets/
- Cytoscape.js performance: https://github.com/cytoscape/cytoscape.js/blob/unstable/documentation/md/performance.md
- Cedar policy language: https://docs.cedarpolicy.com/
- Sondera Harness (Cedar + Agents): https://context7.com/sondera-ai/sondera-harness-python/llms.txt
- LangChain multi-agent orchestration: https://docs.langchain.com/oss/python/langgraph/workflows-agents
- Zustand slices pattern: https://github.com/pmndrs/zustand/blob/main/docs/learn/guides/slices-pattern.md

---
*Architecture research for: Smart Agent Wiki (intelligent multi-agent knowledge platform)*
*Researched: 2026-04-26 (Phase 1-2), Updated: 2026-04-27 (Phase 03)*
