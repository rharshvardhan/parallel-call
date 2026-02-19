"""
Factory Service - Build Starter Kit Generation
===============================================
Converts approved Blueprints into RUNNABLE "Build Starter Kits"
that help engineers start building fast.

Features:
- Fully runnable scaffold with /health and /demo-run endpoints
- Real model selections from blueprint (no TBD placeholders)
- Pattern-specific (RAG/Agentic/Hybrid/Automation) templates
- ZIP packaging for download
- GitHub push helper commands
"""

import os
import io
import uuid
import json
import zipfile
from datetime import datetime
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


# =============================================================================
# MODEL RECOMMENDATIONS (Marketplace Integration)
# =============================================================================

MODEL_RECOMMENDATIONS = {
    "RAG": {
        "primary_llm": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "rationale": "Best for nuanced understanding and context-aware responses"
        },
        "embedding": {
            "provider": "openai",
            "model": "text-embedding-3-large",
            "dimensions": 3072,
            "rationale": "High-quality semantic embeddings for retrieval"
        },
        "reranker": {
            "provider": "cohere",
            "model": "rerank-english-v3.0",
            "rationale": "Improves retrieval precision"
        },
        "vector_db": "chromadb",
    },
    "Agentic": {
        "primary_llm": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "rationale": "Strong reasoning and tool-use capabilities"
        },
        "tool_calling_llm": {
            "provider": "openai",
            "model": "gpt-4o",
            "rationale": "Reliable function calling for tool orchestration"
        },
        "fast_llm": {
            "provider": "anthropic",
            "model": "claude-3-5-haiku-20241022",
            "rationale": "Quick responses for simple agent tasks"
        },
    },
    "Hybrid": {
        "primary_llm": {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "rationale": "Versatile for both RAG and agentic tasks"
        },
        "embedding": {
            "provider": "openai",
            "model": "text-embedding-3-large",
            "dimensions": 3072,
            "rationale": "High-quality semantic embeddings"
        },
        "classifier_llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "rationale": "Fast classification for routing"
        },
    },
    "Automation": {
        "primary_llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "rationale": "Cost-effective for structured tasks"
        },
        "extraction_llm": {
            "provider": "anthropic",
            "model": "claude-3-5-haiku-20241022",
            "rationale": "Fast and accurate for data extraction"
        },
    },
}


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class FactoryStatus(BaseModel):
    """Factory status for a blueprint"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    blueprint_id: str
    blueprint_name: str
    status: str = "Not Started"
    kit_generated_at: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    readiness_checklist: Dict[str, bool] = Field(default_factory=lambda: {
        "data_access_confirmed": False,
        "core_flow_runnable": False,
        "security_baseline_captured": False,
        "observability_plan_noted": False,
    })


class KitMetadata(BaseModel):
    """Metadata for a generated starter kit"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    blueprint_id: str
    blueprint_name: str
    pattern: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    files: List[str] = []
    version: str = "1.0"
    llm_enhanced: bool = True


class GenerateKitRequest(BaseModel):
    blueprint: Dict[str, Any]
    use_llm_enhancement: bool = True


class RegenerateModuleRequest(BaseModel):
    blueprint: Dict[str, Any]
    module: str
    use_llm_enhancement: bool = True


class AddEndpointRequest(BaseModel):
    blueprint: Dict[str, Any]
    endpoint_name: str
    method: str = "POST"
    description: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _extract_model_from_blueprint(blueprint: Dict) -> Dict[str, Any]:
    """Extract selected model information from blueprint"""
    ai_design = blueprint.get("aiDesign", {})
    pattern = ai_design.get("selectedPattern", "Automation")
    
    # Check if blueprint has explicit model selection
    model_selection = ai_design.get("modelSelection", {})
    if model_selection.get("model"):
        return {
            "provider": model_selection.get("provider", "anthropic"),
            "model": model_selection.get("model"),
            "rationale": model_selection.get("rationale", "Selected via Blueprint")
        }
    
    # Fall back to pattern defaults
    return MODEL_RECOMMENDATIONS.get(pattern, MODEL_RECOMMENDATIONS["Automation"]).get("primary_llm", {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "rationale": "Default selection for pattern"
    })


def _get_model_config(pattern: str) -> Dict[str, Any]:
    """Get model configuration for a pattern"""
    return MODEL_RECOMMENDATIONS.get(pattern, MODEL_RECOMMENDATIONS["Automation"])


def _safe_name(name: str) -> str:
    """Convert name to safe filename/variable name"""
    return name.replace(" ", "_").replace("-", "_").replace("/", "_")[:50]


# =============================================================================
# README GENERATOR
# =============================================================================

def _generate_readme(blueprint: Dict) -> str:
    """Generate README.md with exact working commands"""
    cover = blueprint.get("cover", {})
    exec_summary = blueprint.get("executiveSummary", {})
    ai_design = blueprint.get("aiDesign", {})
    scope = blueprint.get("scopeLock", {})
    pattern = ai_design.get("selectedPattern", "Automation")
    primary_model = _extract_model_from_blueprint(blueprint)
    use_case_name = cover.get("useCaseName", "AI Use Case")
    
    # Determine which API keys are needed based on pattern and model
    api_keys_needed = []
    if primary_model.get("provider") == "anthropic":
        api_keys_needed.append("ANTHROPIC_API_KEY")
    if primary_model.get("provider") == "openai" or pattern in ["RAG", "Hybrid", "Agentic"]:
        api_keys_needed.append("OPENAI_API_KEY or Azure OpenAI credentials")
    
    api_keys_section = "\n".join([f"# {key}=your-key-here" for key in api_keys_needed])
    
    readme = f"""# {use_case_name}

> **Pattern**: {pattern} | **Model**: {primary_model.get('provider', 'anthropic')}/{primary_model.get('model', 'claude-sonnet-4-20250514')}

## Quick Start

```bash
# 1. Setup environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your API keys:
{api_keys_section}

# 3. Run the server
uvicorn main:app --reload --port 8001
```

## Test the API

### Health Check
```bash
curl http://localhost:8001/api/health
```
Expected response:
```json
{{"status": "healthy", "version": "1.0.0", "pattern": "{pattern}"}}
```

### Demo Flow
```bash
curl -X POST http://localhost:8001/api/demo-run \\
  -H "Content-Type: application/json" \\
  -d '{{"input": "Hello, test the {pattern} flow"}}'
```
Expected response:
```json
{{"id": "...", "result": {{"answer": "..."}}, "pattern": "{pattern}", "model": "{primary_model.get('model', 'claude-sonnet-4-20250514')}"}}
```

### Process Input (Main Endpoint)
```bash
curl -X POST http://localhost:8001/api/process \\
  -H "Content-Type: application/json" \\
  -d '{{"input": "Your query here", "context": {{"user_id": "test-user"}}}}'
```

## Overview

| Attribute | Value |
|-----------|-------|
| **Domain** | {cover.get('businessDomain', 'Enterprise')} |
| **Pattern** | {pattern} |
| **Primary Model** | `{primary_model.get('model', 'claude-sonnet-4-20250514')}` |
| **Provider** | {primary_model.get('provider', 'anthropic')} |

## Problem Statement

{exec_summary.get('problemStatement', 'See blueprint.md for details.')}

## Solution

{exec_summary.get('proposedSolution', 'See blueprint.md for details.')}

## In-Scope Capabilities

{chr(10).join(['- ' + cap for cap in scope.get('inScopeCapabilities', ['See blueprint.md'])])}

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI application (START HERE)
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment template
├── orchestrator/
│   └── flow.py              # AI flow implementation
├── config/
│   └── llm_config.py        # Model configuration
├── prompts/
│   └── system_prompt.txt    # System prompt
├── contracts/
│   └── openapi.yaml         # API specification
└── blueprint.md             # Original blueprint
```

## Where to Modify

1. **Add business logic**: `orchestrator/flow.py` - Customize the `process_request()` function
2. **Change model**: `config/llm_config.py` - Update model settings
3. **Modify prompts**: `prompts/system_prompt.txt` - Adjust system behavior
4. **Add endpoints**: `backend/main.py` - Add new FastAPI routes

## Push to GitHub

```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit: {use_case_name} starter kit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---
*Generated by Infinite AI Studio Factory*
"""
    return readme


# =============================================================================
# ENV EXAMPLE GENERATOR
# =============================================================================

def _generate_env_example(blueprint: Dict) -> str:
    """Generate .env.example that matches code requirements"""
    ai_design = blueprint.get("aiDesign", {})
    pattern = ai_design.get("selectedPattern", "Automation")
    primary_model = _extract_model_from_blueprint(blueprint)
    
    env_lines = [
        "# =============================================================================",
        "# Environment Configuration",
        "# Copy this file to .env and fill in your API keys",
        "# =============================================================================",
        "",
        "# Server Configuration",
        "PORT=8001",
        "DEBUG=true",
        "",
        "# Primary LLM Configuration",
        f"PRIMARY_LLM_PROVIDER={primary_model.get('provider', 'anthropic')}",
        f"PRIMARY_LLM_MODEL={primary_model.get('model', 'claude-sonnet-4-20250514')}",
        "",
    ]
    
    # Add API keys based on pattern and model
    if primary_model.get("provider") == "anthropic" or pattern in ["RAG", "Agentic", "Hybrid"]:
        env_lines.extend([
            "# Anthropic API Key (get from: https://console.anthropic.com/)",
            "ANTHROPIC_API_KEY=",
            "",
        ])
    
    if primary_model.get("provider") == "openai" or pattern in ["RAG", "Agentic", "Hybrid"]:
        env_lines.extend([
            "# OpenAI API Key (get from: https://platform.openai.com/api-keys)",
            "OPENAI_API_KEY=",
            "",
            "# OR use Azure OpenAI (configure all 4 settings below)",
            "# AZURE_OPENAI_API_KEY=",
            "# AZURE_OPENAI_ENDPOINT=",
            "# AZURE_OPENAI_DEPLOYMENT_NAME=",
            "# AZURE_OPENAI_API_VERSION=2024-12-01-preview",
            "",
        ])
    
    # Pattern-specific configs
    if pattern in ["RAG", "Hybrid"]:
        env_lines.extend([
            "# Vector Database Configuration",
            "VECTOR_DB=chromadb",
            "CHROMA_PERSIST_DIR=./data/chroma",
            "",
        ])
    
    env_lines.extend([
        "# Optional: Logging",
        "LOG_LEVEL=INFO",
    ])
    
    return "\n".join(env_lines)


# =============================================================================
# BACKEND MAIN.PY GENERATOR
# =============================================================================

def _generate_backend_main(blueprint: Dict, pattern: str) -> str:
    """Generate main.py with working /health and /demo-run endpoints"""
    cover = blueprint.get("cover", {})
    primary_model = _extract_model_from_blueprint(blueprint)
    use_case_name = cover.get("useCaseName", "AI Service")
    
    return f'''"""
{use_case_name} - Backend API
{'=' * 50}
Pattern: {pattern}
Primary Model: {primary_model.get('provider', 'anthropic')}/{primary_model.get('model', 'claude-sonnet-4-20250514')}

Quick Start:
    uvicorn main:app --reload --port 8001
    
Test:
    curl http://localhost:8001/api/health
    curl -X POST http://localhost:8001/api/demo-run -H "Content-Type: application/json" -d '{{"input": "test"}}'
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import uuid
import os
import logging

from dotenv import load_dotenv

# Import orchestrator
from orchestrator.flow import process_request, initialize_services

load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
PRIMARY_LLM_PROVIDER = os.environ.get("PRIMARY_LLM_PROVIDER", "{primary_model.get('provider', 'anthropic')}")
PRIMARY_LLM_MODEL = os.environ.get("PRIMARY_LLM_MODEL", "{primary_model.get('model', 'claude-sonnet-4-20250514')}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting {use_case_name}...")
    logger.info(f"Pattern: {pattern}")
    logger.info(f"Model: {{PRIMARY_LLM_PROVIDER}}/{{PRIMARY_LLM_MODEL}}")
    await initialize_services()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="{use_case_name}",
    description="{pattern} Pattern - Generated by AI Studio Factory",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ProcessRequest(BaseModel):
    """Main processing request"""
    input: str = Field(..., min_length=1, max_length=100000, description="Input text to process")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Processing options")


class ProcessResponse(BaseModel):
    """Main processing response"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    result: Dict[str, Any]
    confidence: float = 0.0
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "1.0.0"
    pattern: str = "{pattern}"
    model: str = PRIMARY_LLM_MODEL
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DemoRequest(BaseModel):
    """Demo request"""
    input: str = Field(default="Hello, this is a test", description="Test input")


class DemoResponse(BaseModel):
    """Demo response"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    result: Dict[str, Any]
    pattern: str = "{pattern}"
    model: str = PRIMARY_LLM_MODEL


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and configuration.
    """
    return HealthResponse()


@app.post("/api/demo-run", response_model=DemoResponse)
async def demo_run(request: DemoRequest):
    """
    Demo endpoint to test the flow.
    
    This is a simplified endpoint to verify the setup works.
    """
    logger.info(f"Demo run with input: {{request.input[:50]}}...")
    
    try:
        # Call the orchestrator with demo settings
        result = await process_request(
            input_data=request.input,
            context={{"demo": True}},
            options={{"max_tokens": 500}},
        )
        
        return DemoResponse(
            result=result.get("result", {{"answer": "Demo completed successfully"}}),
        )
    except Exception as e:
        logger.warning(f"Demo flow error (expected if API keys not set): {{e}}")
        # Return mock response if services not configured
        return DemoResponse(
            result={{
                "answer": f"Demo mode: Received input '{{request.input[:100]}}'. Configure API keys in .env for full functionality.",
                "status": "demo_mode"
            }},
        )


@app.post("/api/process", response_model=ProcessResponse)
async def process_input(request: ProcessRequest):
    """
    Main processing endpoint.
    
    Processes input through the {pattern} pipeline.
    
    - **input**: The text/data to process
    - **context**: Optional context (user_id, session_id, etc.)
    - **options**: Processing options (verbose, stream, etc.)
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Processing request: {{request.input[:50]}}...")
    
    try:
        # Call orchestrator
        result = await process_request(
            input_data=request.input,
            context=request.context or {{}},
            options=request.options or {{}},
        )
        
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return ProcessResponse(
            result=result.get("result", {{}}),
            confidence=result.get("confidence", 0.0),
            sources=result.get("sources"),
            metadata={{
                "processing_time_ms": int(processing_time),
                "model_used": PRIMARY_LLM_MODEL,
                "pattern": "{pattern}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }}
        )
    except Exception as e:
        logger.exception("Processing failed")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
'''


# =============================================================================
# REQUIREMENTS.TXT GENERATOR
# =============================================================================

def _generate_backend_requirements(pattern: str) -> str:
    """Generate requirements.txt for backend"""
    base = """# Core Framework
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
pydantic>=2.0.0
python-dotenv>=1.0.0
httpx>=0.24.0
python-multipart>=0.0.6

# Async Support
aiohttp>=3.9.0

# Logging
structlog>=23.0.0

"""
    
    if pattern in ["RAG", "Hybrid"]:
        base += """# LLM Providers
openai>=1.0.0
anthropic>=0.18.0

# RAG / Embeddings
chromadb>=0.4.0

# Document Processing
pypdf>=3.0.0

"""
    elif pattern == "Agentic":
        base += """# LLM Providers
openai>=1.0.0
anthropic>=0.18.0

"""
    else:
        base += """# LLM Providers
openai>=1.0.0
anthropic>=0.18.0

"""
    
    base += """# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
"""
    return base


# =============================================================================
# LLM CONFIG GENERATOR
# =============================================================================

def _generate_llm_config(blueprint: Dict, pattern: str) -> str:
    """Generate config/llm_config.py with actual model selections"""
    primary_model = _extract_model_from_blueprint(blueprint)
    models = _get_model_config(pattern)
    
    code = f'''"""
LLM Configuration
=================
Model configuration for {pattern} pattern.
Primary Model: {primary_model.get('provider', 'anthropic')}/{primary_model.get('model', 'claude-sonnet-4-20250514')}
"""

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str
    model: str
    api_key_env: str
    temperature: float = 0.7
    max_tokens: int = 4096


# Primary LLM (from blueprint selection)
PRIMARY_LLM = LLMConfig(
    provider="{primary_model.get('provider', 'anthropic')}",
    model="{primary_model.get('model', 'claude-sonnet-4-20250514')}",
    api_key_env="{primary_model.get('provider', 'anthropic').upper()}_API_KEY",
)

'''
    
    # Add additional model configs for the pattern
    for purpose, config in models.items():
        if isinstance(config, dict) and "model" in config and purpose != "primary_llm":
            var_name = purpose.upper()
            api_key_env = f"{config['provider'].upper()}_API_KEY"
            code += f'''{var_name} = LLMConfig(
    provider="{config['provider']}",
    model="{config['model']}",
    api_key_env="{api_key_env}",
)

'''
    
    code += '''
def get_api_key(config: LLMConfig) -> str:
    """Get API key from environment"""
    key = os.environ.get(config.api_key_env)
    if not key:
        raise ValueError(f"Missing API key: {config.api_key_env}")
    return key


def validate_config() -> bool:
    """Validate primary API key is present"""
    key = os.environ.get(PRIMARY_LLM.api_key_env)
    return bool(key)
'''
    return code


# =============================================================================
# ORCHESTRATOR FLOW GENERATORS
# =============================================================================

def _generate_orchestrator_flow(blueprint: Dict, pattern: str) -> str:
    """Generate orchestrator/flow.py based on pattern"""
    primary_model = _extract_model_from_blueprint(blueprint)
    provider = primary_model.get('provider', 'anthropic')
    model = primary_model.get('model', 'claude-sonnet-4-20250514')
    
    if pattern == "RAG":
        return _generate_rag_flow(provider, model)
    elif pattern == "Agentic":
        return _generate_agentic_flow(provider, model)
    elif pattern == "Hybrid":
        return _generate_hybrid_flow(provider, model)
    else:
        return _generate_automation_flow(provider, model)


def _generate_automation_flow(provider: str, model: str) -> str:
    """Generate simple automation flow"""
    return f'''"""
Automation Flow
===============
Simple LLM-powered automation.
Model: {provider}/{model}
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# LLM Client
llm_client = None

# Configuration
LLM_PROVIDER = "{provider}"
LLM_MODEL = "{model}"


async def initialize_services():
    """Initialize LLM client"""
    global llm_client
    
    # Check for AnthropicFoundry configuration
    api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
    endpoint = os.environ.get("ANTHROPIC_FOUNDRY_ENDPOINT")
    
    if api_key and endpoint:
        from anthropic import Anthropic
        llm_client = Anthropic(
            api_key=api_key,
            base_url=endpoint
        )
        logger.info(f"Anthropic client initialized with endpoint {{endpoint}}")
    else:
        logger.warning("Anthropic credentials not set - running in demo mode")


async def process_request(
    input_data: str,
    context: Dict[str, Any],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process input through the automation flow.
    
    Args:
        input_data: The input text to process
        context: Context information (user_id, etc.)
        options: Processing options
    
    Returns:
        Result dictionary with answer and metadata
    """
    # Load system prompt
    system_prompt = "You are a helpful AI assistant. Provide clear, accurate responses."
    try:
        with open("prompts/system_prompt.txt", "r") as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        pass
    
    # If no client, return demo response
    if llm_client is None:
        logger.info("Running in demo mode (no API key configured)")
        return {{
            "result": {{
                "answer": f"Demo mode: Received '{{input_data[:100]}}'. Set API keys in .env for full functionality.",
                "model": LLM_MODEL,
                "status": "demo"
            }},
            "confidence": 0.5,
        }}
    
    try:
        if LLM_PROVIDER == "anthropic":
            response = await llm_client.messages.create(
                model=LLM_MODEL,
                max_tokens=options.get("max_tokens", 4096),
                system=system_prompt,
                messages=[{{"role": "user", "content": input_data}}],
            )
            answer = response.content[0].text
            usage = {{
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }}
        else:
            response = await llm_client.chat.completions.create(
                model=LLM_MODEL,
                max_tokens=options.get("max_tokens", 4096),
                messages=[
                    {{"role": "system", "content": system_prompt}},
                    {{"role": "user", "content": input_data}},
                ],
            )
            answer = response.choices[0].message.content
            usage = {{
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }}
        
        return {{
            "result": {{
                "answer": answer,
                "model": LLM_MODEL,
            }},
            "confidence": 0.85,
            "usage": usage,
        }}
        
    except Exception as e:
        logger.exception("LLM call failed")
        raise
'''


def _generate_rag_flow(provider: str, model: str) -> str:
    """Generate RAG flow"""
    return f'''"""
RAG Flow
========
Retrieval-Augmented Generation pipeline.
Model: {provider}/{model}
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Clients
llm_client = None
embedding_client = None
vector_store = None

# Configuration
LLM_PROVIDER = "{provider}"
LLM_MODEL = "{model}"
EMBEDDING_MODEL = "text-embedding-3-large"


@dataclass
class RetrievalResult:
    content: str
    score: float
    metadata: Dict[str, Any]


async def initialize_services():
    """Initialize LLM, embedding, and vector store"""
    global llm_client, embedding_client, vector_store
    
    # Initialize LLM with AnthropicFoundry
    api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
    endpoint = os.environ.get("ANTHROPIC_FOUNDRY_ENDPOINT")
    
    if api_key and endpoint:
        from anthropic import Anthropic
        llm_client = Anthropic(
            api_key=api_key,
            base_url=endpoint
        )
        logger.info("Anthropic client initialized")
    
    # For embeddings, we'll use a simple mock since we removed OpenAI
    embedding_client = None  # Disable embeddings for now
    logger.info("Embedding client disabled (OpenAI removed)")
    
    # Initialize ChromaDB
    try:
        import chromadb
        from chromadb.config import Settings
        chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
        vector_store = chroma_client.get_or_create_collection(name="documents")
        logger.info("ChromaDB initialized")
    except ImportError:
        logger.warning("ChromaDB not installed - RAG retrieval disabled")


async def get_embedding(text: str) -> List[float]:
    """Get embedding for text"""
    if not embedding_client:
        return []
    
    response = await embedding_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


async def retrieve_context(query: str, top_k: int = 5) -> List[RetrievalResult]:
    """Retrieve relevant documents"""
    if not vector_store or not embedding_client:
        return []
    
    query_embedding = await get_embedding(query)
    results = vector_store.query(query_embeddings=[query_embedding], n_results=top_k)
    
    retrieved = []
    if results and results.get("documents"):
        for i, doc in enumerate(results["documents"][0]):
            retrieved.append(RetrievalResult(
                content=doc,
                score=1 - results["distances"][0][i] if results.get("distances") else 0.0,
                metadata=results["metadatas"][0][i] if results.get("metadatas") else {{}},
            ))
    
    return retrieved


async def process_request(
    input_data: str,
    context: Dict[str, Any],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    """Main RAG processing flow"""
    
    # Load system prompt
    system_prompt = "You are a helpful AI assistant. Answer based on the provided context."
    try:
        with open("prompts/system_prompt.txt", "r") as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        pass
    
    # Demo mode if no client
    if llm_client is None:
        return {{
            "result": {{"answer": f"Demo: RAG query '{{input_data[:100]}}'. Set API keys for full functionality.", "status": "demo"}},
            "confidence": 0.5,
            "sources": [],
        }}
    
    try:
        # Retrieve context
        retrieved = await retrieve_context(input_data, top_k=5)
        logger.info(f"Retrieved {{len(retrieved)}} documents")
        
        # Build context
        context_text = "\\n\\n".join([f"[Source {{i+1}}]\\n{{r.content}}" for i, r in enumerate(retrieved)])
        
        user_message = f"""Context:\\n{{context_text}}\\n\\nQuestion: {{input_data}}""" if retrieved else input_data
        
        # Generate response
        if LLM_PROVIDER == "anthropic":
            response = await llm_client.messages.create(
                model=LLM_MODEL,
                max_tokens=options.get("max_tokens", 4096),
                system=system_prompt,
                messages=[{{"role": "user", "content": user_message}}],
            )
            answer = response.content[0].text
        else:
            response = await llm_client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{{"role": "system", "content": system_prompt}}, {{"role": "user", "content": user_message}}],
            )
            answer = response.choices[0].message.content
        
        return {{
            "result": {{"answer": answer, "model": LLM_MODEL}},
            "confidence": max([r.score for r in retrieved]) if retrieved else 0.0,
            "sources": [{{"content": r.content[:200], "score": r.score}} for r in retrieved],
        }}
        
    except Exception as e:
        logger.exception("RAG flow failed")
        raise
'''


def _generate_agentic_flow(provider: str, model: str) -> str:
    """Generate Agentic flow"""
    return f'''"""
Agentic Flow
============
Tool-using agent with planning and execution.
Model: {provider}/{model}
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

# Clients
llm_client = None
tool_client = None

# Configuration
LLM_PROVIDER = "{provider}"
LLM_MODEL = "{model}"
TOOL_MODEL = "gpt-4o"

# Tool registry
TOOLS: Dict[str, Dict] = {{}}


def register_tool(name: str, description: str, parameters: Dict):
    """Register a tool"""
    def decorator(func: Callable):
        TOOLS[name] = {{"function": func, "description": description, "parameters": parameters}}
        return func
    return decorator


# Example tools
@register_tool("search", "Search for information", {{"type": "object", "properties": {{"query": {{"type": "string"}}}}, "required": ["query"]}})
async def search_tool(query: str) -> str:
    return f"Search results for: {{query}}"


@register_tool("calculate", "Perform calculations", {{"type": "object", "properties": {{"expression": {{"type": "string"}}}}, "required": ["expression"]}})
async def calculate_tool(expression: str) -> str:
    try:
        return str(eval(expression))
    except:
        return "Calculation error"


async def initialize_services():
    """Initialize clients"""
    global llm_client, tool_client
    
    # Initialize with AnthropicFoundry
    api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
    endpoint = os.environ.get("ANTHROPIC_FOUNDRY_ENDPOINT")
    
    if api_key and endpoint:
        from anthropic import Anthropic
        llm_client = Anthropic(
            api_key=api_key,
            base_url=endpoint
        )
        tool_client = llm_client  # Use same client for tools
        logger.info("Anthropic client initialized")
    else:
        logger.warning("Anthropic credentials not configured")


async def run_agent(task: str, max_iterations: int = 10) -> Dict[str, Any]:
    """Run agent loop"""
    if not tool_client:
        return {{"result": {{"answer": f"Demo: Agent task '{{task[:100]}}'. Set OPENAI_API_KEY for tools."}}, "confidence": 0.5}}
    
    tools = [
        {{"type": "function", "function": {{"name": n, "description": t["description"], "parameters": t["parameters"]}}}}
        for n, t in TOOLS.items()
    ]
    
    messages = [{{"role": "system", "content": "You are a helpful agent. Use tools when needed."}}, {{"role": "user", "content": task}}]
    tool_results = []
    
    for _ in range(max_iterations):
        response = await tool_client.chat.completions.create(model=TOOL_MODEL, messages=messages, tools=tools, tool_choice="auto")
        message = response.choices[0].message
        
        if not message.tool_calls:
            return {{"result": {{"answer": message.content}}, "confidence": 0.8, "tool_results": tool_results}}
        
        messages.append(message)
        for tc in message.tool_calls:
            args = json.loads(tc.function.arguments)
            result = await TOOLS[tc.function.name]["function"](**args)
            tool_results.append({{"tool": tc.function.name, "result": result}})
            messages.append({{"role": "tool", "tool_call_id": tc.id, "content": str(result)}})
    
    return {{"result": {{"answer": "Max iterations reached"}}, "confidence": 0.5, "tool_results": tool_results}}


async def process_request(input_data: str, context: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Main agentic processing flow"""
    return await run_agent(input_data, options.get("max_iterations", 10))
'''


def _generate_hybrid_flow(provider: str, model: str) -> str:
    """Generate Hybrid flow"""
    return f'''"""
Hybrid Flow
===========
Combines RAG and Agentic patterns with intelligent routing.
Model: {provider}/{model}
"""

import os
import logging
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

LLM_PROVIDER = "{provider}"
LLM_MODEL = "{model}"

llm_client = None
classifier_client = None


class RouteType(Enum):
    RAG = "rag"
    AGENTIC = "agentic"
    DIRECT = "direct"


async def initialize_services():
    """Initialize clients"""
    global llm_client, classifier_client
    
    # Initialize with AnthropicFoundry
    api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY")
    endpoint = os.environ.get("ANTHROPIC_FOUNDRY_ENDPOINT")
    
    if api_key and endpoint:
        from anthropic import AnthropicFoundry
        llm_client = AnthropicFoundry(
            api_key=api_key,
            base_url=endpoint
        )
        classifier_client = llm_client  # Use same client for classification
        logger.info("AnthropicFoundry clients initialized")
    else:
        logger.warning("AnthropicFoundry credentials not configured")
    
    logger.info("Hybrid flow services initialized")


async def classify_request(input_data: str) -> RouteType:
    """Classify request to determine routing"""
    if not classifier_client:
        return RouteType.DIRECT
    
    response = classifier_client.messages.create(
        model=os.environ.get("ANTHROPIC_FOUNDRY_DEPLOYMENT_NAME", "claude-sonnet-4-5"),
        messages=[
            {{"role": "user", "content": f"Classify: RAG (info lookup), AGENTIC (tools/actions), DIRECT (simple). Reply with one word only.\\n\\n{{input_data[:500]}}"}}
        ],
        max_tokens=10,
    )
    
    classification = response.content[0].text.strip().upper()
    return RouteType.RAG if "RAG" in classification else RouteType.AGENTIC if "AGENT" in classification else RouteType.DIRECT


async def process_request(input_data: str, context: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Main hybrid processing flow"""
    
    if llm_client is None:
        return {{"result": {{"answer": f"Demo: '{{input_data[:100]}}'. Set API keys for full functionality.", "route": "demo"}}, "confidence": 0.5}}
    
    # Classify and route
    route = await classify_request(input_data)
    logger.info(f"Routed to: {{route.value}}")
    
    # Process based on route (simplified - all go to direct for starter kit)
    system_prompt = "You are a helpful assistant."
    try:
        with open("prompts/system_prompt.txt", "r") as f:
            system_prompt = f.read().strip()
    except FileNotFoundError:
        pass
    
    if LLM_PROVIDER == "anthropic":
        response = await llm_client.messages.create(
            model=LLM_MODEL,
            max_tokens=options.get("max_tokens", 4096),
            system=system_prompt,
            messages=[{{"role": "user", "content": input_data}}],
        )
        answer = response.content[0].text
    else:
        # Fallback to same client 
        response = llm_client.messages.create(
            model=deployment_name,
            messages=[{{"role": "user", "content": f"{{system_prompt}}\\n\\n{{input_data}}"}}],
            max_tokens=1000,
        )
        answer = response.content[0].text
    
    return {{"result": {{"answer": answer, "route": route.value, "model": LLM_MODEL}}, "confidence": 0.8}}
'''


# =============================================================================
# OTHER FILE GENERATORS
# =============================================================================

def _generate_system_prompt(blueprint: Dict) -> str:
    """Generate prompts/system_prompt.txt"""
    cover = blueprint.get("cover", {})
    exec_summary = blueprint.get("executiveSummary", {})
    ai_design = blueprint.get("aiDesign", {})
    
    return f"""You are an AI assistant for {cover.get('useCaseName', 'this application')}.

Domain: {cover.get('businessDomain', 'Enterprise')}
Pattern: {ai_design.get('selectedPattern', 'Automation')}

Your role:
{exec_summary.get('proposedSolution', 'Assist users with their queries accurately and helpfully.')}

Guidelines:
- Be concise and accurate
- If unsure, say so rather than guessing
- Focus on the task at hand
- Provide actionable responses when possible
"""


def _generate_openapi_yaml(blueprint: Dict, pattern: str) -> str:
    """Generate contracts/openapi.yaml"""
    cover = blueprint.get("cover", {})
    use_case_name = cover.get("useCaseName", "AI Service")
    
    return f"""openapi: 3.0.3
info:
  title: {use_case_name} API
  description: {pattern} Pattern - Generated by AI Studio Factory
  version: 1.0.0

servers:
  - url: http://localhost:8001
    description: Development server

paths:
  /api/health:
    get:
      summary: Health check
      operationId: healthCheck
      responses:
        '200':
          description: Service healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: healthy
                  version:
                    type: string
                    example: "1.0.0"
                  pattern:
                    type: string
                    example: "{pattern}"

  /api/demo-run:
    post:
      summary: Demo flow
      operationId: demoRun
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                input:
                  type: string
                  example: "Hello, test the flow"
      responses:
        '200':
          description: Demo result
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                  result:
                    type: object
                  pattern:
                    type: string
                  model:
                    type: string

  /api/process:
    post:
      summary: Process input
      operationId: processInput
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - input
              properties:
                input:
                  type: string
                  description: Input text to process
                context:
                  type: object
                options:
                  type: object
      responses:
        '200':
          description: Processing result
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                  result:
                    type: object
                  confidence:
                    type: number
                  sources:
                    type: array
                    items:
                      type: object
                  metadata:
                    type: object
"""


def _generate_blueprint_doc(blueprint: Dict) -> str:
    """Generate blueprint.md (renamed from blueprint_v3.md)"""
    return f"""# Blueprint Documentation

## Metadata
- **ID**: {blueprint.get('metadata', {}).get('id', 'N/A')}
- **Generated**: {blueprint.get('metadata', {}).get('generatedAt', 'N/A')}
- **Status**: {blueprint.get('metadata', {}).get('status', 'Draft')}

## Cover
```json
{json.dumps(blueprint.get('cover', {}), indent=2)}
```

## Executive Summary
```json
{json.dumps(blueprint.get('executiveSummary', {}), indent=2)}
```

## AI Design
```json
{json.dumps(blueprint.get('aiDesign', {}), indent=2)}
```

## Scope Lock
```json
{json.dumps(blueprint.get('scopeLock', {}), indent=2)}
```

## Value Hypothesis
```json
{json.dumps(blueprint.get('valueHypothesis', {}), indent=2)}
```

## Functional Design
```json
{json.dumps(blueprint.get('functionalDesign', {}), indent=2)}
```

## Reference Architecture
```json
{json.dumps(blueprint.get('referenceArchitecture', {}), indent=2)}
```

## Operating Model
```json
{json.dumps(blueprint.get('operatingModel', {}), indent=2)}
```

## Governance Gates
```json
{json.dumps(blueprint.get('governanceGates', {}), indent=2)}
```

## Delivery Plan
```json
{json.dumps(blueprint.get('deliveryPlan', {}), indent=2)}
```

## Factory Handoff
```json
{json.dumps(blueprint.get('factoryHandoff', {}), indent=2)}
```

---
*Disclaimer: {blueprint.get('metadata', {}).get('disclaimer', 'Advisory only.')}*
"""


def _generate_gitignore() -> str:
    """Generate .gitignore"""
    return """# Python
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
env/
.env

# IDE
.idea/
.vscode/
*.swp

# Data
*.db
data/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
dist/
build/
*.egg-info/
"""


def _generate_test_file(blueprint: Dict, pattern: str) -> str:
    """Generate tests/test_api.py"""
    return '''"""
API Tests
=========
Basic tests for the API endpoints.

Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_health_check():
    """Test health endpoint returns healthy status"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "pattern" in data


def test_demo_run():
    """Test demo endpoint works"""
    response = client.post(
        "/api/demo-run",
        json={"input": "Hello, test"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "result" in data


def test_process_input():
    """Test main process endpoint"""
    response = client.post(
        "/api/process",
        json={
            "input": "Test query",
            "context": {"user_id": "test"},
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "result" in data


def test_process_input_empty():
    """Test process endpoint rejects empty input"""
    response = client.post(
        "/api/process",
        json={"input": ""}
    )
    assert response.status_code == 422  # Validation error
'''


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

async def generate_starter_kit(
    blueprint: Dict[str, Any],
    use_llm: bool = True
) -> tuple[bytes, KitMetadata]:
    """
    Generate a complete, runnable starter kit from a blueprint.
    
    Returns:
        tuple: (zip_bytes, metadata)
    """
    # Extract key info
    cover = blueprint.get("cover", {})
    ai_design = blueprint.get("aiDesign", {})
    pattern = ai_design.get("selectedPattern", "Automation")
    blueprint_id = blueprint.get("metadata", {}).get("id", str(uuid.uuid4()))
    blueprint_name = cover.get("useCaseName", "AI Use Case")
    
    # Generate all files
    files: Dict[str, str] = {}
    
    # Root files
    files["README.md"] = _generate_readme(blueprint)
    files[".gitignore"] = _generate_gitignore()
    files["blueprint.md"] = _generate_blueprint_doc(blueprint)  # Renamed from blueprint_v3.md
    
    # Backend
    files["backend/main.py"] = _generate_backend_main(blueprint, pattern)
    files["backend/requirements.txt"] = _generate_backend_requirements(pattern)
    files["backend/.env.example"] = _generate_env_example(blueprint)
    
    # Orchestrator
    files["orchestrator/flow.py"] = _generate_orchestrator_flow(blueprint, pattern)
    files["orchestrator/__init__.py"] = '"""Orchestrator module"""'
    
    # Config
    files["config/llm_config.py"] = _generate_llm_config(blueprint, pattern)
    files["config/__init__.py"] = '"""Config module"""'
    
    # Prompts
    files["prompts/system_prompt.txt"] = _generate_system_prompt(blueprint)
    
    # Contracts
    files["contracts/openapi.yaml"] = _generate_openapi_yaml(blueprint, pattern)
    
    # Tests
    files["tests/__init__.py"] = '"""Tests module"""'
    files["tests/test_api.py"] = _generate_test_file(blueprint, pattern)
    
    # Create ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    
    zip_bytes = zip_buffer.getvalue()
    
    # Create metadata
    metadata = KitMetadata(
        blueprint_id=blueprint_id,
        blueprint_name=blueprint_name,
        pattern=pattern,
        files=list(files.keys()),
        llm_enhanced=use_llm,
    )
    
    return zip_bytes, metadata


async def regenerate_module(
    blueprint: Dict[str, Any],
    module: str,
    use_llm: bool = True
) -> Dict[str, str]:
    """Regenerate a specific module"""
    ai_design = blueprint.get("aiDesign", {})
    pattern = ai_design.get("selectedPattern", "Automation")
    
    files: Dict[str, str] = {}
    
    if module == "backend":
        files["backend/main.py"] = _generate_backend_main(blueprint, pattern)
        files["backend/requirements.txt"] = _generate_backend_requirements(pattern)
        files["backend/.env.example"] = _generate_env_example(blueprint)
    elif module == "orchestrator":
        files["orchestrator/flow.py"] = _generate_orchestrator_flow(blueprint, pattern)
    elif module == "prompts":
        files["prompts/system_prompt.txt"] = _generate_system_prompt(blueprint)
    elif module == "contracts":
        files["contracts/openapi.yaml"] = _generate_openapi_yaml(blueprint, pattern)
    elif module == "config":
        files["config/llm_config.py"] = _generate_llm_config(blueprint, pattern)
    
    return files


async def add_endpoint_to_kit(
    blueprint: Dict[str, Any],
    endpoint_name: str,
    method: str = "POST",
    description: str = "",
    request_schema: Optional[Dict] = None,
    response_schema: Optional[Dict] = None,
) -> Dict[str, str]:
    """Generate code for a new endpoint"""
    
    # Generate endpoint code snippet
    safe_name = endpoint_name.replace("-", "_").replace(" ", "_").lower()
    
    endpoint_code = f'''
# Add this to backend/main.py

class {safe_name.title().replace("_", "")}Request(BaseModel):
    """Request for {endpoint_name}"""
    data: str = Field(..., description="Input data")


class {safe_name.title().replace("_", "")}Response(BaseModel):
    """Response for {endpoint_name}"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    result: Dict[str, Any]


@app.{method.lower()}("/api/{endpoint_name}")
async def {safe_name}(request: {safe_name.title().replace("_", "")}Request):
    """
    {description or f'{endpoint_name} endpoint'}
    """
    # Implement your logic here
    return {safe_name.title().replace("_", "")}Response(
        result={{"message": "Endpoint implemented", "input": request.data}}
    )
'''
    
    return {
        "endpoint_code": endpoint_code,
        "endpoint_name": endpoint_name,
        "method": method,
    }
