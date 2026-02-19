import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from blueprint_service import BlueprintStep4, BlueprintStep3

import os
from dotenv import load_dotenv

load_dotenv()


class OpportunityClusterRequest(BaseModel):
  """Request for AI opportunity inspiration.

  This deliberately does NOT include detailed internal data – only high-level
  signals like vertical and lens.
  """

  vertical: str = Field(
    ..., description="Vertical focus, e.g. Payor, Provider, Medtech, Life Sciences, Cross-Industry"
  )
  lens: str = Field(
    ..., description="Technical or functional lens, e.g. Data & Integration, SDLC & MLOps, Content & Guardrails, Member/Patient Experience"
  )


class OpportunityCluster(BaseModel):
  id: str = Field(default_factory=lambda: str(uuid.uuid4()))
  title: str
  description: str
  vertical: str
  lens: str
  patterns: List[str]
  sensitivity: str
  maturityHint: str


class OpportunityResponse(BaseModel):
  generatedAt: datetime = Field(default_factory=datetime.utcnow)
  advisory: bool = True
  clusters: List[OpportunityCluster]


def _system_message() -> str:
  return (
    "You are Infinite AI Studio's Opportunity Intelligence engine. "
    "You suggest AI opportunity areas for large, regulated enterprises "
    "with a strong focus on healthcare (payor, provider, medtech, life sciences) "
    "and platform / SDLC. You never speak conversationally. You respond with "
    "short, structured bullets and avoid numeric claims, percentages, or ROI "
    "numbers."
  )


def _user_prompt(vertical: str, lens: str) -> str:
  return f"""
Generate 4–6 AI opportunity clusters for a large enterprise.

Context:
- Vertical: {vertical}
- Lens: {lens}
- Studio patterns: Retrieval-Augmented Generation (RAG), Agentic workflows, Task automation.
- Output must be advisory only, not a promise of results.

For each cluster, provide:
- title: concise and non-marketing.
- description: 1–2 sentences about what AI would do and why it matters.
- patterns: 1–3 of ["RAG", "Agentic", "Automation", "Hybrid"].
- sensitivity: one of ["PHI/PII", "Regulated", "Operational", "Low-risk"].
- maturityHint: one of ["Explore", "Pilot-ready", "Scale-ready"].

RESPONSE FORMAT (JSON ONLY):
{{
  "clusters": [
    {{
      "title": string,
      "description": string,
      "patterns": array of string,
      "sensitivity": string,
      "maturityHint": string
    }},
    ... 4 to 6 items total ...
  ]
}}

Do not add extra keys. Do not write any prose before or after the JSON.
""".strip()


async def generate_opportunity_clusters(
  req: OpportunityClusterRequest,
) -> OpportunityResponse:

  # Check for Anthropic configuration (try both Foundry and regular Anthropic)
  api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
  endpoint = os.environ.get("ANTHROPIC_FOUNDRY_ENDPOINT")
  deployment_name = os.environ.get("ANTHROPIC_FOUNDRY_DEPLOYMENT_NAME") or "claude-3-5-sonnet-20241022"
  
  if not api_key:
    raise RuntimeError("Anthropic API key is not configured. Set ANTHROPIC_FOUNDRY_API_KEY or ANTHROPIC_API_KEY in backend/.env")

  # Normalize endpoint: Foundry endpoints sometimes include the API path
  if endpoint:
    ep = endpoint.rstrip('/')
    for suffix in ('/v1/messages', '/messages', '/anthropic/v1/messages'):
      if ep.endswith(suffix):
        ep = ep[: -len(suffix)]
        break
    endpoint = ep

  # Prefer AnthropicFoundry when a custom Foundry endpoint is provided.
  client = None
  init_errors = []
  if endpoint:
    try:
      from anthropic import AnthropicFoundry
      try:
        client = AnthropicFoundry(api_key=api_key, base_url=endpoint)
        print(f"Initialized AnthropicFoundry client with endpoint: {endpoint}")
      except Exception as e:
        init_errors.append(f"AnthropicFoundry init failed: {e}")
        print(f"AnthropicFoundry initialization failed, will try fallback: {e}")
    except ImportError:
      init_errors.append("AnthropicFoundry is not available in the installed anthropic package")
      print("AnthropicFoundry class not found in anthropic package; will try standard Anthropic client")

  if client is None:
    try:
      from anthropic import Anthropic
      try:
        client = Anthropic(api_key=api_key, base_url=endpoint) if endpoint else Anthropic(api_key=api_key)
      except TypeError:
        client = Anthropic(api_key=api_key)
      print("Initialized standard Anthropic client")
    except Exception as e:
      init_errors.append(str(e))
      print(f"Failed to initialize any Anthropic client: {e}")
      raise RuntimeError("Failed to initialize Anthropic client. Errors: %s" % ("; ".join(init_errors)))

  system_message = _system_message()
  user_prompt = _user_prompt(req.vertical, req.lens)
  
  # Make call using client with fallback support
  try:
    print(f"Making request to Anthropic with model: {deployment_name}")
    response = client.messages.create(
      model=deployment_name,
      messages=[
        {"role": "user", "content": f"{system_message}\n\n{user_prompt}"}
      ],
      max_tokens=2048,
    )
    print("Anthropic request completed")
  except Exception as exc:
    print(f"Anthropic request failed: {exc}")
    raise RuntimeError(f"Failed to call Anthropic API: {str(exc)}")

  # Extract text content (Anthropic response wrapper)
  content = None
  try:
    if hasattr(response, "content") and getattr(response, "content"):
      content = getattr(response, "content")[0].text
    elif isinstance(response, dict):
      if "output" in response:
        content = response.get("output")
      elif "choices" in response and len(response["choices"]) > 0:
        ch = response["choices"][0]
        if isinstance(ch.get("message"), dict) and "content" in ch.get("message"):
          content = ch["message"]["content"]
        else:
          content = ch.get("text") or ch.get("message")
      else:
        content = str(response)
    elif hasattr(response, "completion"):
      content = getattr(response, "completion")
    else:
      content = str(response)

    if not content:
      raise ValueError("Empty content extracted from Anthropic response")

    print(f"Extracted response text, length: {len(content) if hasattr(content, '__len__') else 'unknown'}")
  except Exception as e:
    print(f"Failed to extract text from response: {e}")
    try:
      content = str(response)
    except Exception:
      content = "(unreadable response)"
    raise RuntimeError(f"Invalid response format from Anthropic: {str(e)}. Raw response: {content[:1000]}")

  import json

  print("LLM raw response content:", (content[:500] + '...') if content and len(content) > 500 else content)

  # Clean up response if wrapped in code fences
  content = content.strip()
  if content.startswith("```json"):
    content = content[7:]
  if content.startswith("```"):
    content = content[3:]
  if content.endswith("```"):
    content = content[:-3]
  content = content.strip()

  try:
    parsed = json.loads(content)
    print("Successfully parsed JSON response")
  except json.JSONDecodeError as exc:
    print(f"Failed to parse LLM response as JSON. Raw content: {content}")
    raise RuntimeError(f"LLM returned non-JSON content for opportunities: {exc}")

  clusters: List[OpportunityCluster] = []
  try:
    for item in parsed.get("clusters", []):
      clusters.append(
        OpportunityCluster(
          title=item.get("title", "Untitled area"),
          description=item.get("description", ""),
          vertical=req.vertical,
          lens=req.lens,
          patterns=item.get("patterns", []),
          sensitivity=item.get("sensitivity", "Operational"),
          maturityHint=item.get("maturityHint", "Explore"),
        )
      )
    print(f"Successfully constructed {len(clusters)} opportunity clusters")
  except Exception as e:
    print(f"Failed to construct opportunity clusters: {e}")
    raise RuntimeError(f"Failed to construct clusters from LLM response: {str(e)}")

  return OpportunityResponse(clusters=clusters)
