"""
Blueprint Service V3 - Decision-Ready, Build-Oriented Blueprint Generation
============================================================================
Transforms AI use cases into actionable blueprints that help leaders:
- Decide whether to proceed
- Understand what will be built
- Know what to do next
"""

import os
import uuid
import json
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field




load_dotenv()


# =============================================================================
# V3 PYDANTIC MODELS - 14 Numbered Sections
# =============================================================================

# Section 1: Blueprint Cover & Identity
class BlueprintCover(BaseModel):
    useCaseName: str
    businessDomain: str
    sponsorOwner: str = "TBC"
    blueprintType: str  # "Advisory" or "Build-Ready"
    studioVersion: str = "V3"
    generatedDate: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))


# Section 2: Executive Blueprint Summary (At-a-Glance)
class ExecutiveSummary(BaseModel):
    problemStatement: str  # 1-2 lines
    proposedSolution: str  # What will be built
    decision: str  # Build / Extend / Reuse / Do Not Proceed
    businessValue: str  # High / Medium / Low
    businessValueRationale: str  # 1-line Gartner-style
    feasibility: str  # High / Medium / Low
    feasibilityRationale: str  # 1-line Gartner-style
    confidenceLevel: str  # High / Medium / Low
    estimatedTimeline: str  # Range e.g., "4-8 weeks"
    topRisks: List[str]  # Top 3 risks (short bullets)
    nextBestAction: str  # Clear and directive


# Section 3: Use Case Definition & Scope Lock
class ScopeLock(BaseModel):
    inScopeCapabilities: List[str]
    outOfScope: List[str]
    primaryUserPersonas: List[str]
    successCriteria: List[str]  # Measurable
    keyAssumptions: List[str]


# Section 4: Business & Value Hypothesis
class ValueHypothesis(BaseModel):
    primaryValueDriver: str  # cost, speed, risk, CX
    valueCreationMechanism: str
    valueConfidenceLevel: str  # High / Medium / Low
    failureConditions: List[str]  # What would invalidate this use case


# Section 5: Functional Solution Design
class FunctionalDesign(BaseModel):
    inputs: List[str]  # Data/events
    coreProcessingStages: List[str]
    aiDecisionPoints: List[str]
    humanInTheLoopLocations: List[str]
    outputs: List[str]  # Actions


# Section 6: AI Design & Pattern Selection
class AIDesign(BaseModel):
    selectedPattern: str  # RAG / Agentic / Hybrid / Automation
    patternRationale: str
    rejectedPatterns: List[str]  # With reasons
    autonomyLevel: str  # Assisted / Semi / High
    learningFeedbackLoop: str


# Section 7: Reference Architecture (Logical)
class ReferenceArchitecture(BaseModel):
    logicalLayers: List[str]  # UI, Orchestration, AI, Data, Governance
    dataFlowNarrative: str
    trustSecurityBoundaries: List[str]
    modelInteractionPoints: List[str]
    observabilityMonitoring: List[str]


# Section 8: Operating Model & Ownership
class OperatingModel(BaseModel):
    promptAILogicOwnership: str
    approvalChangeControl: str
    qualityMonitoringResponsibility: str
    failureHandlingEscalation: str
    retrainingIterationApproach: str


# Section 9: Governance Decision Gate
class DecisionGate(BaseModel):
    gateName: str  # Gate 1, 2, or 3
    gateType: str  # Build Approval / Pilot Approval / Scale Approval
    whatMustBeTrue: List[str]
    decisionOwner: str
    blockingRisks: List[str]


class GovernanceGates(BaseModel):
    gate1BuildApproval: DecisionGate
    gate2PilotApproval: DecisionGate
    gate3ScaleApproval: DecisionGate


# Section 10: Delivery & Rollout Plan
class DeliveryPlan(BaseModel):
    mvpScope: List[str]
    pilotScope: List[str]
    scaleScope: List[str]
    prototypeTimeline: str  # 2-4 weeks
    endToEndPrototypeTimeline: str  # 4-8 weeks
    enterpriseReadyTimeline: str  # 3-4 months
    keyRisksPerPhase: List[str]


# Section 11: Factory Handoff Contract
class FactoryHandoff(BaseModel):
    inputsFactoryReceives: List[str]
    whatFactoryValidates: List[str]
    whatFactoryMayChange: List[str]
    lockedMustNotChange: List[str]


# Section 12: Acceleration & Reuse Opportunities (Optional)
class AccelerationOpportunities(BaseModel):
    roiEstimationFramework: str  # Applied / Recommended Next / Optional / N/A
    modelSelectionGuidance: str
    promptAccelerators: str
    securityComplianceAccelerators: str


# Section 13: Gaps & Custom Build Areas
class GapsAndCustomBuild(BaseModel):
    componentsRequiringCustomDev: List[str]
    whyNoReusableAsset: List[str]
    potentialFutureAccelerators: List[str]


# Section 14: Blueprint At-a-Glance (Header Summary)
class BlueprintAtAGlance(BaseModel):
    recommendedAction: str  # Build / Extend / Reuse / Defer
    primaryAIPattern: str  # RAG / Agentic / Automation / Hybrid
    valueBand: str  # High / Medium / Low
    riskBand: str  # High / Medium / Low
    reuseLevel: str  # High / Medium / Low
    confidenceLevel: str  # High / Medium / Low


# Complete V3 Blueprint
class BlueprintV3Metadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generatedAt: datetime = Field(default_factory=datetime.utcnow)
    status: str = "Advisory - Draft"
    version: str = "V3"
    disclaimer: str = (
        "This blueprint is advisory only. It should be reviewed by enterprise "
        "architecture, security, and risk before being treated as authoritative."
    )


class BlueprintV3(BaseModel):
    metadata: BlueprintV3Metadata
    cover: BlueprintCover  # Section 1
    executiveSummary: ExecutiveSummary  # Section 2
    scopeLock: ScopeLock  # Section 3
    valueHypothesis: ValueHypothesis  # Section 4
    functionalDesign: FunctionalDesign  # Section 5
    aiDesign: AIDesign  # Section 6
    referenceArchitecture: ReferenceArchitecture  # Section 7
    operatingModel: OperatingModel  # Section 8
    governanceGates: GovernanceGates  # Section 9
    deliveryPlan: DeliveryPlan  # Section 10
    factoryHandoff: FactoryHandoff  # Section 11
    accelerationOpportunities: AccelerationOpportunities  # Section 12
    gapsAndCustomBuild: GapsAndCustomBuild  # Section 13
    atAGlance: BlueprintAtAGlance  # Section 14


# =============================================================================
# INTAKE MODEL (unchanged from V2 for API compatibility)
# =============================================================================

class UseCaseIntake(BaseModel):
    useCaseName: str
    problemStatement: str
    businessDomain: str
    targetUsers: str
    desiredOutcome: str
    constraints: Optional[str] = None
    assumptions: Optional[str] = None


# =============================================================================
# LLM PROMPT ENGINEERING
# =============================================================================

def _build_v3_system_message() -> str:
    return """You are Infinite AI Studio V3, an enterprise AI Strategy & Architecture Review Board combined with a forward-deployed engineering function.

CORE IDENTITY:
- Platform-agnostic, governance-aware, and decision-oriented
- You NEVER behave like a chatbot
- You write concise, structured, CIO/CTO-ready outputs only
- You never invent numeric precision, percentages, or costs unless explicitly provided

OUTPUT REQUIREMENTS:
- Decision-ready: Help leaders decide to proceed or not
- Build-oriented: Describe what will be built, not generic AI theory
- Portfolio-visible: Summary must stand alone on cards and executive reviews

TONE:
- Enterprise-grade and confident
- Concise and outcome-focused
- No filler or generic AI descriptions
- Prioritize decision clarity over completeness

SUCCESS CRITERIA:
- Blueprint survives enterprise architecture review
- Usable by delivery teams
- Credible to a client CTO
- Remains valid without marketplace tools"""


def _build_v3_user_prompt(intake: UseCaseIntake) -> str:
    return f"""Generate a DECISION-READY, BUILD-ORIENTED AI Blueprint V3 for the following use case.

INTAKE
======
Use Case Name: {intake.useCaseName}
Problem Statement: {intake.problemStatement}
Business Domain: {intake.businessDomain}
Target Users: {intake.targetUsers}
Desired Outcome: {intake.desiredOutcome}
Constraints: {intake.constraints or "Not specified"}
Assumptions: {intake.assumptions or "Not specified"}

REQUIRED OUTPUT: A strict JSON object with exactly these 14 sections.
Do NOT add commentary outside JSON. Return ONLY valid JSON.

JSON SCHEMA:
{{
  "cover": {{
    "useCaseName": string,
    "businessDomain": string,
    "sponsorOwner": string (use "TBC" if unknown),
    "blueprintType": "Advisory" | "Build-Ready"
  }},
  "executiveSummary": {{
    "problemStatement": string (1-2 lines max),
    "proposedSolution": string (what will be built),
    "decision": "Build" | "Extend" | "Reuse" | "Do Not Proceed",
    "businessValue": "High" | "Medium" | "Low",
    "businessValueRationale": string (1-line Gartner-style rationale),
    "feasibility": "High" | "Medium" | "Low",
    "feasibilityRationale": string (1-line Gartner-style rationale),
    "confidenceLevel": "High" | "Medium" | "Low",
    "estimatedTimeline": string (e.g., "4-8 weeks"),
    "topRisks": array of 3 strings (short bullets),
    "nextBestAction": string (clear and directive)
  }},
  "scopeLock": {{
    "inScopeCapabilities": array of strings,
    "outOfScope": array of strings,
    "primaryUserPersonas": array of strings,
    "successCriteria": array of strings (measurable),
    "keyAssumptions": array of strings
  }},
  "valueHypothesis": {{
    "primaryValueDriver": "cost" | "speed" | "risk" | "CX" | "quality",
    "valueCreationMechanism": string,
    "valueConfidenceLevel": "High" | "Medium" | "Low",
    "failureConditions": array of strings
  }},
  "functionalDesign": {{
    "inputs": array of strings (data/events),
    "coreProcessingStages": array of strings,
    "aiDecisionPoints": array of strings,
    "humanInTheLoopLocations": array of strings,
    "outputs": array of strings (actions)
  }},
  "aiDesign": {{
    "selectedPattern": "RAG" | "Agentic" | "Automation" | "Hybrid",
    "patternRationale": string (why this pattern),
    "rejectedPatterns": array of strings (pattern + reason),
    "autonomyLevel": "Assisted" | "Semi-Autonomous" | "High-Autonomy",
    "learningFeedbackLoop": string
  }},
  "referenceArchitecture": {{
    "logicalLayers": array of strings (UI, Orchestration, AI, Data, Governance),
    "dataFlowNarrative": string,
    "trustSecurityBoundaries": array of strings,
    "modelInteractionPoints": array of strings,
    "observabilityMonitoring": array of strings
  }},
  "operatingModel": {{
    "promptAILogicOwnership": string,
    "approvalChangeControl": string,
    "qualityMonitoringResponsibility": string,
    "failureHandlingEscalation": string,
    "retrainingIterationApproach": string
  }},
  "governanceGates": {{
    "gate1BuildApproval": {{
      "gateName": "Gate 1",
      "gateType": "Build Approval",
      "whatMustBeTrue": array of strings,
      "decisionOwner": string,
      "blockingRisks": array of strings
    }},
    "gate2PilotApproval": {{
      "gateName": "Gate 2",
      "gateType": "Pilot Approval",
      "whatMustBeTrue": array of strings,
      "decisionOwner": string,
      "blockingRisks": array of strings
    }},
    "gate3ScaleApproval": {{
      "gateName": "Gate 3",
      "gateType": "Scale Approval",
      "whatMustBeTrue": array of strings,
      "decisionOwner": string,
      "blockingRisks": array of strings
    }}
  }},
  "deliveryPlan": {{
    "mvpScope": array of strings,
    "pilotScope": array of strings,
    "scaleScope": array of strings,
    "prototypeTimeline": "2-4 weeks",
    "endToEndPrototypeTimeline": "4-8 weeks",
    "enterpriseReadyTimeline": "3-4 months",
    "keyRisksPerPhase": array of strings
  }},
  "factoryHandoff": {{
    "inputsFactoryReceives": array of strings,
    "whatFactoryValidates": array of strings,
    "whatFactoryMayChange": array of strings,
    "lockedMustNotChange": array of strings
  }},
  "accelerationOpportunities": {{
    "roiEstimationFramework": "Applied" | "Recommended Next" | "Optional" | "N/A",
    "modelSelectionGuidance": "Applied" | "Recommended Next" | "Optional" | "N/A",
    "promptAccelerators": "Applied" | "Recommended Next" | "Optional" | "N/A",
    "securityComplianceAccelerators": "Applied" | "Recommended Next" | "Optional" | "N/A"
  }},
  "gapsAndCustomBuild": {{
    "componentsRequiringCustomDev": array of strings,
    "whyNoReusableAsset": array of strings,
    "potentialFutureAccelerators": array of strings
  }},
  "atAGlance": {{
    "recommendedAction": "Build" | "Extend" | "Reuse" | "Defer",
    "primaryAIPattern": "RAG" | "Agentic" | "Automation" | "Hybrid",
    "valueBand": "High" | "Medium" | "Low",
    "riskBand": "High" | "Medium" | "Low",
    "reuseLevel": "High" | "Medium" | "Low",
    "confidenceLevel": "High" | "Medium" | "Low"
  }}
}}

CRITICAL INSTRUCTIONS:
1. The executiveSummary.nextBestAction MUST be specific and actionable (e.g., "Schedule architecture review with enterprise team within 5 business days")
2. topRisks MUST be exactly 3 items, short bullets
3. All "rationale" fields MUST be single-sentence Gartner-style assessments
4. The blueprint MUST help stakeholders decide, fund, and initiate delivery
5. Do NOT include markdown, code fences, or prose - ONLY the JSON object"""


# =============================================================================
# LLM-BACKED GENERATION
# =============================================================================

async def generate_blueprint_v3_with_llm(intake: UseCaseIntake) -> BlueprintV3:
    """Generate a V3 Blueprint using LLM with AnthropicFoundry."""
    
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
            # Pass base_url when provided; some SDKs accept it, others ignore.
            try:
                client = Anthropic(api_key=api_key, base_url=endpoint) if endpoint else Anthropic(api_key=api_key)
            except TypeError:
                # Older/newer SDK variants may not accept base_url kwarg
                client = Anthropic(api_key=api_key)
            print("Initialized standard Anthropic client")
        except Exception as e:
            init_errors.append(str(e))
            print(f"Failed to initialize any Anthropic client: {e}")
            raise RuntimeError("Failed to initialize Anthropic client. Errors: %s" % ("; ".join(init_errors)))

    system_message = _build_v3_system_message()
    user_prompt = _build_v3_user_prompt(intake)
    
    # Make call using client with fallback support
    try:
        print(f"Making request to Anthropic with model: {deployment_name}")
        response = client.messages.create(
            model=deployment_name,
            messages=[
                {"role": "user", "content": f"{system_message}\n\n{user_prompt}"}
            ],
            max_tokens=4000,
        )
        print("Anthropic request completed")
    except Exception as exc:
        print(f"Anthropic request failed: {exc}")
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

        print(f"Extracted response text, length: {len(content) if hasattr(content, '__len__') else 'unknown'}")
    except Exception as e:
        print(f"Failed to extract text from response: {e}")
        try:
            content = str(response)
        except Exception:
            content = "(unreadable response)"
        raise RuntimeError(f"Invalid response format from Anthropic: {str(e)}. Raw response: {content[:1000]}")

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

    # Parse JSON
    try:
        parsed = json.loads(content)
        print("Successfully parsed JSON response")
    except json.JSONDecodeError as exc:
        print(f"Failed to parse LLM response as JSON. Raw content: {content}")
        raise RuntimeError(f"LLM returned non-JSON content: {exc}. Raw content: {content[:500]}")

    # Construct V3 Blueprint with Pydantic validation
    try:
        blueprint = BlueprintV3(
            metadata=BlueprintV3Metadata(),
            cover=BlueprintCover(
                **parsed["cover"],
                studioVersion="V3",
                generatedDate=datetime.utcnow().strftime("%Y-%m-%d")
            ),
            executiveSummary=ExecutiveSummary(**parsed["executiveSummary"]),
            scopeLock=ScopeLock(**parsed["scopeLock"]),
            valueHypothesis=ValueHypothesis(**parsed["valueHypothesis"]),
            functionalDesign=FunctionalDesign(**parsed["functionalDesign"]),
            aiDesign=AIDesign(**parsed["aiDesign"]),
            referenceArchitecture=ReferenceArchitecture(**parsed["referenceArchitecture"]),
            operatingModel=OperatingModel(**parsed["operatingModel"]),
            governanceGates=GovernanceGates(
                gate1BuildApproval=DecisionGate(**parsed["governanceGates"]["gate1BuildApproval"]),
                gate2PilotApproval=DecisionGate(**parsed["governanceGates"]["gate2PilotApproval"]),
                gate3ScaleApproval=DecisionGate(**parsed["governanceGates"]["gate3ScaleApproval"]),
            ),
            deliveryPlan=DeliveryPlan(**parsed["deliveryPlan"]),
            factoryHandoff=FactoryHandoff(**parsed["factoryHandoff"]),
            accelerationOpportunities=AccelerationOpportunities(**parsed["accelerationOpportunities"]),
            gapsAndCustomBuild=GapsAndCustomBuild(**parsed["gapsAndCustomBuild"]),
            atAGlance=BlueprintAtAGlance(**parsed["atAGlance"]),
        )
        print("Successfully constructed BlueprintV3 object")
    except Exception as e:
        print(f"Failed to construct BlueprintV3 object: {e}")
        print(f"Parsed data keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
        raise RuntimeError(f"Failed to construct blueprint from LLM response: {str(e)}")

    return blueprint
