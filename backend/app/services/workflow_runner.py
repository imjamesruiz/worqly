import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from celery import chain, group, chord
from sqlalchemy.orm import Session

from app.schemas.workflow_models import Workflow, Node, Edge, NodeType
from app.core.tasks import execute_single_node, execute_workflow_chain, execute_parallel_nodes
from app.models.execution import WorkflowExecution, ExecutionLog, ExecutionStatus, NodeExecutionStatus
from app.services.oauth_manager import OAuthManager
from app.services.node_executor import NodeExecutor


class WorkflowRunner:
    """Compiles and executes workflows as Celery DAGs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.oauth_manager = OAuthManager(db)
        self.node_executor = NodeExecutor(db)
    
    def compile_workflow(self, workflow: Workflow, execution_id: str, test_mode: bool = False) -> Dict[str, Any]:
        """
        Compile a workflow into a Celery DAG for execution
        
        Args:
            workflow: The workflow to compile
            execution_id: Unique execution identifier
            test_mode: Whether to run in test mode
            
        Returns:
            Dictionary with execution plan and Celery task
        """
        try:
            # Validate workflow
            issues = workflow.validate_workflow()
            if issues:
                return {
                    "success": False,
                    "error_message": f"Workflow validation failed: {'; '.join(issues)}",
                    "issues": issues
                }
            
            # Build execution graph
            execution_plan = self._build_execution_plan(workflow)
            
            # Create Celery DAG
            celery_dag = self._create_celery_dag(execution_plan, workflow, execution_id, test_mode)
            
            return {
                "success": True,
                "execution_plan": execution_plan,
                "celery_dag": celery_dag,
                "execution_id": execution_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error_message": str(e)
            }
    
    def _build_execution_plan(self, workflow: Workflow) -> Dict[str, Any]:
        """Build execution plan from workflow DAG"""
        
        # Create node lookup
        nodes = {node.id: node for node in workflow.nodes}
        edges = workflow.edges
        
        # Build adjacency lists
        incoming_edges = {}
        outgoing_edges = {}
        
        for edge in edges:
            if edge.source not in outgoing_edges:
                outgoing_edges[edge.source] = []
            outgoing_edges[edge.source].append(edge)
            
            if edge.target not in incoming_edges:
                incoming_edges[edge.target] = []
            incoming_edges[edge.target].append(edge)
        
        # Find trigger nodes (no incoming edges)
        trigger_nodes = []
        for node in workflow.nodes:
            if node.type == NodeType.TRIGGER and node.id not in incoming_edges:
                trigger_nodes.append(node.id)
        
        # Build execution levels (topological sort)
        execution_levels = self._topological_sort(nodes, edges)
        
        # Create execution plan
        plan = {
            "trigger_nodes": trigger_nodes,
            "execution_levels": execution_levels,
            "total_nodes": len(workflow.nodes),
            "total_edges": len(edges)
        }
        
        return plan
    
    def _topological_sort(self, nodes: Dict[str, Node], edges: List[Edge]) -> List[List[str]]:
        """Perform topological sort to determine execution order"""
        
        # Calculate in-degrees
        in_degree = {node_id: 0 for node_id in nodes.keys()}
        for edge in edges:
            in_degree[edge.target] += 1
        
        # Find nodes with no incoming edges
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        levels = []
        
        while queue:
            current_level = []
            next_queue = []
            
            for node_id in queue:
                current_level.append(node_id)
                
                # Process outgoing edges
                for edge in edges:
                    if edge.source == node_id:
                        in_degree[edge.target] -= 1
                        if in_degree[edge.target] == 0:
                            next_queue.append(edge.target)
            
            levels.append(current_level)
            queue = next_queue
        
        return levels
    
    def _create_celery_dag(self, execution_plan: Dict[str, Any], workflow: Workflow, 
                          execution_id: str, test_mode: bool = False):
        """Create Celery DAG from execution plan"""
        
        execution_levels = execution_plan["execution_levels"]
        nodes = {node.id: node for node in workflow.nodes}
        
        if not execution_levels:
            raise ValueError("No execution levels found")
        
        # Start with trigger nodes
        trigger_level = execution_levels[0]
        
        if len(trigger_level) == 1:
            # Single trigger - create chain
            return self._create_chain_execution(trigger_level[0], execution_levels[1:], 
                                              workflow, execution_id, test_mode)
        else:
            # Multiple triggers - create parallel execution
            return self._create_parallel_execution(trigger_level, execution_levels[1:], 
                                                 workflow, execution_id, test_mode)
    
    def _create_chain_execution(self, start_node: str, remaining_levels: List[List[str]], 
                               workflow: Workflow, execution_id: str, test_mode: bool = False):
        """Create chain execution for single trigger workflow"""
        
        # Build execution sequence
        execution_sequence = [start_node]
        
        for level in remaining_levels:
            execution_sequence.extend(level)
        
        # Create Celery chain
        tasks = []
        for node_id in execution_sequence:
            task = execute_single_node.s(node_id, {}, execution_id, test_mode)
            tasks.append(task)
        
        return chain(*tasks)
    
    def _create_parallel_execution(self, trigger_nodes: List[str], remaining_levels: List[List[str]], 
                                 workflow: Workflow, execution_id: str, test_mode: bool = False):
        """Create parallel execution for multiple triggers"""
        
        # Create parallel tasks for trigger nodes
        trigger_tasks = []
        for node_id in trigger_nodes:
            task = execute_single_node.s(node_id, {}, execution_id, test_mode)
            trigger_tasks.append(task)
        
        # Create parallel group for triggers
        trigger_group = group(*trigger_tasks)
        
        # Process remaining levels sequentially
        if remaining_levels:
            # Create chain for remaining levels
            remaining_tasks = []
            for level in remaining_levels:
                if len(level) == 1:
                    remaining_tasks.append(execute_single_node.s(level[0], {}, execution_id, test_mode))
                else:
                    # Parallel execution within level
                    level_tasks = [execute_single_node.s(node_id, {}, execution_id, test_mode) 
                                 for node_id in level]
                    remaining_tasks.append(group(*level_tasks))
            
            # Chain trigger group with remaining tasks
            return chain(trigger_group, *remaining_tasks)
        else:
            return trigger_group
    
    def execute_workflow_sync(self, workflow: Workflow, trigger_data: Dict[str, Any] = None, 
                            test_mode: bool = False) -> Dict[str, Any]:
        """
        Execute workflow synchronously (for testing)
        
        Args:
            workflow: The workflow to execute
            trigger_data: Initial trigger data
            test_mode: Whether to run in test mode
            
        Returns:
            Execution result
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Create execution record
            execution = WorkflowExecution(
                workflow_id=int(workflow.id) if workflow.id.isdigit() else 0,
                execution_id=execution_id,
                status=ExecutionStatus.RUNNING,
                trigger_data=trigger_data,
                started_at=datetime.utcnow()
            )
            self.db.add(execution)
            self.db.commit()
            
            # Build execution plan
            execution_plan = self._build_execution_plan(workflow)
            execution_levels = execution_plan["execution_levels"]
            
            # Execute nodes level by level
            execution_data = trigger_data or {}
            execution_logs = []
            
            for level in execution_levels:
                level_results = []
                
                for node_id in level:
                    node = next((n for n in workflow.nodes if n.id == node_id), None)
                    if not node:
                        continue
                    
                    # Execute node
                    node_result = self._execute_node_sync(node, execution_data, execution_id, test_mode)
                    level_results.append(node_result)
                    execution_logs.append(node_result)
                    
                    # Update execution data
                    execution_data[node_id] = node_result.get("result", {})
                
                # Check for failures
                failed_nodes = [r for r in level_results if not r.get("success", False)]
                if failed_nodes:
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = f"Failed nodes: {[r['node_id'] for r in failed_nodes]}"
                    break
            
            # Update execution status
            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED
                execution.result_data = execution_data
            
            execution.completed_at = datetime.utcnow()
            execution.execution_time_ms = int((time.time() - start_time) * 1000)
            self.db.commit()
            
            return {
                "success": execution.status == ExecutionStatus.COMPLETED,
                "execution_id": execution_id,
                "result_data": execution_data,
                "logs": execution_logs,
                "execution_time_ms": execution.execution_time_ms,
                "error_message": execution.error_message
            }
            
        except Exception as e:
            if 'execution' in locals():
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                self.db.commit()
            
            return {
                "success": False,
                "execution_id": execution_id,
                "error_message": str(e),
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def _execute_node_sync(self, node: Node, input_data: Dict[str, Any], 
                          execution_id: str, test_mode: bool = False) -> Dict[str, Any]:
        """Execute a single node synchronously"""
        
        start_time = time.time()
        
        try:
            # Create execution log
            log = ExecutionLog(
                execution_id=self.db.query(WorkflowExecution).filter(
                    WorkflowExecution.execution_id == execution_id
                ).first().id,
                node_id=node.id,
                node_name=node.name,
                node_type=node.type.value,
                status=NodeExecutionStatus.RUNNING,
                input_data=input_data,
                started_at=datetime.utcnow()
            )
            self.db.add(log)
            self.db.commit()
            
            # Execute node
            if test_mode:
                result = self.node_executor.test_node(node, input_data)
            else:
                result = self.node_executor.execute_node(node, input_data)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Update log
            log.status = NodeExecutionStatus.COMPLETED
            log.output_data = result
            log.execution_time_ms = execution_time
            log.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "node_id": node.id,
                "success": True,
                "result": result,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            
            # Update log with error
            if 'log' in locals():
                log.status = NodeExecutionStatus.FAILED
                log.error_message = str(e)
                log.execution_time_ms = execution_time
                log.completed_at = datetime.utcnow()
                self.db.commit()
            
            return {
                "node_id": node.id,
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time
            }
    
    def validate_workflow_structure(self, workflow: Workflow) -> Dict[str, Any]:
        """Validate workflow structure and return detailed analysis"""
        
        issues = workflow.validate_workflow()
        
        # Additional validations
        analysis = {
            "valid": len(issues) == 0,
            "issues": issues,
            "statistics": {
                "total_nodes": len(workflow.nodes),
                "total_edges": len(workflow.edges),
                "trigger_nodes": len(workflow.get_trigger_nodes()),
                "action_nodes": len([n for n in workflow.nodes if n.type == NodeType.ACTION]),
                "condition_nodes": len([n for n in workflow.nodes if n.type == NodeType.CONDITION])
            },
            "execution_plan": None
        }
        
        if analysis["valid"]:
            try:
                execution_plan = self._build_execution_plan(workflow)
                analysis["execution_plan"] = execution_plan
            except Exception as e:
                analysis["valid"] = False
                analysis["issues"].append(f"Execution plan generation failed: {str(e)}")
        
        return analysis
