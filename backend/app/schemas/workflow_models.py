from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid


class NodeType(str, Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    TRANSFORMER = "transformer"
    WEBHOOK = "webhook"
    DELAY = "delay"
    LOOP = "loop"


class ConnectionType(str, Enum):
    DATA_FLOW = "data_flow"
    CONDITIONAL = "conditional"
    ERROR_HANDLER = "error_handler"


class NodeStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


class Port(BaseModel):
    id: str
    label: str
    data_type: str = Field(..., description="Type of data: string, number, boolean, object, array")
    required: bool = False
    description: Optional[str] = None


class Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    service: str = Field(..., description="Service name (gmail, slack, etc.)")
    name: str = Field(..., min_length=1, max_length=255)
    label: str = Field(..., min_length=1, max_length=255)
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    params: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=300, ge=1, le=3600)
    enabled: bool = True
    status: NodeStatus = NodeStatus.IDLE
    inputs: List[Port] = Field(default_factory=list)
    outputs: List[Port] = Field(default_factory=list)
    
    @validator('params')
    def validate_params(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Params must be a dictionary')
        return v
    
    @validator('config')
    def validate_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Config must be a dictionary')
        return v


class Edge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_port: Optional[str] = None
    target_port: Optional[str] = None
    connection_type: ConnectionType = ConnectionType.DATA_FLOW
    condition: Optional[str] = None
    data_mapping: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    
    @validator('source', 'target')
    def validate_node_ids(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Node ID must be a non-empty string')
        return v


class WorkflowTrigger(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger_type: str = Field(..., description="Type of trigger: webhook, schedule, manual")
    config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    last_triggered: Optional[str] = None


class WorkflowExecution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    status: str = Field(..., description="Execution status")
    trigger_data: Optional[Dict[str, Any]] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_ms: Optional[int] = None


class NodeExecution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    node_id: str
    node_name: str
    node_type: str
    status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_ms: Optional[int] = None


class Workflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    owner_id: int
    is_active: bool = True
    is_template: bool = False
    version: int = 1
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    trigger: Optional[WorkflowTrigger] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @validator('nodes')
    def validate_nodes(cls, v):
        if not isinstance(v, list):
            raise ValueError('Nodes must be a list')
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in v]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError('Duplicate node IDs found')
        
        return v
    
    @validator('edges')
    def validate_edges(cls, v, values):
        if not isinstance(v, list):
            raise ValueError('Edges must be a list')
        
        # Get node IDs from the workflow
        node_ids = set()
        if 'nodes' in values:
            node_ids = {node.id for node in values['nodes']}
        
        # Validate edge references
        for edge in v:
            if edge.source not in node_ids:
                raise ValueError(f'Edge source node {edge.source} not found in workflow nodes')
            if edge.target not in node_ids:
                raise ValueError(f'Edge target node {edge.target} not found in workflow nodes')
        
        # Check for cycles (basic validation)
        if cls._has_cycles(v):
            raise ValueError('Workflow contains cycles, which are not allowed')
        
        return v
    
    @staticmethod
    def _has_cycles(edges: List[Edge]) -> bool:
        """Check if the workflow graph has cycles using DFS"""
        # Build adjacency list
        graph = {}
        for edge in edges:
            if edge.source not in graph:
                graph[edge.source] = []
            graph[edge.source].append(edge.target)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle_util(node):
                    return True
        
        return False
    
    def get_trigger_nodes(self) -> List[Node]:
        """Get all trigger nodes (nodes with no incoming edges)"""
        target_nodes = {edge.target for edge in self.edges}
        return [node for node in self.nodes if node.id not in target_nodes and node.type == NodeType.TRIGGER]
    
    def get_node_dependencies(self, node_id: str) -> List[str]:
        """Get list of nodes that must be executed before the given node"""
        return [edge.source for edge in self.edges if edge.target == node_id]
    
    def get_downstream_nodes(self, node_id: str) -> List[str]:
        """Get list of nodes that depend on the given node"""
        return [edge.target for edge in self.edges if edge.source == node_id]
    
    def validate_workflow(self) -> List[str]:
        """Validate the workflow and return list of issues"""
        issues = []
        
        # Check for trigger nodes
        trigger_nodes = self.get_trigger_nodes()
        if not trigger_nodes:
            issues.append("Workflow must have at least one trigger node")
        
        # Check for orphaned nodes
        all_node_ids = {node.id for node in self.nodes}
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        orphaned_nodes = all_node_ids - connected_nodes
        if orphaned_nodes and len(connected_nodes) > 0:
            issues.append(f"Orphaned nodes found: {', '.join(orphaned_nodes)}")
        
        # Check for nodes with no outputs (except triggers)
        for node in self.nodes:
            if node.type != NodeType.TRIGGER:
                has_outputs = any(edge.source == node.id for edge in self.edges)
                if not has_outputs:
                    issues.append(f"Node '{node.name}' has no outgoing connections")
        
        return issues


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    trigger: Optional[WorkflowTrigger] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    nodes: Optional[List[Node]] = None
    edges: Optional[List[Edge]] = None
    trigger: Optional[WorkflowTrigger] = None
    settings: Optional[Dict[str, Any]] = None


class WorkflowExecutionRequest(BaseModel):
    trigger_data: Optional[Dict[str, Any]] = None
    test_mode: bool = False
    execution_id: Optional[str] = None


class WorkflowTestRequest(BaseModel):
    trigger_data: Optional[Dict[str, Any]] = None
    node_id: Optional[str] = None  # Test specific node


class WorkflowExecutionResponse(BaseModel):
    execution_id: str
    status: str
    success: bool
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    logs: List[NodeExecution] = Field(default_factory=list)
    execution_time_ms: Optional[int] = None


class WorkflowBulkUpdate(BaseModel):
    """For bulk updates of workflow structure"""
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    trigger: Optional[WorkflowTrigger] = None
    settings: Optional[Dict[str, Any]] = None
