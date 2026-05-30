#!/usr/bin/env python3
"""Quick reference and example usage"""

import requests
import json

BASE_URL = "http://localhost:8000"

def example_health_check():
    """Example: Check server health"""
    print("Example: Health Check")
    print("-" * 50)
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def example_simple_pipeline():
    """Example: Simple text transformation pipeline"""
    print("Example: Simple Text Pipeline")
    print("-" * 50)
    
    pipeline = {
        "nodes": [
            {
                "id": "input-1",
                "type": "customInput",
                "data": {"inputName": "user_name", "inputType": "Text"}
            },
            {
                "id": "text-1",
                "type": "text",
                "data": {"text": "Hello, {{input-1}}! Welcome to our platform."}
            },
            {
                "id": "output-1",
                "type": "customOutput",
                "data": {"outputName": "greeting"}
            }
        ],
        "edges": [
            {
                "source": "input-1",
                "sourceHandle": "input-1-value",
                "target": "text-1",
                "targetHandle": "text-1-input"
            },
            {
                "source": "text-1",
                "sourceHandle": "text-1-output",
                "target": "output-1",
                "targetHandle": "output-1-value"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/pipelines/execute", json=pipeline)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def example_llm_pipeline():
    """Example: LLM-based pipeline"""
    print("Example: LLM Pipeline")
    print("-" * 50)
    
    pipeline = {
        "nodes": [
            {
                "id": "input-1",
                "type": "customInput",
                "data": {"inputName": "topic", "inputType": "Text"}
            },
            {
                "id": "text-1",
                "type": "text",
                "data": {"text": "Write a short paragraph about: {{input-1}}"}
            },
            {
                "id": "llm-1",
                "type": "llm",
                "data": {"systemPrompt": "You are a professional writer."}
            },
            {
                "id": "output-1",
                "type": "customOutput",
                "data": {"outputName": "article"}
            }
        ],
        "edges": [
            {
                "source": "input-1",
                "sourceHandle": "input-1-value",
                "target": "text-1",
                "targetHandle": "text-1-input"
            },
            {
                "source": "text-1",
                "sourceHandle": "text-1-output",
                "target": "llm-1",
                "targetHandle": "llm-1-prompt"
            },
            {
                "source": "llm-1",
                "sourceHandle": "llm-1-response",
                "target": "output-1",
                "targetHandle": "output-1-value"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/pipelines/execute", json=pipeline)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def example_multi_step_pipeline():
    """Example: Multi-step transformation pipeline"""
    print("Example: Multi-Step Pipeline")
    print("-" * 50)
    
    pipeline = {
        "nodes": [
            {
                "id": "input-1",
                "type": "customInput",
                "data": {"inputName": "raw_text"}
            },
            {
                "id": "text-1",
                "type": "text",
                "data": {"text": "Summarize: {{input-1}}"}
            },
            {
                "id": "llm-1",
                "type": "llm",
                "data": {"systemPrompt": "Be concise."}
            },
            {
                "id": "text-2",
                "type": "text",
                "data": {"text": "Summary complete: {{llm-1}}"}
            },
            {
                "id": "output-1",
                "type": "customOutput",
                "data": {"outputName": "final_summary"}
            }
        ],
        "edges": [
            {
                "source": "input-1",
                "sourceHandle": "value",
                "target": "text-1",
                "targetHandle": "input"
            },
            {
                "source": "text-1",
                "sourceHandle": "output",
                "target": "llm-1",
                "targetHandle": "prompt"
            },
            {
                "source": "llm-1",
                "sourceHandle": "response",
                "target": "text-2",
                "targetHandle": "input"
            },
            {
                "source": "text-2",
                "sourceHandle": "output",
                "target": "output-1",
                "targetHandle": "value"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/pipelines/execute", json=pipeline)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("FastAPI Pipeline Builder - Usage Examples")
    print("=" * 50)
    print()
    print("NOTE: Make sure the server is running:")
    print("  python3 -m uvicorn main:app --reload")
    print()
    
    try:
        example_health_check()
        example_simple_pipeline()
        example_llm_pipeline()
        example_multi_step_pipeline()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server at", BASE_URL)
        print("Make sure to run: python3 -m uvicorn main:app --reload")
    except Exception as e:
        print(f"ERROR: {e}")
