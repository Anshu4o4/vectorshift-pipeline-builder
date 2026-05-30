import os
import re
import json
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for local frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class NodeData(BaseModel):
    """Represents a node in the pipeline"""
    id: str
    type: str  # customInput, customOutput, llm, text
    data: Dict[str, Any]


class Edge(BaseModel):
    """Represents a connection between nodes"""
    source: str
    sourceHandle: str
    target: str
    targetHandle: str


class PipelineRequest(BaseModel):
    """Request body for pipeline execution"""
    nodes: List[NodeData]
    edges: List[Edge]


class PipelineResponse(BaseModel):
    """Response from pipeline execution"""
    status: str
    results: Dict[str, Any]
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# Pipeline Executor
# ============================================================================

class PipelineExecutor:
    """Executes a visual pipeline with nodes and edges"""

    def __init__(self, nodes: List[NodeData], edges: List[Edge]):
        self.nodes = {node.id: node for node in nodes}
        self.edges = edges
        self.node_values = {}
        self.execution_order = []

    def build_graph(self) -> None:
        """Build execution graph and validate connections"""
        # Build adjacency list
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize all nodes
        for node_id in self.nodes:
            in_degree[node_id] = 0
        
        # Build edges
        for edge in self.edges:
            graph[edge.source].append(edge.target)
            in_degree[edge.target] += 1
        
        # Topological sort with cycle detection
        queue = deque([node_id for node_id in self.nodes if in_degree[node_id] == 0])
        visited = set()
        
        while queue:
            node_id = queue.popleft()
            self.execution_order.append(node_id)
            visited.add(node_id)
            
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles (only count visited nodes that have edges)
        nodes_with_edges = set()
        for edge in self.edges:
            nodes_with_edges.add(edge.source)
            nodes_with_edges.add(edge.target)
        
        # If any node with edges wasn't visited, there's a cycle
        if nodes_with_edges - visited:
            unvisited_with_edges = [n for n in (nodes_with_edges - visited) if n in self.nodes]
            if any(in_degree[n] > 0 for n in unvisited_with_edges):
                raise ValueError("Pipeline contains cycles")

    def validate_connections(self) -> None:
        """Validate that all connections are valid"""
        node_ids = set(self.nodes.keys())
        
        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(f"Source node '{edge.source}' does not exist")
            if edge.target not in node_ids:
                raise ValueError(f"Target node '{edge.target}' does not exist")

    def validate_pipeline(self) -> None:
        """Validate pipeline structure"""
        # Check for at least one output node
        has_output = any(node.type == "customOutput" for node in self.nodes.values())
        if not has_output:
            raise ValueError("Pipeline must have at least one output node")
        
        # Check for at least one input node
        has_input = any(node.type == "customInput" for node in self.nodes.values())
        if not has_input:
            raise ValueError("Pipeline must have at least one input node")

    def get_node_inputs(self, node_id: str) -> Dict[str, Any]:
        """Get input values for a node from connected source nodes"""
        inputs = {}
        
        for edge in self.edges:
            if edge.target == node_id:
                source_value = self.node_values.get(edge.source)
                if source_value is None:
                    raise ValueError(f"Source node '{edge.source}' produced no value")
                
                # Use the handle name as the key
                inputs[edge.targetHandle] = source_value
        
        return inputs

    def execute_node(self, node_id: str) -> Any:
        """Execute a single node and return its output"""
        node = self.nodes[node_id]
        
        if node.type == "customInput":
            return self._execute_input_node(node)
        elif node.type == "text":
            return self._execute_text_node(node)
        elif node.type == "llm":
            return self._execute_llm_node(node)
        elif node.type == "customOutput":
            return self._execute_output_node(node)
        else:
            raise ValueError(f"Unknown node type: {node.type}")

    def _execute_input_node(self, node: NodeData) -> Any:
        """Execute an input node"""
        # Input nodes return their configured value or wait for external input
        # For now, return a placeholder that would be filled by the user
        input_name = node.data.get("inputName", "input")
        input_type = node.data.get("inputType", "Text")
        return f"{{{{input:{input_name}}}}}"

    def _execute_text_node(self, node: NodeData) -> str:
        """Execute a text node with variable interpolation"""
        text_template = node.data.get("text", "")
        
        # Get input from connected nodes
        inputs = self.get_node_inputs(node.id)
        
        # Create a context dict for template interpolation
        context = {}
        for key, value in inputs.items():
            # Extract variable name from handle (e.g., "text-1-input" -> use value directly)
            context[key] = str(value)
        
        # Also add values indexed by source node ID for easier access
        for edge in self.edges:
            if edge.target == node.id:
                source_value = self.node_values.get(edge.source)
                if source_value:
                    context[edge.source] = str(source_value)
        
        # Replace {{variable}} patterns
        result = text_template
        for var_name, var_value in context.items():
            result = result.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        return result

    def _execute_llm_node(self, node: NodeData) -> str:
        """Execute an LLM node"""
        # Get input from connected nodes
        inputs = self.get_node_inputs(node.id)
        
        # Get the prompt from input
        prompt = None
        system_prompt = node.data.get("systemPrompt", "You are a helpful assistant.")
        
        # Find the prompt input
        for key, value in inputs.items():
            if "prompt" in key.lower() or not prompt:
                prompt = str(value)
                break
        
        if not prompt:
            raise ValueError("LLM node must have a prompt input")
        
        # Call OpenAI API
        response = self._call_openai_api(system_prompt, prompt)
        return response

    def _execute_output_node(self, node: NodeData) -> Any:
        """Execute an output node"""
        # Output nodes aggregate their inputs
        inputs = self.get_node_inputs(node.id)
        
        output_name = node.data.get("outputName", "output")
        
        # Return the first input value or aggregated inputs
        if inputs:
            return next(iter(inputs.values()))
        return None

    def _call_openai_api(self, system_prompt: str, user_input: str) -> str:
        """Call OpenAI API with the given prompts"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            # Return a mock response for testing
            return f"[Mock LLM Response] System: {system_prompt} | User: {user_input}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                raise ValueError("Unexpected OpenAI response format")
                
        except httpx.HTTPError as e:
            raise ValueError(f"LLM API call failed: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error calling LLM API: {str(e)}")

    def execute(self) -> Dict[str, Any]:
        """Execute the entire pipeline"""
        # Validate pipeline
        self.validate_connections()
        self.validate_pipeline()
        
        # Build execution graph
        self.build_graph()
        
        # Execute nodes in order
        outputs = {}
        for node_id in self.execution_order:
            try:
                result = self.execute_node(node_id)
                self.node_values[node_id] = result
                
                # Store outputs from output nodes
                node = self.nodes[node_id]
                if node.type == "customOutput":
                    output_name = node.data.get("outputName", node_id)
                    outputs[output_name] = result
                    
            except Exception as e:
                raise ValueError(f"Error executing node '{node_id}': {str(e)}")
        
        return outputs


# ============================================================================
# FastAPI Endpoints
# ============================================================================

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/pipelines/execute")
def execute_pipeline(request: PipelineRequest) -> PipelineResponse:
    """Execute a pipeline with given nodes and edges"""
    try:
        # Create executor
        executor = PipelineExecutor(request.nodes, request.edges)
        
        # Execute pipeline
        results = executor.execute()
        
        return PipelineResponse(
            status="success",
            results=results,
            data={"nodes": [n.dict() for n in request.nodes], "edges": [e.dict() for e in request.edges]}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")
