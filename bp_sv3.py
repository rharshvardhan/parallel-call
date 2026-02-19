"""
Blueprint Service V3 - Parallel API Calls for faster generation
================================================================
Splits 14 sections into 3 groups, fires them simultaneously.
Expected time: ~20-25s instead of 65s.
"""

import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import List, Optional

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


# =============================================================================
# PYDANTIC MODELS — 14 Sections (unchanged)
# =============================================================================

class BlueprintCover(BaseModel):
    useCaseName: str
    businessDomain: str
    sponsorOwner: str = "TBC"
    blueprintType: str
    studioVersion: str = "V3"
    generatedDate: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))

class ExecutiveSummary(BaseModel):
    problemStatement: str
    proposedSolution: str
    decision: str
    businessValue: str
    businessValueRationale: str
    feasibility: str
    feasibilityRationale: str
    confidenceLevel: str
    estimatedTimeline: str
    topRisks: List[str]
    nextBestAction: str

class ScopeLock(BaseModel):
    inScopeCapabilities: List[str]
    outOfScope: List[str]
    primaryUserPersonas: List[str]
    successCriteria: List[str]
    keyAssumptions: List[str]

class ValueHypothesis(BaseModel):
    primaryValueDriver: str
    valueCreationMechanism: str
    valueConfidenceLevel: str
    failureConditions: List[str]

class FunctionalDesign(BaseModel):
    inputs: List[str]
    coreProcessingStages: List[str]
    aiDecisionPoints: List[str]
    humanInTheLoopLocations: List[str]
    outputs: List[str]

class AIDesign(BaseModel):
    selectedPattern: str
    patternRationale: str
    rejectedPatterns: List[str]
    autonomyLevel: str
    learningFeedbackLoop: str

class ReferenceArchitecture(BaseModel):
    logicalLayers: List[str]
    dataFlowNarrative: str
    trustSecurityBoundaries: List[str]
    modelInteractionPoints: List[str]
    observabilityMonitoring: List[str]

class OperatingModel(BaseModel):
    promptAILogicOwnership: str
    approvalChangeControl: str
    qualityMonitoringResponsibility: str
    failureHandlingEscalation: str
    retrainingIterationApproach: str

class DecisionGate(BaseModel):
    gateName: str
    gateType: str
    whatMustBeTrue: List[str]
    decisionOwner: str
    blockingRisks: List[str]

class GovernanceGates(BaseModel):
    gate1BuildApproval: DecisionGate
    gate2PilotApproval: DecisionGate
    gate3ScaleApproval: DecisionGate

class DeliveryPlan(BaseModel):
    mvpScope: List[str]
    pilotScope: List[str]
    scaleScope: List[str]
    prototypeTimeline: str
    endToEndPrototypeTimeline: str
    enterpriseReadyTimeline: str
    keyRisksPerPhase: List[str]

class FactoryHandoff(BaseModel):
    inputsFactoryReceives: List[str]
    whatFactoryValidates: List[str]
    whatFactoryMayChange: List[str]
    lockedMustNotChange: List[str]

class AccelerationOpportunities(BaseModel):
    roiEstimationFramework: str
    modelSelectionGuidance: str
    promptAccelerators: str
    securityComplianceAccelerators: str

class GapsAndCustomBuild(BaseModel):
    componentsRequiringCustomDev: List[str]
    whyNoReusableAsset: List[str]
    potentialFutureAccelerators: List[str]

class BlueprintAtAGlance(BaseModel):
    recommendedAction: str
    primaryAIPattern: str
    valueBand: str
    riskBand: str
    reuseLevel: str
    confidenceLevel: str

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
    cover: BlueprintCover
    executiveSummary: ExecutiveSummary
    scopeLock: ScopeLock
    valueHypothesis: ValueHypothesis
    functionalDesign: FunctionalDesign
    aiDesign: AIDesign
    referenceArchitecture: ReferenceArchitecture
    operatingModel: OperatingModel
    governanceGates: GovernanceGates
    deliveryPlan: DeliveryPlan
    factoryHandoff: FactoryHandoff
    accelerationOpportunities: AccelerationOpportunities
    gapsAndCustomBuild: GapsAndCustomBuild
    atAGlance: BlueprintAtAGlance


# =============================================================================
# INTAKE MODEL
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
# SHARED IDENTITY — injected into every group's system prompt
# =============================================================================

SHARED_IDENTITY = """You are Infinite AI Studio V3, an enterprise AI Strategy & Architecture Review Board.

CORE IDENTITY:
- Platform-agnostic, governance-aware, and decision-oriented
- You NEVER behave like a chatbot
- You write concise, structured, CIO/CTO-ready outputs only
- You never invent numeric precision, percentages, or costs unless explicitly provided

TONE:
- Enterprise-grade, confident, outcome-focused
- No filler or generic AI descriptions

OUTPUT FORMAT:
Return ONLY a valid JSON object — no markdown, no code fences, no prose outside the JSON."""


# =============================================================================
# GROUP SYSTEM PROMPTS — each group has its own schema slice
# =============================================================================

# Group 1: Strategy & Summary (cover, executiveSummary, scopeLock, valueHypothesis, atAGlance)
SYSTEM_PROMPT_GROUP1 = SHARED_IDENTITY + """

Generate ONLY these 5 sections as a single JSON object:

{
  "cover": {
    "useCaseName": string,
    "businessDomain": string,
    "sponsorOwner": string,
    "blueprintType": "Advisory" | "Build-Ready"
  },
  "executiveSummary": {
    "problemStatement": string,
    "proposedSolution": string,
    "decision": "Build" | "Extend" | "Reuse" | "Do Not Proceed",
    "businessValue": "High" | "Medium" | "Low",
    "businessValueRationale": string,
    "feasibility": "High" | "Medium" | "Low",
    "feasibilityRationale": string,
    "confidenceLevel": "High" | "Medium" | "Low",
    "estimatedTimeline": string,
    "topRisks": [string, string, string],
    "nextBestAction": string
  },
  "scopeLock": {
    "inScopeCapabilities": [string],
    "outOfScope": [string],
    "primaryUserPersonas": [string],
    "successCriteria": [string],
    "keyAssumptions": [string]
  },
  "valueHypothesis": {
    "primaryValueDriver": "cost" | "speed" | "risk" | "CX" | "quality",
    "valueCreationMechanism": string,
    "valueConfidenceLevel": "High" | "Medium" | "Low",
    "failureConditions": [string]
  },
  "atAGlance": {
    "recommendedAction": "Build" | "Extend" | "Reuse" | "Defer",
    "primaryAIPattern": "RAG" | "Agentic" | "Automation" | "Hybrid",
    "valueBand": "High" | "Medium" | "Low",
    "riskBand": "High" | "Medium" | "Low",
    "reuseLevel": "High" | "Medium" | "Low",
    "confidenceLevel": "High" | "Medium" | "Low"
  }
}

RULES:
- topRisks must be exactly 3 short bullet strings
- nextBestAction must be specific and actionable
- All rationale fields must be a single Gartner-style sentence"""


# Group 2: Technical Design (functionalDesign, aiDesign, referenceArchitecture, operatingModel)
SYSTEM_PROMPT_GROUP2 = SHARED_IDENTITY + """

Generate ONLY these 4 sections as a single JSON object:

{
  "functionalDesign": {
    "inputs": [string],
    "coreProcessingStages": [string],
    "aiDecisionPoints": [string],
    "humanInTheLoopLocations": [string],
    "outputs": [string]
  },
  "aiDesign": {
    "selectedPattern": "RAG" | "Agentic" | "Automation" | "Hybrid",
    "patternRationale": string,
    "rejectedPatterns": [string],
    "autonomyLevel": "Assisted" | "Semi-Autonomous" | "High-Autonomy",
    "learningFeedbackLoop": string
  },
  "referenceArchitecture": {
    "logicalLayers": [string],
    "dataFlowNarrative": string,
    "trustSecurityBoundaries": [string],
    "modelInteractionPoints": [string],
    "observabilityMonitoring": [string]
  },
  "operatingModel": {
    "promptAILogicOwnership": string,
    "approvalChangeControl": string,
    "qualityMonitoringResponsibility": string,
    "failureHandlingEscalation": string,
    "retrainingIterationApproach": string
  }
}"""


# Group 3: Delivery & Governance (governanceGates, deliveryPlan, factoryHandoff, accelerationOpportunities, gapsAndCustomBuild)
SYSTEM_PROMPT_GROUP3 = SHARED_IDENTITY + """

Generate ONLY these 5 sections as a single JSON object:

{
  "governanceGates": {
    "gate1BuildApproval": {
      "gateName": "Gate 1",
      "gateType": "Build Approval",
      "whatMustBeTrue": [string],
      "decisionOwner": string,
      "blockingRisks": [string]
    },
    "gate2PilotApproval": {
      "gateName": "Gate 2",
      "gateType": "Pilot Approval",
      "whatMustBeTrue": [string],
      "decisionOwner": string,
      "blockingRisks": [string]
    },
    "gate3ScaleApproval": {
      "gateName": "Gate 3",
      "gateType": "Scale Approval",
      "whatMustBeTrue": [string],
      "decisionOwner": string,
      "blockingRisks": [string]
    }
  },
  "deliveryPlan": {
    "mvpScope": [string],
    "pilotScope": [string],
    "scaleScope": [string],
    "prototypeTimeline": string,
    "endToEndPrototypeTimeline": string,
    "enterpriseReadyTimeline": string,
    "keyRisksPerPhase": [string]
  },
  "factoryHandoff": {
    "inputsFactoryReceives": [string],
    "whatFactoryValidates": [string],
    "whatFactoryMayChange": [string],
    "lockedMustNotChange": [string]
  },
  "accelerationOpportunities": {
    "roiEstimationFramework": "Applied" | "Recommended Next" | "Optional" | "N/A",
    "modelSelectionGuidance": "Applied" | "Recommended Next" | "Optional" | "N/A",
    "promptAccelerators": "Applied" | "Recommended Next" | "Optional" | "N/A",
    "securityComplianceAccelerators": "Applied" | "Recommended Next" | "Optional" | "N/A"
  },
  "gapsAndCustomBuild": {
    "componentsRequiringCustomDev": [string],
    "whyNoReusableAsset": [string],
    "potentialFutureAccelerators": [string]
  }
}"""


# =============================================================================
# HELPERS
# =============================================================================

def _build_user_prompt(intake: UseCaseIntake) -> str:
    return f"""Generate the blueprint sections for this use case:

Use Case: {intake.useCaseName}
Problem: {intake.problemStatement}
Domain: {intake.businessDomain}
Users: {intake.targetUsers}
Outcome: {intake.desiredOutcome}
Constraints: {intake.constraints or "None"}
Assumptions: {intake.assumptions or "None"}"""


def _get_async_client() -> anthropic.AsyncAnthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set in environment.")
    return anthropic.AsyncAnthropic(api_key=api_key)


def _parse_json(raw: str, group: str) -> dict:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Group {group} returned invalid JSON: {e}\nRaw (first 500 chars): {cleaned[:500]}")


def _build_blueprint(parsed: dict) -> BlueprintV3:
    try:
        return BlueprintV3(
            metadata=BlueprintV3Metadata(),
            cover=BlueprintCover(
                **parsed["cover"],
                studioVersion="V3",
                generatedDate=datetime.utcnow().strftime("%Y-%m-%d"),
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
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"Blueprint construction failed — missing or invalid field: {e}")


# =============================================================================
# PARALLEL LLM CALLS
# =============================================================================

async def _call_group(
    client: anthropic.AsyncAnthropic,
    model: str,
    system: str,
    user: str,
    group_name: str,
) -> dict:
    """Single async API call for one group of sections."""
    response = await client.messages.create(
        model=model,
        max_tokens=2000,   # each group needs ~1/3 of original tokens
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return _parse_json(response.content[0].text, group_name)


async def generate_blueprint_v3(intake: UseCaseIntake) -> BlueprintV3:
    """
    Generate a V3 Blueprint using 3 parallel Claude calls.
    All 3 groups fire simultaneously — total time ≈ slowest group (~20-25s).
    """
    client = _get_async_client()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    user_prompt = _build_user_prompt(intake)

    # Fire all 3 groups at the same time
    group1, group2, group3 = await asyncio.gather(
        _call_group(client, model, SYSTEM_PROMPT_GROUP1, user_prompt, "Group1"),
        _call_group(client, model, SYSTEM_PROMPT_GROUP2, user_prompt, "Group2"),
        _call_group(client, model, SYSTEM_PROMPT_GROUP3, user_prompt, "Group3"),
    )

    # Merge all 3 dicts into one and build the blueprint
    parsed = {**group1, **group2, **group3}
    return _build_blueprint(parsed)