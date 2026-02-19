"""
Blueprint Refinement Service - Dependency-Aware Intelligent Regeneration
=========================================================================
Enables intelligent blueprint refinement that:
- Tracks dependencies between sections
- Only regenerates impacted sections
- Preserves unchanged sections
- Provides detailed change summaries
"""

import os
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from dotenv import load_dotenv
from pydantic import BaseModel, Field


from blueprint_service_v3 import (
    BlueprintV3, BlueprintV3Metadata, BlueprintCover, ExecutiveSummary,
    ScopeLock, ValueHypothesis, FunctionalDesign, AIDesign, 
    ReferenceArchitecture, OperatingModel, GovernanceGates, DecisionGate,
    DeliveryPlan, FactoryHandoff, AccelerationOpportunities, 
    GapsAndCustomBuild, BlueprintAtAGlance
)

load_dotenv()


# =============================================================================
# REFINEMENT MODELS
# =============================================================================

class ChangeFactorType(str, Enum):
    BUDGET_COST = "budget_cost"
    COMPLIANCE_SECURITY = "compliance_security"
    SCOPE_CHANGE = "scope_change"
    TARGET_USERS = "target_users"
    RISK_TOLERANCE = "risk_tolerance"
    NEW_CONTEXT = "new_context"
    TIMELINE = "timeline"
    OTHER = "other"


class ChangeFactor(BaseModel):
    type: ChangeFactorType
    description: str


class RefinementRequest(BaseModel):
    """Input for blueprint refinement"""
    previousBlueprint: Dict[str, Any]  # The existing blueprint JSON
    changeFactors: List[ChangeFactor]  # What factors are changing (max 3)
    additionalContext: Optional[str] = None  # Free-text context
    overrideSections: Optional[List[str]] = None  # Advanced mode: user-specified sections to regenerate


class ScoreDelta(BaseModel):
    """Represents a change in a score/rating"""
    field: str  # e.g., "businessValue", "feasibility", "riskBand"
    previousValue: str
    newValue: str
    direction: str  # "up", "down", "unchanged"
    

class DecisionDelta(BaseModel):
    """Represents a change in a key decision"""
    field: str  # e.g., "decision", "selectedPattern", "recommendedAction"
    previousValue: str
    newValue: str
    reasoning: str


class SectionChange(BaseModel):
    """Represents changes to a blueprint section"""
    sectionName: str
    wasRegenerated: bool
    changeHighlights: List[str] = []  # Key changes in this section


class ChangeSummary(BaseModel):
    """Summary of all changes made during refinement"""
    refinementId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    changeFactors: List[str]  # What the user changed
    aiReasoning: str  # Why changes were made
    impactedSections: List[str]  # Which sections were regenerated
    preservedSections: List[str]  # Which sections were kept unchanged
    sectionChanges: List[SectionChange]  # Detailed changes per section
    scoreDeltas: List[ScoreDelta]  # Changes to scores
    decisionDeltas: List[DecisionDelta]  # Changes to key decisions
    factoryImpact: bool  # Does this affect Factory outputs?
    factoryImpactReason: Optional[str] = None


class RefinementResponse(BaseModel):
    """Response from blueprint refinement"""
    blueprint: Dict[str, Any]  # The updated blueprint
    changeSummary: ChangeSummary
    newVersion: int


# =============================================================================
# DEPENDENCY MAPPING
# =============================================================================

# Defines how sections depend on each other
SECTION_DEPENDENCIES = {
    "executiveSummary": ["cover", "valueHypothesis", "aiDesign", "deliveryPlan"],
    "scopeLock": ["cover", "functionalDesign"],
    "valueHypothesis": ["executiveSummary", "scopeLock"],
    "functionalDesign": ["scopeLock", "aiDesign"],
    "aiDesign": ["scopeLock", "functionalDesign", "valueHypothesis"],
    "referenceArchitecture": ["aiDesign", "functionalDesign", "scopeLock"],
    "operatingModel": ["aiDesign", "referenceArchitecture"],
    "governanceGates": ["scopeLock", "valueHypothesis", "deliveryPlan"],
    "deliveryPlan": ["scopeLock", "aiDesign", "referenceArchitecture"],
    "factoryHandoff": ["functionalDesign", "aiDesign", "scopeLock"],
    "accelerationOpportunities": ["aiDesign", "referenceArchitecture"],
    "gapsAndCustomBuild": ["aiDesign", "referenceArchitecture", "accelerationOpportunities"],
    "atAGlance": ["executiveSummary", "aiDesign", "valueHypothesis"],
}

# Maps change factors to directly impacted sections
FACTOR_TO_SECTIONS = {
    ChangeFactorType.BUDGET_COST: ["valueHypothesis", "deliveryPlan", "executiveSummary", "atAGlance"],
    ChangeFactorType.COMPLIANCE_SECURITY: ["referenceArchitecture", "operatingModel", "governanceGates", "scopeLock"],
    ChangeFactorType.SCOPE_CHANGE: ["scopeLock", "functionalDesign", "deliveryPlan", "executiveSummary", "atAGlance"],
    ChangeFactorType.TARGET_USERS: ["scopeLock", "functionalDesign", "valueHypothesis"],
    ChangeFactorType.RISK_TOLERANCE: ["executiveSummary", "governanceGates", "valueHypothesis", "atAGlance"],
    ChangeFactorType.TIMELINE: ["deliveryPlan", "executiveSummary", "governanceGates"],
    ChangeFactorType.NEW_CONTEXT: ["executiveSummary", "scopeLock", "aiDesign", "atAGlance"],
    ChangeFactorType.OTHER: ["executiveSummary", "scopeLock", "atAGlance"],
}


def calculate_impacted_sections(change_factors: List[ChangeFactor], override_sections: Optional[List[str]] = None) -> List[str]:
    """Calculate which sections need to be regenerated based on change factors"""
    if override_sections:
        return override_sections
    
    impacted = set()
    
    # Get directly impacted sections
    for factor in change_factors:
        direct_sections = FACTOR_TO_SECTIONS.get(factor.type, [])
        impacted.update(direct_sections)
    
    # Add dependent sections (cascade)
    to_process = list(impacted)
    while to_process:
        section = to_process.pop()
        for dep_section, dependencies in SECTION_DEPENDENCIES.items():
            if section in dependencies and dep_section not in impacted:
                impacted.add(dep_section)
                to_process.append(dep_section)
    
    # Always include atAGlance as it summarizes everything
    impacted.add("atAGlance")
    
    return list(impacted)


def get_preserved_sections(impacted: List[str]) -> List[str]:
    """Get list of sections that won't be changed"""
    all_sections = [
        "cover", "executiveSummary", "scopeLock", "valueHypothesis", 
        "functionalDesign", "aiDesign", "referenceArchitecture", 
        "operatingModel", "governanceGates", "deliveryPlan", 
        "factoryHandoff", "accelerationOpportunities", "gapsAndCustomBuild", "atAGlance"
    ]
    return [s for s in all_sections if s not in impacted]


# =============================================================================
# LLM PROMPTS FOR REFINEMENT
# =============================================================================

def _build_refinement_system_message() -> str:
    return """You are Infinite AI Studio V3 Refinement Engine, specialized in intelligent blueprint updates.

CORE PRINCIPLES:
1. PRESERVE what doesn't need to change - maintain consistency
2. REGENERATE only impacted sections with full quality
3. PROPAGATE changes logically through dependencies
4. EXPLAIN your reasoning clearly

OUTPUT REQUIREMENTS:
- Enterprise-grade quality on regenerated sections
- Clear reasoning for why changes were made
- Accurate score and decision deltas
- No hallucinated data - only infer from provided context

CRITICAL: You are updating an EXISTING blueprint, not creating from scratch.
The user's changes should be reflected, but unaffected sections must remain unchanged."""


def _build_refinement_prompt(
    previous_blueprint: Dict[str, Any],
    change_factors: List[ChangeFactor],
    additional_context: Optional[str],
    impacted_sections: List[str],
    preserved_sections: List[str]
) -> str:
    factors_text = "\n".join([f"- {f.type.value}: {f.description}" for f in change_factors])
    
    # Only include impacted sections from previous blueprint to reduce token usage
    impacted_data = {}
    for section in impacted_sections:
        if section in previous_blueprint:
            impacted_data[section] = previous_blueprint[section]
    
    # Include key context from preserved sections (just summaries)
    context_summary = {
        "useCaseName": previous_blueprint.get("cover", {}).get("useCaseName", ""),
        "businessDomain": previous_blueprint.get("cover", {}).get("businessDomain", ""),
        "currentDecision": previous_blueprint.get("executiveSummary", {}).get("decision", ""),
        "currentPattern": previous_blueprint.get("aiDesign", {}).get("selectedPattern", ""),
        "currentValueBand": previous_blueprint.get("atAGlance", {}).get("valueBand", ""),
        "currentRiskBand": previous_blueprint.get("atAGlance", {}).get("riskBand", ""),
    }
    
    return f"""BLUEPRINT REFINEMENT REQUEST
============================

USE CASE CONTEXT:
- Name: {context_summary['useCaseName']}
- Domain: {context_summary['businessDomain']}
- Current Decision: {context_summary['currentDecision']}
- Current Pattern: {context_summary['currentPattern']}
- Current Value: {context_summary['currentValueBand']}
- Current Risk: {context_summary['currentRiskBand']}

CHANGE FACTORS (what is changing):
{factors_text}

ADDITIONAL CONTEXT:
{additional_context or "None provided"}

SECTIONS TO REGENERATE: {json.dumps(impacted_sections)}

CURRENT DATA FOR IMPACTED SECTIONS:
{json.dumps(impacted_data, indent=2)}

OUTPUT REQUIRED - Return a JSON object with:
{{
  "updatedSections": {{
    // Only regenerate these specific sections with the changes applied
  }},
  "changeSummary": {{
    "aiReasoning": "Brief explanation of changes made",
    "scoreDeltas": [
      {{"field": "businessValue", "previousValue": "High", "newValue": "Medium", "direction": "down"}}
    ],
    "decisionDeltas": [
      {{"field": "selectedPattern", "previousValue": "RAG", "newValue": "Hybrid", "reasoning": "Why changed"}}
    ],
    "factoryImpact": true,
    "factoryImpactReason": "Why factory is impacted (if applicable)"
  }}
}}

SECTION SCHEMAS:
- executiveSummary: problemStatement, proposedSolution, decision (Build/Extend/Reuse/Do Not Proceed), businessValue, businessValueRationale, feasibility, feasibilityRationale, confidenceLevel, estimatedTimeline, topRisks (array of 3), nextBestAction
- scopeLock: inScopeCapabilities, outOfScope, primaryUserPersonas, successCriteria, keyAssumptions (all arrays)
- valueHypothesis: primaryValueDriver (cost/speed/risk/CX/quality), valueCreationMechanism, valueConfidenceLevel, failureConditions (array)
- aiDesign: selectedPattern (RAG/Agentic/Automation/Hybrid), patternRationale, rejectedPatterns (array), autonomyLevel (Assisted/Semi-Autonomous/High-Autonomy), learningFeedbackLoop
- atAGlance: recommendedAction (Build/Extend/Reuse/Defer), primaryAIPattern, valueBand, riskBand, reuseLevel, confidenceLevel

Return ONLY valid JSON. Include only scoreDeltas/decisionDeltas if values actually changed."""


# =============================================================================
# REFINEMENT ENGINE
# =============================================================================

async def refine_blueprint(request: RefinementRequest) -> RefinementResponse:
    """Refine a blueprint based on change factors"""
    
    # Check for Anthropic configuration (try both Foundry and regular Anthropic)
    api_key = os.environ.get("ANTHROPIC_FOUNDRY_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    endpoint = os.environ.get("ANTHROPIC_FOUNDRY_ENDPOINT")
    deployment_name = os.environ.get("ANTHROPIC_FOUNDRY_DEPLOYMENT_NAME") or "claude-3-5-sonnet-20241022"
    
    if not api_key:
        raise RuntimeError("Anthropic API key is not configured. Set ANTHROPIC_FOUNDRY_API_KEY or ANTHROPIC_API_KEY in backend/.env")
    
    # Calculate impacted sections
    impacted_sections = calculate_impacted_sections(
        request.changeFactors, 
        request.overrideSections
    )
    preserved_sections = get_preserved_sections(impacted_sections)
    
    # Extract previous version for delta calculation
    prev_blueprint = request.previousBlueprint
    prev_version = prev_blueprint.get("metadata", {}).get("version", 1)
    
    # Parse version number
    if isinstance(prev_version, str):
        if prev_version.startswith("V"):
            prev_version = int(prev_version[1:]) if prev_version[1:].isdigit() else 1
        elif prev_version.isdigit():
            prev_version = int(prev_version)
        else:
            prev_version = 1

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
                print(f"Initialized AnthropicFoundry client for refinement with endpoint: {endpoint}")
            except Exception as e:
                init_errors.append(f"AnthropicFoundry init failed: {e}")
                print(f"AnthropicFoundry initialization failed for refinement, will try fallback: {e}")
        except ImportError:
            init_errors.append("AnthropicFoundry is not available in the installed anthropic package")
            print("AnthropicFoundry class not found for refinement; will try standard Anthropic client")

    if client is None:
        try:
            from anthropic import Anthropic
            # Pass base_url when provided; some SDKs accept it, others ignore.
            try:
                client = Anthropic(api_key=api_key, base_url=endpoint) if endpoint else Anthropic(api_key=api_key)
            except TypeError:
                # Older/newer SDK variants may not accept base_url kwarg
                client = Anthropic(api_key=api_key)
            print("Initialized standard Anthropic client for refinement")
        except Exception as e:
            init_errors.append(str(e))
            print(f"Failed to initialize any Anthropic client for refinement: {e}")
            raise RuntimeError("Failed to initialize Anthropic client. Errors: %s" % ("; ".join(init_errors)))

    system_message = _build_refinement_system_message()
    user_prompt = _build_refinement_prompt(
        prev_blueprint,
        request.changeFactors,
        request.additionalContext,
        impacted_sections,
        preserved_sections
    )
    
    # Make call using client with fallback support
    try:
        print(f"Making refinement request to Anthropic with model: {deployment_name}")
        response = client.messages.create(
            model=deployment_name,
            messages=[
                {"role": "user", "content": f"{system_message}\n\n{user_prompt}"}
            ],
            max_tokens=4000,
        )
        print("Anthropic refinement request completed")
    except Exception as exc:
        print(f"Anthropic refinement request failed: {exc}")
        raise RuntimeError(f"Failed to call Anthropic API for refinement: {str(exc)}")

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

        print(f"Extracted refinement response text, length: {len(content) if hasattr(content, '__len__') else 'unknown'}")
    except Exception as e:
        print(f"Failed to extract text from refinement response: {e}")
        try:
            content = str(response)
        except Exception:
            content = "(unreadable response)"
        raise RuntimeError(f"Invalid response format from Anthropic: {str(e)}. Raw response: {content[:1000]}")

    # Clean up response
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
        print("Successfully parsed refinement JSON response")
    except json.JSONDecodeError as exc:
        print(f"Failed to parse refinement LLM response as JSON. Raw content: {content}")
        raise RuntimeError(f"LLM returned non-JSON content: {exc}. Raw content: {content[:500]}")
    
    # Get updated sections from response
    updated_sections = parsed.get("updatedSections", parsed.get("updatedBlueprint", {}))
    summary_data = parsed.get("changeSummary", {})
    
    # Merge updated sections into full blueprint (preserve unchanged sections)
    updated_bp = dict(prev_blueprint)  # Copy all original data
    for section_name, section_data in updated_sections.items():
        if section_name in impacted_sections:
            updated_bp[section_name] = section_data
    
    # Calculate new version
    new_version = prev_version + 1
    
    # Update metadata
    updated_bp["metadata"] = {
        "id": prev_blueprint.get("metadata", {}).get("id", str(uuid.uuid4())),
        "generatedAt": datetime.utcnow().isoformat(),
        "status": "Advisory - Draft",
        "version": new_version,
        "disclaimer": prev_blueprint.get("metadata", {}).get("disclaimer", "")
    }
    
    # Build section changes from impacted sections
    section_changes = []
    for section in impacted_sections:
        section_changes.append(SectionChange(
            sectionName=section,
            wasRegenerated=True,
            changeHighlights=[]
        ))
    
    # Build change summary
    change_summary = ChangeSummary(
        changeFactors=[f"{f.type.value}: {f.description}" for f in request.changeFactors],
        aiReasoning=summary_data.get("aiReasoning", "Blueprint refined based on provided change factors."),
        impactedSections=impacted_sections,
        preservedSections=preserved_sections,
        sectionChanges=section_changes,
        scoreDeltas=[
            ScoreDelta(**sd) for sd in summary_data.get("scoreDeltas", [])
        ],
        decisionDeltas=[
            DecisionDelta(**dd) for dd in summary_data.get("decisionDeltas", [])
        ],
        factoryImpact=summary_data.get("factoryImpact", False),
        factoryImpactReason=summary_data.get("factoryImpactReason")
    )
    
    return RefinementResponse(
        blueprint=updated_bp,
        changeSummary=change_summary,
        newVersion=new_version
    )


async def preview_impact(change_factors: List[ChangeFactor], override_sections: Optional[List[str]] = None) -> Dict[str, Any]:
    """Preview which sections will be impacted without running refinement"""
    impacted = calculate_impacted_sections(change_factors, override_sections)
    preserved = get_preserved_sections(impacted)
    
    return {
        "impactedSections": impacted,
        "preservedSections": preserved,
        "factorMapping": {
            f.type.value: FACTOR_TO_SECTIONS.get(f.type, [])
            for f in change_factors
        }
    }
