#!/usr/bin/env python3
"""Test script for the pipeline executor"""

import json
from main import PipelineExecutor, NodeData, Edge

def test_simple_pipeline():
    """Test a simple pipeline with input -> text -> output"""
    print("Testing simple pipeline...")
    
    nodes = [
        NodeData(id="input-1", type="customInput", data={"inputName": "user_input", "inputType": "Text"}),
        NodeData(id="text-1", type="text", data={"text": "Hello {{input-1}}"}),
        NodeData(id="output-1", type="customOutput", data={"outputName": "result"})
    ]
    
    edges = [
        Edge(source="input-1", sourceHandle="input-1-value", target="text-1", targetHandle="text-1-input"),
        Edge(source="text-1", sourceHandle="text-1-output", target="output-1", targetHandle="output-1-value")
    ]
    
    executor = PipelineExecutor(nodes, edges)
    results = executor.execute()
    
    print(f"✓ Simple pipeline executed successfully")
    print(f"  Results: {results}")
    assert "result" in results
    print()


def test_invalid_connections():
    """Test pipeline with invalid connections"""
    print("Testing invalid connections...")
    
    nodes = [
        NodeData(id="input-1", type="customInput", data={"inputName": "user_input"}),
        NodeData(id="output-1", type="customOutput", data={"outputName": "result"})
    ]
    
    # Invalid source node
    edges = [
        Edge(source="nonexistent", sourceHandle="value", target="output-1", targetHandle="value")
    ]
    
    executor = PipelineExecutor(nodes, edges)
    try:
        executor.execute()
        print("✗ Should have raised an error for invalid source")
    except ValueError as e:
        print(f"✓ Correctly caught invalid connection: {e}")
    print()


def test_missing_output_node():
    """Test pipeline without output node"""
    print("Testing missing output node...")
    
    nodes = [
        NodeData(id="input-1", type="customInput", data={"inputName": "user_input"}),
        NodeData(id="text-1", type="text", data={"text": "Hello"})
    ]
    
    edges = []
    
    executor = PipelineExecutor(nodes, edges)
    try:
        executor.execute()
        print("✗ Should have raised an error for missing output")
    except ValueError as e:
        print(f"✓ Correctly caught missing output node: {e}")
    print()


def test_llm_pipeline():
    """Test pipeline with LLM node"""
    print("Testing LLM pipeline...")
    
    nodes = [
        NodeData(id="input-1", type="customInput", data={"inputName": "user_query"}),
        NodeData(id="text-1", type="text", data={"text": "{{input-1}}"}),
        NodeData(id="llm-1", type="llm", data={"systemPrompt": "You are a helpful assistant"}),
        NodeData(id="output-1", type="customOutput", data={"outputName": "result"})
    ]
    
    edges = [
        Edge(source="input-1", sourceHandle="input-1-value", target="text-1", targetHandle="text-1-input"),
        Edge(source="text-1", sourceHandle="text-1-output", target="llm-1", targetHandle="llm-1-prompt"),
        Edge(source="llm-1", sourceHandle="llm-1-response", target="output-1", targetHandle="output-1-value")
    ]
    
    executor = PipelineExecutor(nodes, edges)
    results = executor.execute()
    
    print(f"✓ LLM pipeline executed successfully")
    print(f"  Results: {results}")
    assert "result" in results
    print()


def test_topological_sort():
    """Test that nodes are executed in correct order"""
    print("Testing topological sort...")
    
    nodes = [
        NodeData(id="input-1", type="customInput", data={"inputName": "data"}),
        NodeData(id="text-1", type="text", data={"text": "Process"}),
        NodeData(id="text-2", type="text", data={"text": "Final"}),
        NodeData(id="output-1", type="customOutput", data={"outputName": "result"})
    ]
    
    edges = [
        Edge(source="input-1", sourceHandle="value", target="text-1", targetHandle="input"),
        Edge(source="text-1", sourceHandle="output", target="text-2", targetHandle="input"),
        Edge(source="text-2", sourceHandle="output", target="output-1", targetHandle="value")
    ]
    
    executor = PipelineExecutor(nodes, edges)
    executor.validate_connections()
    executor.validate_pipeline()
    executor.build_graph()
    
    expected_order = ["input-1", "text-1", "text-2", "output-1"]
    assert executor.execution_order == expected_order, f"Expected {expected_order}, got {executor.execution_order}"
    print(f"✓ Correct execution order: {executor.execution_order}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Pipeline Executor Tests")
    print("=" * 60)
    print()
    
    test_simple_pipeline()
    test_invalid_connections()
    test_missing_output_node()
    test_topological_sort()
    test_llm_pipeline()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
