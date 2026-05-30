# FastAPI Pipeline Executor Backend

## Overview
This is a FastAPI backend for a visual pipeline builder. It provides endpoints to execute pipelines composed of nodes (Input, Text, LLM, Output) connected by edges.

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone/navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key if using real LLM
```

## Running the Server

Start the FastAPI server:
```bash
python3 -m uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`

## API Endpoints

### 1. Health Check
**GET** `/`

Returns server status.

**Response:**
```json
{
  "status": "ok"
}
```

### 2. Execute Pipeline
**POST** `/pipelines/execute`

Executes a pipeline with the given nodes and edges.

**Request Body:**
```json
{
  "nodes": [
    {
      "id": "customInput-1",
      "type": "customInput",
      "data": {
        "inputName": "user_input",
        "inputType": "Text"
      }
    },
    {
      "id": "text-1",
      "type": "text",
      "data": {
        "text": "Process: {{customInput-1}}"
      }
    },
    {
      "id": "llm-1",
      "type": "llm",
      "data": {
        "systemPrompt": "You are a helpful assistant"
      }
    },
    {
      "id": "customOutput-1",
      "type": "customOutput",
      "data": {
        "outputName": "result"
      }
    }
  ],
  "edges": [
    {
      "source": "customInput-1",
      "sourceHandle": "customInput-1-value",
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
      "target": "customOutput-1",
      "targetHandle": "customOutput-1-value"
    }
  ]
}
```

**Response (Success):**
```json
{
  "status": "success",
  "results": {
    "result": "LLM response here"
  },
  "data": {
    "nodes": [...],
    "edges": [...]
  },
  "error": null
}
```

**Response (Error):**
```json
{
  "status": "error",
  "detail": "Pipeline must have at least one output node"
}
```

## Supported Node Types

### 1. customInput
Input node that receives external data.

**Data Fields:**
- `inputName`: Name of the input
- `inputType`: Type of input (e.g., "Text")

### 2. text
Text processing node that supports variable interpolation.

**Data Fields:**
- `text`: Template string with `{{variable}}` placeholders

**Example:**
```json
{
  "type": "text",
  "data": {
    "text": "Hello {{name}}, your age is {{age}}"
  }
}
```

### 3. llm
Language Model node that calls OpenAI API.

**Data Fields:**
- `systemPrompt`: System prompt for the LLM (optional, defaults to "You are a helpful assistant.")

### 4. customOutput
Output node that captures pipeline results.

**Data Fields:**
- `outputName`: Name for the output result

## Error Handling

The backend validates and returns meaningful error messages for:

- **Invalid connections**: Source or target nodes don't exist
- **Missing required nodes**: Pipeline must have at least one input and one output
- **Cycles**: Pipelines cannot have circular dependencies
- **LLM API failures**: Clear error messages when OpenAI API calls fail
- **Malformed requests**: Invalid JSON or missing required fields

## Testing

Run the test suites:

```bash
# Test pipeline logic
python3 test_pipeline.py

# Test FastAPI endpoints
python3 test_endpoints.py
```

## Architecture

### PipelineExecutor Class

The core executor that:
1. Validates pipeline structure
2. Builds a DAG (directed acyclic graph)
3. Performs topological sort for correct execution order
4. Executes nodes in dependency order
5. Handles inter-node communication

### Key Features

- **Topological Sort**: Ensures nodes execute in correct order
- **Lazy Evaluation**: Only computes when needed
- **Template Variables**: Supports `{{variable}}` interpolation in text nodes
- **Mock LLM**: Returns mock responses when API key is not set
- **Real LLM Integration**: Calls OpenAI API when OPENAI_API_KEY is set

## Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for LLM integration (optional)
  - If not set, LLM nodes return mock responses
  - Get one at: https://platform.openai.com/api-keys

## Example Pipelines

### Simple Text Processing
```json
{
  "nodes": [
    {"id": "input-1", "type": "customInput", "data": {"inputName": "text"}},
    {"id": "text-1", "type": "text", "data": {"text": "Processed: {{input-1}}"}},
    {"id": "output-1", "type": "customOutput", "data": {"outputName": "result"}}
  ],
  "edges": [
    {"source": "input-1", "sourceHandle": "value", "target": "text-1", "targetHandle": "input"},
    {"source": "text-1", "sourceHandle": "output", "target": "output-1", "targetHandle": "value"}
  ]
}
```

### LLM-Based Processing
```json
{
  "nodes": [
    {"id": "input-1", "type": "customInput", "data": {"inputName": "question"}},
    {"id": "llm-1", "type": "llm", "data": {"systemPrompt": "You are an expert."}},
    {"id": "output-1", "type": "customOutput", "data": {"outputName": "answer"}}
  ],
  "edges": [
    {"source": "input-1", "sourceHandle": "value", "target": "llm-1", "targetHandle": "prompt"},
    {"source": "llm-1", "sourceHandle": "response", "target": "output-1", "targetHandle": "value"}
  ]
}
```

## Development

### Code Structure

- `main.py`: FastAPI app with pipeline executor
- `test_pipeline.py`: Unit tests for pipeline logic
- `test_endpoints.py`: Integration tests for API endpoints
- `requirements.txt`: Python dependencies

### Extending the Backend

To add a new node type:

1. Add handling in `PipelineExecutor.execute_node()`
2. Implement `_execute_<node_type>_node()` method
3. Update validation in `validate_pipeline()`
4. Add tests in `test_pipeline.py`

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
Install dependencies: `pip install -r requirements.txt`

### LLM returns mock response
Set the `OPENAI_API_KEY` environment variable with a valid OpenAI API key.

### "Pipeline must have at least one output node"
Ensure your pipeline includes at least one `customOutput` node.

### "Invalid connection" errors
Verify all source and target node IDs in edges match node IDs.

## License

MIT
