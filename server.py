from fastapi import FastAPI, APIRouter
from fastapi.responses import Response
from dotenv import load_dotenv
from fastapi import HTTPException
from blueprint_service import UseCaseIntake, Blueprint, generate_blueprint_with_llm
from blueprint_service_v3 import BlueprintV3, generate_blueprint_v3_with_llm, UseCaseIntake as UseCaseIntakeV3
from factory_service import (
    FactoryStatus,
    KitMetadata,
    GenerateKitRequest,
    RegenerateModuleRequest,
    AddEndpointRequest,
    generate_starter_kit,
    regenerate_module,
    add_endpoint_to_kit,
)
from refinement_service import (
    RefinementRequest,
    RefinementResponse,
    ChangeFactor,
    ChangeFactorType,
    refine_blueprint,
    preview_impact,
)

from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from opportunity_service import OpportunityClusterRequest, OpportunityResponse, generate_opportunity_clusters

import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection setup
MONGO_URI = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client["backend_db"]

# Collections
portfolio_collection = db["portfolio"]
status_checks_collection = db["status_checks"]
factory_status_collection = db["factory_status"]
kits_collection = db["kits"]
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Test MongoDB connection on startup
    try:
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
    yield
    # Close MongoDB connection on shutdown
    client.close()

# Create the main app without a prefix
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    try:
        status_dict = input.model_dump()
        status_obj = StatusCheck(**status_dict)
        
        # Convert to dict and serialize datetime to ISO string for storage
        doc = status_obj.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        
        # Store in MongoDB
        status_checks_collection.insert_one(doc)
        return status_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



@api_router.post("/blueprints/generate", response_model=Blueprint)
async def generate_blueprint_endpoint(intake: UseCaseIntake):
    try:
        blueprint = await generate_blueprint_with_llm(intake)
        return blueprint
    except RuntimeError as exc:
        logger.error(f"Blueprint generation configuration error: {exc}")
        raise HTTPException(status_code=500, detail="Blueprint generation is temporarily unavailable. Please contact the platform owner.")
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error during blueprint generation")
        raise HTTPException(status_code=500, detail="Unexpected error while generating blueprint. Advisory blueprint could not be produced.")


@api_router.post("/opportunities/intel", response_model=OpportunityResponse)
async def get_opportunity_intel(req: OpportunityClusterRequest):
    try:
        return await generate_opportunity_clusters(req)
    except RuntimeError as exc:
        logger.error(f"Opportunity intelligence configuration error: {exc}")
        raise HTTPException(status_code=500, detail="AI opportunity intelligence is temporarily unavailable. Please contact the platform owner.")
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error during opportunity intelligence generation")
        raise HTTPException(status_code=500, detail="Unexpected error while generating opportunity clusters.")


# V3 Blueprint Generation Endpoint
@api_router.post("/blueprints/v3/generate", response_model=BlueprintV3)
async def generate_blueprint_v3_endpoint(intake: UseCaseIntakeV3):
    """
    V3 Blueprint Generation - Decision-Ready, Build-Oriented
    
    Generates a comprehensive 14-section blueprint designed for:
    - Executive decision-making
    - Portfolio visibility
    - Factory handoff
    """
    try:
        blueprint = await generate_blueprint_v3_with_llm(intake)
        return blueprint
    except RuntimeError as exc:
        logger.error(f"V3 Blueprint generation configuration error: {exc}")
        raise HTTPException(status_code=500, detail="V3 Blueprint generation is temporarily unavailable. Please contact the platform owner.")
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error during V3 blueprint generation")
        raise HTTPException(status_code=500, detail="Unexpected error while generating V3 blueprint.")


# =============================================================================
# BLUEPRINT REFINEMENT ENDPOINTS
# =============================================================================

class PreviewImpactRequest(BaseModel):
    """Request to preview which sections will be impacted"""
    changeFactors: List[ChangeFactor]
    overrideSections: Optional[List[str]] = None


@api_router.post("/blueprints/v3/preview-impact")
async def preview_refinement_impact(request: PreviewImpactRequest):
    """
    Preview which sections will be impacted by refinement.
    Use this before refining to show users what will change.
    """
    try:
        impact = await preview_impact(request.changeFactors, request.overrideSections)
        return impact
    except Exception as exc:
        logger.exception("Error previewing impact")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/blueprints/v3/refine", response_model=RefinementResponse)
async def refine_blueprint_endpoint(request: RefinementRequest):
    """
    Intelligent Blueprint Refinement
    
    Refines an existing blueprint based on change factors:
    - Analyzes dependencies between sections
    - Only regenerates impacted sections
    - Preserves unchanged sections exactly
    - Returns detailed change summary with deltas
    
    Change Factor Types:
    - budget_cost: Budget or cost constraints changed
    - compliance_security: Compliance or security requirements updated
    - scope_change: Scope expanded or reduced
    - target_users: Target users changed
    - risk_tolerance: Risk tolerance adjusted
    - timeline: Timeline requirements changed
    - new_context: New context or requirements
    - other: Other changes
    """
    try:
        # Validate max 3 change factors
        if len(request.changeFactors) > 3:
            raise HTTPException(
                status_code=400, 
                detail="Maximum 3 change factors allowed. Select primary factors only."
            )
        
        result = await refine_blueprint(request)
        return result
    except RuntimeError as exc:
        error_msg = str(exc)
        if "API key" in error_msg or "credentials" in error_msg or "not configured" in error_msg:
            logger.error(f"Blueprint refinement configuration error: {exc}")
            raise HTTPException(status_code=500, detail=f"Refinement service configuration error: {error_msg}")
        else:
            logger.error(f"Blueprint refinement runtime error: {exc}")
            raise HTTPException(status_code=500, detail=f"Blueprint refinement failed: {error_msg}")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during blueprint refinement")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}")


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    try:
        # Get status checks from MongoDB
        status_checks = list(status_checks_collection.find({}, {"_id": 0}))
        
        # Convert ISO string timestamps back to datetime objects
        for check in status_checks:
            if isinstance(check['timestamp'], str):
                check['timestamp'] = datetime.fromisoformat(check['timestamp'])
        
        return status_checks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# =============================================================================
# PORTFOLIO API ENDPOINTS (MongoDB-backed)
# =============================================================================

class PortfolioItem(BaseModel):
    """Portfolio item model for MongoDB storage"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: Optional[str] = None
    vertical: Optional[str] = None
    pattern: Optional[str] = None
    stage: str = "Idea"  # Idea, Validating, Blueprinted, In Factory, Live, Archived
    lastEvaluated: Optional[str] = None
    owner: Optional[str] = None
    scores: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    intakePrefill: Optional[Dict[str, Any]] = None
    blueprint: Optional[Dict[str, Any]] = None  # Full blueprint data
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PortfolioItemCreate(BaseModel):
    """Model for creating a portfolio item"""
    model_config = ConfigDict(extra="allow")
    
    id: Optional[str] = None
    name: str
    domain: Optional[str] = None
    vertical: Optional[str] = None
    pattern: Optional[str] = None
    stage: str = "Idea"
    lastEvaluated: Optional[str] = None
    owner: Optional[str] = None
    scores: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    intakePrefill: Optional[Dict[str, Any]] = None
    blueprint: Optional[Dict[str, Any]] = None


@api_router.get("/portfolio")
async def get_portfolio_items():
    """Get all portfolio items"""
    try:
        items = list(portfolio_collection.find({}, {"_id": 0}))
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@api_router.post("/portfolio")
async def create_portfolio_item(item: PortfolioItemCreate):
    """Create a new portfolio item"""
    item_dict = item.model_dump()
    
    # Generate ID if not provided
    if not item_dict.get("id"):
        item_dict["id"] = str(uuid.uuid4())
    
    item_dict["createdAt"] = datetime.utcnow().isoformat()
    item_dict["updatedAt"] = datetime.utcnow().isoformat()
    
    # Check if item with same ID exists
    existing = portfolio_collection.find_one({"id": item_dict["id"]})
    if existing:
        # Update existing
        portfolio_collection.update_one({"id": item_dict["id"]}, {"$set": item_dict})
    else:
        # Insert new item
        portfolio_collection.insert_one(item_dict)
    
    # Return the item without _id field
    item = portfolio_collection.find_one({"id": item_dict["id"]}, {"_id": 0})
    return {"success": True, "item": item}


@api_router.get("/portfolio/{item_id}")
async def get_portfolio_item(item_id: str):
    """Get a single portfolio item by ID"""
    try:
        item = portfolio_collection.find_one({"id": item_id}, {"_id": 0})
        if not item:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@api_router.put("/portfolio/{item_id}")
async def update_portfolio_item(item_id: str, updates: Dict[str, Any]):
    """Update a portfolio item (creates if not exists)"""
    try:
        updates["updatedAt"] = datetime.utcnow().isoformat()
        updates["id"] = item_id  # Ensure ID is set
        
        # Upsert: update if exists, insert if not
        result = portfolio_collection.update_one(
            {"id": item_id}, 
            {"$set": updates, "$setOnInsert": {"createdAt": datetime.utcnow().isoformat()}},
            upsert=True
        )
        
        # Get the updated/created item without _id
        item = portfolio_collection.find_one({"id": item_id}, {"_id": 0})
        return {"success": True, "item": item}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@api_router.delete("/portfolio/{item_id}")
async def delete_portfolio_item(item_id: str):
    """Delete a portfolio item"""
    try:
        result = portfolio_collection.delete_one({"id": item_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        
        return {"success": True, "deleted_id": item_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@api_router.post("/portfolio/bulk")
async def bulk_upsert_portfolio(items: List[Dict[str, Any]]):
    """Bulk upsert portfolio items (for migration from localStorage)"""
    results = []
    for item in items:
        if not item.get("id"):
            item["id"] = str(uuid.uuid4())
        item["updatedAt"] = datetime.utcnow().isoformat()
        
        # Upsert each item
        portfolio_collection.update_one(
            {"id": item["id"]}, 
            {"$set": item, "$setOnInsert": {"createdAt": datetime.utcnow().isoformat()}},
            upsert=True
        )
        results.append(item["id"])
    
    return {"success": True, "upserted_ids": results, "count": len(results)}


@api_router.post("/portfolio/merge")
async def merge_portfolio_items(items: List[Dict[str, Any]]):
    """
    Merge portfolio items from localStorage into MongoDB storage.
    Uses name-based matching to avoid duplicates.
    Only adds items that don't exist (by name).
    """
    added = []
    skipped = []
    
    # Get existing names from MongoDB
    existing_docs = portfolio_collection.find({}, {"name": 1, "_id": 0})
    existing_names = {doc.get("name", "").lower().strip() for doc in existing_docs}
    
    for item in items:
        item_name = item.get("name", "").lower().strip()
        
        if not item_name:
            skipped.append({"reason": "no_name", "item": item.get("name", "unnamed")})
            continue
            
        if item_name in existing_names:
            skipped.append({"reason": "duplicate", "name": item.get("name")})
            continue
        
        # Add new item
        if not item.get("id"):
            item["id"] = str(uuid.uuid4())
        item["updatedAt"] = datetime.utcnow().isoformat()
        item["mergedAt"] = datetime.utcnow().isoformat()
        
        portfolio_collection.insert_one(item)
        added.append(item.get("name"))
        existing_names.add(item_name)  # Prevent duplicates within batch
    
    return {
        "success": True, 
        "added": added, 
        "added_count": len(added),
        "skipped": skipped,
        "skipped_count": len(skipped)
    }


# =============================================================================
# FACTORY V5 ENDPOINTS
# =============================================================================

@api_router.post("/factory/generate-kit")
async def generate_kit_endpoint(request: GenerateKitRequest):
    """
    Generate a Starter Kit from a V3 Blueprint.
    Returns a ZIP file for download.
    """
    try:
        zip_bytes, metadata = await generate_starter_kit(
            request.blueprint,
            use_llm=request.use_llm_enhancement
        )
        
        # Store metadata in MongoDB
        metadata_dict = metadata.model_dump()
        metadata_dict['generated_at'] = metadata_dict['generated_at'].isoformat()
        
        # Upsert kit metadata
        kits_collection.update_one(
            {"blueprint_id": metadata.blueprint_id}, 
            {"$set": metadata_dict},
            upsert=True
        )
        
        # Update factory status in MongoDB
        factory_status_collection.update_one(
            {"blueprint_id": metadata.blueprint_id},
            {"$set": {
                "blueprint_id": metadata.blueprint_id,
                "blueprint_name": metadata.blueprint_name,
                "status": "Starter Kit Generated",
                "kit_generated_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
            }},
            upsert=True
        )
        
        # Return ZIP file
        safe_name = metadata.blueprint_name.replace(" ", "_").replace("/", "_")[:50]
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}_starter_kit.zip"'
            }
        )
    except Exception as e:
        logger.exception("Failed to generate starter kit")
        raise HTTPException(status_code=500, detail=f"Failed to generate starter kit: {str(e)}")


@api_router.post("/factory/generate-kit-preview")
async def generate_kit_preview_endpoint(request: GenerateKitRequest):
    """
    Generate a Starter Kit and return file contents for preview (no download).
    """
    try:
        import zipfile
        import io
        
        zip_bytes, metadata = await generate_starter_kit(
            request.blueprint,
            use_llm=request.use_llm_enhancement
        )
        
        # Extract files from ZIP for preview
        files = {}
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            for name in zf.namelist():
                if not name.endswith('/'):  # Skip directories
                    files[name] = zf.read(name).decode('utf-8')
        
        # Store metadata in MongoDB
        metadata_dict = metadata.model_dump()
        metadata_dict['generated_at'] = metadata_dict['generated_at'].isoformat()
        
        # Upsert kit metadata
        kits_collection.update_one(
            {"blueprint_id": metadata.blueprint_id}, 
            {"$set": metadata_dict},
            upsert=True
        )
        
        # Update factory status in MongoDB
        factory_status_collection.update_one(
            {"blueprint_id": metadata.blueprint_id},
            {"$set": {
                "blueprint_id": metadata.blueprint_id,
                "blueprint_name": metadata.blueprint_name,
                "status": "Starter Kit Generated",
                "kit_generated_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
            }},
            upsert=True
        )
        
        return {
            "metadata": metadata_dict,
            "files": files,
            "file_count": len(files)
        }
    except Exception as e:
        logger.exception("Failed to generate starter kit preview")
        raise HTTPException(status_code=500, detail=f"Failed to generate starter kit: {str(e)}")


@api_router.get("/factory/status/{blueprint_id}")
async def get_factory_status(blueprint_id: str):
    """Get factory status for a blueprint"""
    status = factory_status_collection.find_one({"blueprint_id": blueprint_id}, {"_id": 0})
    if not status:
        return {
            "blueprint_id": blueprint_id,
            "status": "Not Started",
            "readiness_checklist": {
                "data_access_confirmed": False,
                "core_flow_runnable": False,
                "security_baseline_captured": False,
                "observability_plan_noted": False,
            }
        }
    return status


@api_router.put("/factory/status/{blueprint_id}")
async def update_factory_status(blueprint_id: str, status_update: Dict[str, Any]):
    """Update factory status for a blueprint"""
    status_update["last_updated"] = datetime.utcnow().isoformat()
    status_update["blueprint_id"] = blueprint_id
    
    # Upsert status in MongoDB
    factory_status_collection.update_one(
        {"blueprint_id": blueprint_id},
        {"$set": status_update},
        upsert=True
    )
    
    return {"success": True, "blueprint_id": blueprint_id}


@api_router.get("/factory/kits")
async def list_factory_kits():
    """List all generated starter kits"""
    kits = list(kits_collection.find({}, {"_id": 0}))
    return {"kits": kits}


@api_router.get("/factory/kit/{blueprint_id}")
async def get_factory_kit(blueprint_id: str):
    """Get kit metadata for a blueprint"""
    kit = kits_collection.find_one({"blueprint_id": blueprint_id}, {"_id": 0})
    if not kit:
        raise HTTPException(status_code=404, detail="Kit not found")
    return kit


@api_router.post("/factory/regenerate-module")
async def regenerate_module_endpoint(request: RegenerateModuleRequest):
    """Regenerate a specific module of the starter kit"""
    try:
        files = await regenerate_module(
            request.blueprint,
            request.module,
            use_llm=request.use_llm_enhancement
        )
        return {"module": request.module, "files": files}
    except Exception as e:
        logger.exception(f"Failed to regenerate module {request.module}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/factory/add-endpoint")
async def add_endpoint_endpoint(request: AddEndpointRequest):
    """Generate code for a new endpoint"""
    try:
        result = await add_endpoint_to_kit(
            request.blueprint,
            request.endpoint_name,
            request.method,
            request.description,
            request.request_schema,
            request.response_schema
        )
        return result
    except Exception as e:
        logger.exception("Failed to add endpoint")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/factory/download-kit/{blueprint_id}")
async def download_existing_kit(blueprint_id: str, blueprint: Dict[str, Any]):
    """Download a previously generated kit (regenerates from blueprint)"""
    try:
        zip_bytes, metadata = await generate_starter_kit(blueprint, use_llm=False)
        safe_name = metadata.blueprint_name.replace(" ", "_").replace("/", "_")[:50]
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}_starter_kit.zip"'
            }
        )
    except Exception as e:
        logger.exception("Failed to download kit")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GITHUB OAUTH & PUSH ENDPOINTS
# =============================================================================

import httpx
import base64

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
FRONTEND_URL = os.environ.get("REACT_APP_FRONTEND_URL", "")


class GitHubAuthRequest(BaseModel):
    """Request to exchange GitHub OAuth code for token"""
    code: str


class GitHubPushRequest(BaseModel):
    """Request to push files to GitHub"""
    token: str
    repo_name: str
    repo_description: Optional[str] = None
    is_private: bool = False
    files: Dict[str, str]  # filename -> content


class GitHubTokenResponse(BaseModel):
    """Response from GitHub token exchange"""
    access_token: str
    user: Dict[str, Any]


@api_router.get("/github/oauth-url")
async def get_github_oauth_url():
    """Get GitHub OAuth URL for initiating login"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=503, 
            detail="GitHub OAuth not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables."
        )
    
    redirect_uri = f"{FRONTEND_URL}/factory?github_callback=true"
    oauth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={redirect_uri}&scope=repo,user"
    
    return {"oauth_url": oauth_url, "configured": True}


@api_router.post("/github/exchange-token")
async def exchange_github_token(request: GitHubAuthRequest):
    """Exchange GitHub OAuth code for access token"""
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth not configured"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": request.code,
                },
                headers={"Accept": "application/json"},
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Failed to exchange code for token")
            
            token_data = token_response.json()
            
            if "error" in token_data:
                raise HTTPException(
                    status_code=401,
                    detail=token_data.get("error_description", "OAuth authentication failed")
                )
            
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(status_code=401, detail="No access token received")
            
            # Fetch user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Failed to fetch GitHub user info")
            
            user_data = user_response.json()
            
            return {
                "access_token": access_token,
                "user": {
                    "id": user_data.get("id"),
                    "login": user_data.get("login"),
                    "avatar_url": user_data.get("avatar_url"),
                    "name": user_data.get("name"),
                }
            }
            
    except httpx.HTTPError as e:
        logger.exception("HTTP error during GitHub OAuth")
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")


@api_router.post("/github/push")
async def push_to_github(request: GitHubPushRequest):
    """Create a GitHub repository and push files to it"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {request.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            
            # Get user info to get username
            user_response = await client.get(
                "https://api.github.com/user",
                headers=headers,
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid GitHub token")
            
            user_data = user_response.json()
            username = user_data.get("login")
            
            # Create repository
            repo_response = await client.post(
                "https://api.github.com/user/repos",
                json={
                    "name": request.repo_name,
                    "description": request.repo_description or "Generated by Infinite AI Studio Factory",
                    "private": request.is_private,
                    "auto_init": True,  # Initialize with README to create default branch
                },
                headers=headers,
            )
            
            if repo_response.status_code == 422:
                # Repository might already exist
                error_detail = repo_response.json()
                if "name already exists" in str(error_detail):
                    raise HTTPException(
                        status_code=409,
                        detail=f"Repository '{request.repo_name}' already exists. Please choose a different name."
                    )
                raise HTTPException(status_code=422, detail=str(error_detail))
            
            if repo_response.status_code != 201:
                raise HTTPException(
                    status_code=repo_response.status_code,
                    detail=f"Failed to create repository: {repo_response.text}"
                )
            
            repo_data = repo_response.json()
            repo_full_name = repo_data["full_name"]
            default_branch = repo_data.get("default_branch", "main")
            
            # Wait a moment for GitHub to initialize the repo
            import asyncio
            await asyncio.sleep(2)
            
            # Get the HEAD commit SHA
            ref_response = await client.get(
                f"https://api.github.com/repos/{repo_full_name}/git/refs/heads/{default_branch}",
                headers=headers,
            )
            
            if ref_response.status_code != 200:
                # Retry once after short delay
                await asyncio.sleep(2)
                ref_response = await client.get(
                    f"https://api.github.com/repos/{repo_full_name}/git/refs/heads/{default_branch}",
                    headers=headers,
                )
            
            if ref_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get repository reference. Please try again."
                )
            
            head_sha = ref_response.json()["object"]["sha"]
            
            # Get the tree for the current HEAD
            commit_response = await client.get(
                f"https://api.github.com/repos/{repo_full_name}/git/commits/{head_sha}",
                headers=headers,
            )
            base_tree_sha = commit_response.json()["tree"]["sha"]
            
            # Create blobs for each file
            tree_items = []
            for file_path, file_content in request.files.items():
                # Create blob
                blob_response = await client.post(
                    f"https://api.github.com/repos/{repo_full_name}/git/blobs",
                    json={
                        "content": file_content,
                        "encoding": "utf-8",
                    },
                    headers=headers,
                )
                
                if blob_response.status_code != 201:
                    logger.warning(f"Failed to create blob for {file_path}: {blob_response.text}")
                    continue
                
                blob_sha = blob_response.json()["sha"]
                
                tree_items.append({
                    "path": file_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha,
                })
            
            if not tree_items:
                raise HTTPException(status_code=500, detail="Failed to create any file blobs")
            
            # Create tree
            tree_response = await client.post(
                f"https://api.github.com/repos/{repo_full_name}/git/trees",
                json={
                    "base_tree": base_tree_sha,
                    "tree": tree_items,
                },
                headers=headers,
            )
            
            if tree_response.status_code != 201:
                raise HTTPException(status_code=500, detail="Failed to create git tree")
            
            new_tree_sha = tree_response.json()["sha"]
            
            # Create commit
            commit_create_response = await client.post(
                f"https://api.github.com/repos/{repo_full_name}/git/commits",
                json={
                    "message": "Initial commit: Add starter kit files from Infinite AI Studio Factory",
                    "tree": new_tree_sha,
                    "parents": [head_sha],
                },
                headers=headers,
            )
            
            if commit_create_response.status_code != 201:
                raise HTTPException(status_code=500, detail="Failed to create commit")
            
            new_commit_sha = commit_create_response.json()["sha"]
            
            # Update reference
            update_ref_response = await client.patch(
                f"https://api.github.com/repos/{repo_full_name}/git/refs/heads/{default_branch}",
                json={"sha": new_commit_sha},
                headers=headers,
            )
            
            if update_ref_response.status_code not in [200, 201]:
                raise HTTPException(status_code=500, detail="Failed to update branch reference")
            
            return {
                "success": True,
                "repository": {
                    "name": repo_data["name"],
                    "full_name": repo_full_name,
                    "html_url": repo_data["html_url"],
                    "clone_url": repo_data["clone_url"],
                    "private": repo_data["private"],
                },
                "files_pushed": len(tree_items),
                "commit_sha": new_commit_sha,
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to push to GitHub")
        raise HTTPException(status_code=500, detail=f"Failed to push to GitHub: {str(e)}")


@api_router.get("/github/check-token")
async def check_github_token(token: str):
    """Check if a GitHub token is valid"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "valid": True,
                    "user": {
                        "login": user_data.get("login"),
                        "avatar_url": user_data.get("avatar_url"),
                        "name": user_data.get("name"),
                    }
                }
            else:
                return {"valid": False}
                
    except Exception:
        return {"valid": False}


# Include the router in the main app
app.include_router(api_router)

# Configure CORS
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
allowed_origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

