#!/usr/bin/env python3
"""Test FastAPI endpoints"""

import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    print("Testing GET / (health check)...")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print(f"✓ Health check passed: {data}")
    print()


def test_execute_simple_pipeline():
    """Test pipeline execution"""
    print("Testing POST /pipelines/execute...")
    
    payload = {
        "nodes": [
            {"id": "input-1", "type": "customInput", "data": {"inputName": "user_input", "inputType": "Text"}},
            {"id": "text-1", "type": "text", "data": {"text": "Process: {{input-1}}"}},
            {"id": "output-1", "type": "customOutput", "data": {"outputName": "result"}}
        ],
        "edges": [
            {"source": "input-1", "sourceHandle": "input-1-value", "target": "text-1", "targetHandle": "text-1-input"},
            {"source": "text-1", "sourceHandle": "text-1-output", "target": "output-1", "targetHandle": "output-1-value"}
        ]
    }
    
    response = client.post("/pipelines/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data
    assert "result" in data["results"]
    print(f"✓ Pipeline execution successful")
    print(f"  Status: {data['status']}")
    print(f"  Results: {data['results']}")
    print()


def test_execute_invalid_pipeline():
    """Test pipeline execution with invalid pipeline"""
    print("Testing POST /pipelines/execute with invalid pipeline...")
    
    payload = {
        "nodes": [
            {"id": "input-1", "type": "customInput", "data": {"inputName": "user_input"}}
            # Missing output node
        ],
        "edges": []
    }
    
    response = client.post("/pipelines/execute", json=payload)
    assert response.status_code == 400
    data = response.json()
    print(f"✓ Correctly rejected invalid pipeline: {data['detail']}")
    print()


def test_execute_llm_pipeline():
    """Test LLM pipeline"""
    print("Testing POST /pipelines/execute with LLM...")
    
    payload = {
        "nodes": [
            {"id": "input-1", "type": "customInput", "data": {"inputName": "query"}},
            {"id": "text-1", "type": "text", "data": {"text": "User query: {{input-1}}"}},
            {"id": "llm-1", "type": "llm", "data": {"systemPrompt": "You are helpful"}},
            {"id": "output-1", "type": "customOutput", "data": {"outputName": "response"}}
        ],
        "edges": [
            {"source": "input-1", "sourceHandle": "value", "target": "text-1", "targetHandle": "input"},
            {"source": "text-1", "sourceHandle": "output", "target": "llm-1", "targetHandle": "prompt"},
            {"source": "llm-1", "sourceHandle": "response", "target": "output-1", "targetHandle": "value"}
        ]
    }
    
    response = client.post("/pipelines/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print(f"✓ LLM pipeline executed successfully")
    print(f"  Response: {data['results']}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("FastAPI Endpoint Tests")
    print("=" * 60)
    print()
    
    test_health_check()
    test_execute_simple_pipeline()
    test_execute_invalid_pipeline()
    test_execute_llm_pipeline()
    
    print("=" * 60)
    print("All endpoint tests passed!")
    print("=" * 60)
