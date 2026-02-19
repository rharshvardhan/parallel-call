import os
import uuid
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)




load_dotenv()


class UseCaseIntake(BaseModel):
    useCaseName: str
    problemStatement: str
    businessDomain: str
    targetUsers: str
    desiredOutcome: str
    constraints: Optional[str] = None
    assumptions: Optional[str] = None


class MarketplacePotential(BaseModel):
    reusableAsset: bool
    confidence: str
    notes: Optional[str] = None


class BlueprintStep1(BaseModel):
    useCaseName: str
    problemStatement: str
    businessDomain: str
    targetUsers: str
    desiredOutcome: str
    keyConstraints: str
    keyAssumptions: str


class BlueprintStep2(BaseModel):
    reuseRecommendation: str
    reuseConfidence: str
    rationale: str


class BlueprintStep3(BaseModel):
    businessValue: str
    technicalFeasibility: str
    overallConfidence: str
    risks: List[str]


class BlueprintStep4(BaseModel):
    recommendedAction: str
    recommendedPattern: str
    autonomy: str
    justification: str


class BlueprintStep5(BaseModel):
    blueprintEnabled: bool
    executiveSummary: str
    scopeAndBoundaries: List[str]
    validationSummary: List[str]
    solutionPattern: str
    conceptualWorkflow: List[str]
    conceptualArchitecture: List[str]
    effortAndTimeline: str
    governanceControlPoints: List[str]
    factoryReadiness: List[str]
    marketplacePotential: MarketplacePotential
    # Additional structured deliverables for PDF and governance views
    useCaseType: str
    maturityLevel: str
    modelSelection: str
    targetArchitecture: List[str]
    dataIntegrationChecklist: List[str]
    risksAndGuardrails: List[str]
    nextSteps: List[str]
    marketplaceReferences: List[str]


class BlueprintMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generatedAt: datetime = Field(default_factory=datetime.utcnow)
    status: str = "Advisory - Draft"
    disclaimer: str = (
        "This blueprint is advisory only. It should be reviewed by enterprise "
        "architecture, security, and risk before being treated as authoritative."
    )


class Blueprint(BaseModel):
    metadata: BlueprintMetadata
    step1: BlueprintStep1
    step2: BlueprintStep2
    step3: BlueprintStep3
    step4: BlueprintStep4
    step5: BlueprintStep5


def _build_system_message() -> str:
    return (
        "You are Infinite AI Studio, an enterprise AI Strategy & Architecture "
        "Review Board combined with a forward-deployed engineering function. "
        "You are platform-agnostic, governance-aware, and decision-oriented. "
        "You NEVER behave like a chatbot. You write concise, structured, "
        "CIO/CTO-ready outputs only. You never invent numeric precision, "
        "percentages, or costs."
    )


def _build_user_prompt(intake: UseCaseIntake) -> str:
    # Prompt is deliberately explicit and asks for JSON only.
    return f"""
You will receive a SINGLE AI initiative intake and must return a STRICT JSON object
matching the schema below. Do not add commentary or prose outside JSON. Do not use
conversational tone. Assume a large, regulated enterprise context.

INTAKE
------
Use Case Name: {intake.useCaseName}
Problem Statement: {intake.problemStatement}
Business Function / Domain: {intake.businessDomain}
Target Users: {intake.targetUsers}
Desired Business Outcome: {intake.desiredOutcome}
Key Constraints: {intake.constraints or "Not specified"}
Key Assumptions: {intake.assumptions or "Not specified"}

REQUIRED JSON SCHEMA (TYPES ONLY, DO NOT ECHO THIS BACK):
{{
  "step1": {{
    "useCaseName": string,
    "problemStatement": string,
    "businessDomain": string,
    "targetUsers": string,
    "desiredOutcome": string,
    "keyConstraints": string,
    "keyAssumptions": string
  }},
  "step2": {{
    "reuseRecommendation": "As-Is" | "Extend" | "Build New",
    "reuseConfidence": "High" | "Medium" | "Low",
    "rationale": string
  }},
  "step3": {{
    "businessValue": "High" | "Medium" | "Low",
    "technicalFeasibility": "High" | "Medium" | "Low",
    "overallConfidence": "High" | "Medium" | "Low",
    "risks": array of string (2-6 bullet points)
  }},
  "step4": {{
    "recommendedAction": "Build" | "Extend" | "Defer",
    "recommendedPattern": "Retrieval-Augmented Generation (RAG)" | "Task Automation" | "Agentic Workflow (ReAct-based)",
    "autonomy": "Assisted" | "Semi-Autonomous" | "Autonomous",
    "justification": string (2-4 concise sentences)
  }},
  "step5": {{
    "blueprintEnabled": boolean,
    "executiveSummary": string,
    "scopeAndBoundaries": array of string,
    "validationSummary": array of string,
    "solutionPattern": string,
    "conceptualWorkflow": array of string,
    "conceptualArchitecture": array of string,
    "effortAndTimeline": string,
    "governanceControlPoints": array of string,
    "factoryReadiness": array of string,
    "marketplacePotential": {{
      "reusableAsset": boolean,
      "confidence": "High" | "Medium" | "Low",
      "notes": string
    }},
    "useCaseType": string,
    "maturityLevel": string,
    "modelSelection": string,
    "targetArchitecture": array of string,
    "dataIntegrationChecklist": array of string,
    "risksAndGuardrails": array of string,
    "nextSteps": array of string,
    "marketplaceReferences": array of string
  }}
}}

RESPONSE FORMAT
---------------
Return ONLY a single JSON object matching the SCHEMA above (without comments). Do
NOT wrap it in markdown fences. Do NOT add any prose before or after the JSON.
""".strip()


async def generate_blueprint_with_llm(intake: UseCaseIntake) -> Blueprint:
    # Check for Anthropic configuration (try both Foundry and regular Anthropic)
    api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    endpoint = os.environ.get("ANTHROPIC_FOUNDRY_ENDPOINT")
    deployment_name = os.environ.get("ANTHROPIC_FOUNDRY_DEPLOYMENT_NAME") or "claude-3-5-sonnet-20241022"
    
    if not api_key:
        raise RuntimeError("Anthropic API key is not configured. Set ANTHROPIC_FOUNDRY_API_KEY or ANTHROPIC_API_KEY in backend/.env")

    # Normalize endpoint: Foundry endpoints sometimes include the API path
    # (e.g. /anthropic/v1/messages). The SDK expects a base URL, so strip
    # known trailing paths if present.
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
                logger.info(f"Initialized AnthropicFoundry client with endpoint: {endpoint}")
            except Exception as e:
                init_errors.append(f"AnthropicFoundry init failed: {e}")
                logger.exception("AnthropicFoundry initialization failed, will try fallback: %s", e)
        except ImportError:
            init_errors.append("AnthropicFoundry is not available in the installed anthropic package")
            logger.info("AnthropicFoundry class not found in anthropic package; will try standard Anthropic client")

    if client is None:
        try:
            from anthropic import Anthropic
            # Pass base_url when provided; some SDKs accept it, others ignore.
            try:
                client = Anthropic(api_key=api_key, base_url=endpoint) if endpoint else Anthropic(api_key=api_key)
            except TypeError:
                # Older/newer SDK variants may not accept base_url kwarg
                client = Anthropic(api_key=api_key)
            logger.info("Initialized standard Anthropic client")
        except Exception as e:
            init_errors.append(str(e))
            logger.exception("Failed to initialize any Anthropic client: %s", e)
            raise RuntimeError("Failed to initialize Anthropic client. Errors: %s" % ("; ".join(init_errors)))

    system_message = _build_system_message()
    user_prompt = _build_user_prompt(intake)
    
    # Make call using AnthropicFoundry
    try:
        logger.info(f"Making request to Anthropic with model: {deployment_name}")

        # Dynamically pick the supported create method on the client.
        response = None
        messages_payload = [{"role": "user", "content": f"{system_message}\n\n{user_prompt}"}]

        if hasattr(client, "messages") and hasattr(client.messages, "create"):
            response = client.messages.create(model=deployment_name, messages=messages_payload, max_tokens=4000)
        elif hasattr(client, "chat") and hasattr(client.chat, "completions") and hasattr(client.chat.completions, "create"):
            response = client.chat.completions.create(model=deployment_name, messages=messages_payload, max_tokens=4000)
        elif hasattr(client, "responses") and hasattr(client.responses, "create"):
            # Some SDKs use a single-string input rather than messages for responses API
            combined_input = f"{system_message}\n\n{user_prompt}"
            try:
                response = client.responses.create(model=deployment_name, input=combined_input, max_tokens=4000)
            except TypeError:
                # fallback to messages structure if supported
                response = client.responses.create(model=deployment_name, messages=messages_payload, max_tokens=4000)
        else:
            raise RuntimeError("Anthropic client does not expose a supported 'create' method (messages, chat.completions, or responses)")

        logger.info("Anthropic request completed")
    except Exception as exc:
        logger.exception(f"Anthropic request failed: {exc}")
        raise RuntimeError(f"Failed to call Anthropic API: {str(exc)}")

    # Extract text content (Anthropic response wrapper)
    content = None
    try:
        # Multiple SDK response shapes are possible; try several common patterns.
        if hasattr(response, "content") and getattr(response, "content"):
            # Foundry / messages API: content is a list of message objects
            content = getattr(response, "content")[0].text
        elif isinstance(response, dict):
            # Some clients return dict-like objects
            if "output" in response:
                content = response.get("output")
            elif "choices" in response and len(response["choices"]) > 0:
                ch = response["choices"][0]
                # common shape: choices[0].message.content or choices[0].text
                if isinstance(ch.get("message"), dict) and "content" in ch.get("message"):
                    content = ch["message"]["content"]
                else:
                    content = ch.get("text") or ch.get("message")
            else:
                # Last resort: stringify
                content = str(response)
        elif hasattr(response, "completion"):
            content = getattr(response, "completion")
        else:
            # Try string conversion as a last fallback
            content = str(response)

        if not content:
            raise ValueError("Empty content extracted from Anthropic response")

        logger.info(f"Extracted response text, length: {len(content) if hasattr(content, '__len__') else 'unknown'}")
    except Exception as e:
        logger.exception(f"Failed to extract text from response: {e}")
        try:
            content = str(response)
        except Exception:
            content = "(unreadable response)"
        raise RuntimeError(f"Invalid response format from Anthropic: {str(e)}. Raw response: {content[:1000]}")

    logger.debug("LLM raw response content: %s", (content[:500] + '...') if content and len(content) > 500 else content)


    import json
    try:
        # Clean the content in case there are markdown code blocks
        clean_content = content.strip()
        if clean_content.startswith('```json'):
            clean_content = clean_content[7:]
        if clean_content.endswith('```'):
            clean_content = clean_content[:-3]
        clean_content = clean_content.strip()
        
        parsed = json.loads(clean_content)
        logger.info("Successfully parsed JSON response")
    except json.JSONDecodeError as exc:
        logger.exception("Failed to parse LLM response as JSON. Raw content: %s", content)
        raise RuntimeError(f"LLM returned non-JSON content: {exc}. Raw content: {content[:500]}")

    blueprint = Blueprint(
        metadata=BlueprintMetadata(),
        step1=BlueprintStep1(**parsed["step1"]),
        step2=BlueprintStep2(**parsed["step2"]),
        step3=BlueprintStep3(**parsed["step3"]),
        step4=BlueprintStep4(**parsed["step4"]),
        step5=BlueprintStep5(
            **{
                **parsed["step5"],
                "marketplacePotential": MarketplacePotential(
                    **parsed["step5"]["marketplacePotential"]
                ),
            }
        ),
    )

    return blueprint
