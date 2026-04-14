
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
import os
import json
from threading import Lock
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4

import asyncio
from dotenv import load_dotenv
from db import init_db, close_db
from tortoise import Tortoise
import logging

# Load .env before reading environment-backed settings.
load_dotenv()

# --- Configurable Settings ---
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "1") == "1"
DEFAULT_MODELS_DIR = os.environ.get("DEFAULT_MODELS_DIR") or os.environ.get("MODELS_DIR")


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vaultwares.api")

app = FastAPI(title="Vaultwares Workflow API", description="API for managing workflows, favorites, backup, NIM integration, and storage.", version="0.2.0")

# --- CORS ---
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic(auto_error=False)

def check_auth(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    if not AUTH_ENABLED:
        return
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing credentials")
    # Placeholder: Replace with real user/pass check
    if credentials.username != "admin" or credentials.password != "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")

# --- Models ---
class Workflow(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    steps: list = Field(default_factory=list)
    pinned: bool = False
    pin: Optional[bool] = None
    favorite: bool = False
    lastRun: Optional[str] = None

class WorkflowCreateRequest(BaseModel):
    id: Optional[str] = None
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    steps: list = Field(default_factory=list)
    pinned: bool = False
    pin: Optional[bool] = None
    favorite: bool = False
    lastRun: Optional[str] = None

class WorkflowUpdateRequest(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[list] = None
    pinned: Optional[bool] = None
    pin: Optional[bool] = None
    favorite: Optional[bool] = None
    lastRun: Optional[str] = None

class WorkflowsExportRequest(BaseModel):
    ids: List[str]

class WorkflowsBackupRequest(BaseModel):
    pass

class WorkflowsRestoreRequest(BaseModel):
    data: list | dict

class WorkflowPinRequest(BaseModel):
    id: str
    pin: bool

class WorkflowFavoriteRequest(BaseModel):
    id: str
    favorite: bool

class WorkflowRunRequest(BaseModel):
    id: str
    mode: str  # 'local' or 'nim'

class ConfigUpdateRequest(BaseModel):
    modelsDir: Optional[str] = None
    preferredStorageProvider: Optional[str] = None
    apiMode: Optional[str] = None
    apiBase: Optional[str] = None
    themeIndex: Optional[int] = None
    runtimeProvider: Optional[str] = None
    localBridgeUrl: Optional[str] = None
    localComfyUrl: Optional[str] = None
    saveDirectory: Optional[str] = None
    facefusionCommand: Optional[str] = None
    scannedModels: Optional[dict] = None
    flowModelSelections: Optional[dict] = None
    updatedAt: Optional[str] = None

class ModelsDirRequest(BaseModel):
    dir_path: Optional[str] = None
    models_dir: Optional[str] = None
    modelsDir: Optional[str] = None

# --- Persistent JSON Storage ---
VAULTWARES_HOME_CSS = """
body { background: #181c24; color: #f3f6fa; font-family: 'Segoe UI', Arial, sans-serif; text-align: center; margin: 0; padding: 0; }
.logo { margin-top: 48px; }
.vault {
    display: inline-block;
    margin: 0 auto 24px auto;
    width: 120px;
    height: 120px;
    background: linear-gradient(135deg, #2e3a4e 60%, #4e7ad2 100%);
    border-radius: 50%;
    box-shadow: 0 4px 32px #0008;
    position: relative;
}
.vault:before {
    content: '';
    display: block;
    position: absolute;
    left: 50%; top: 50%;
    width: 60px; height: 60px;
    background: #232b3a;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 0 0 8px #4e7ad2;
}
h1 { font-size: 2.5rem; margin: 24px 0 8px 0; letter-spacing: 2px; }
.subtitle { color: #b0c4e7; font-size: 1.2rem; margin-bottom: 32px; }
.links a {
    display: inline-block;
    margin: 12px 16px;
    padding: 12px 28px;
    background: #4e7ad2;
    color: #fff;
    border-radius: 6px;
    text-decoration: none;
    font-weight: 600;
    font-size: 1.1rem;
    transition: background 0.2s;
}
.links a:hover { background: #355a8a; }
.apidoc-link {
    margin-top: 40px;
    color: #b0c4e7;
    font-size: 0.95rem;
}
.apidoc-link a {
    color: #fff;
    text-decoration: underline;
}
"""

WORKFLOWS_FILE = os.environ.get("WORKFLOWS_FILE", "workflows.json")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
API_KEY_REG_URL = os.environ.get("API_KEY_REG_URL", f"{FRONTEND_URL.rstrip('/')}/register")

_storage_lock = Lock()
APP_CONFIG = {
    "modelsDir": DEFAULT_MODELS_DIR or "",
    "preferredStorageProvider": "other",
    "apiMode": "remote-with-local-fallback",
    "apiBase": "",
    "themeIndex": 0,
    "runtimeProvider": "local-bridge" if DEFAULT_MODELS_DIR else "browser-local",
    "localBridgeUrl": "http://127.0.0.1:8484",
    "localComfyUrl": "http://127.0.0.1:8188",
    "saveDirectory": "",
    "facefusionCommand": "facefusion",
    "scannedModels": {
        "scannedAt": "",
        "source": "none",
        "modelsDir": DEFAULT_MODELS_DIR or "",
        "warnings": [],
        "categories": {
            "checkpoints": [],
            "loras": [],
            "insightface": [],
            "hyperswap": [],
            "reactorFaces": [],
            "facerestoreModels": [],
            "ultralytics": [],
            "sams": [],
        },
    },
    "flowModelSelections": {
        "imageCaptioning": {"captionModel": "", "captionAdapter": ""},
        "loraTraining": {"baseModel": ""},
        "videoFaceSwap": {
            "swapModel": "",
            "alternateSwapModel": "",
            "faceModel": "",
            "restoreModel": "",
            "detectorModel": "",
        },
    },
}

def _next_workflow_id() -> str:
    return f"wf-{uuid4().hex[:12]}"

def _workflow_pin_value(pin: Optional[bool], pinned: Optional[bool]) -> bool:
    if pin is not None:
        return bool(pin)
    if pinned is not None:
        return bool(pinned)
    return False

def _workflow_to_dict(workflow: Workflow) -> dict:
    pin_value = _workflow_pin_value(workflow.pin, workflow.pinned)
    return {
        "id": workflow.id,
        "name": workflow.name,
        "category": workflow.category,
        "description": workflow.description,
        "steps": workflow.steps or [],
        "pinned": pin_value,
        "favorite": bool(workflow.favorite),
        "lastRun": workflow.lastRun,
    }

def _dict_to_workflow(data: dict) -> Workflow:
    pin_value = _workflow_pin_value(data.get("pin"), data.get("pinned"))
    return Workflow(
        id=data.get("id", _next_workflow_id()),
        name=data.get("name", "Untitled workflow"),
        category=data.get("category"),
        description=data.get("description"),
        steps=data.get("steps") or [],
        pinned=pin_value,
        pin=pin_value,
        favorite=bool(data.get("favorite", False)),
        lastRun=data.get("lastRun"),
    )

def _load_workflows_from_file() -> List[Workflow]:
    with _storage_lock:
        if not os.path.exists(WORKFLOWS_FILE):
            return []
        with open(WORKFLOWS_FILE, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    if not isinstance(raw, list):
        return []
    return [_dict_to_workflow(item) for item in raw if isinstance(item, dict)]

def _save_workflows_to_file(workflows: List[Workflow]) -> None:
    serialized = [_workflow_to_dict(workflow) for workflow in workflows]
    with _storage_lock:
        with open(WORKFLOWS_FILE, "w", encoding="utf-8") as handle:
            json.dump(serialized, handle, indent=2)


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
    <head>
        <title>Vaultwares Pipelines</title>
        <style>{css}</style>
    </head>
    <body>
        <div class="logo">
            <div class="vault"></div>
        </div>
        <h1>Vaultwares Pipelines</h1>
        <div class="subtitle">Multi-Agent AI Workflow Platform</div>
        <p>Welcome to <b>Vaultwares</b>!<br>
        Access the full dashboard, explore workflows, and manage your AI pipelines.</p>
        <div class="links">
            <a href="{frontend_url}" target="_blank">Go to Frontend Dashboard</a>
            <a href="{api_key_url}" target="_blank">Register for an API Key</a>
        </div>
        <p class="apidoc-link">API documentation: <a href='/docs'>/docs</a></p>
    </body>
    </html>
    """.format(css=VAULTWARES_HOME_CSS, frontend_url=FRONTEND_URL, api_key_url=API_KEY_REG_URL)


# --- DB Setup ---
from tortoise import fields, models
from tortoise.exceptions import DoesNotExist
DB_URL = os.getenv("DB_URL", "postgres://postgres:postgres@localhost:5432/vaultwares")

class WorkflowDB(models.Model):
    id = fields.CharField(pk=True, max_length=64)
    name = fields.CharField(max_length=255)
    category = fields.CharField(max_length=255, null=True)
    steps = fields.JSONField(null=True)
    pinned = fields.BooleanField(default=False)
    favorite = fields.BooleanField(default=False)

    class Meta:
        table = "workflows"

def workflowdb_to_pydantic(wf: WorkflowDB) -> Workflow:
    pin_value = bool(wf.pinned)
    return Workflow(
        id=wf.id,
        name=wf.name,
        category=wf.category,
        description=None,
        steps=wf.steps or [],
        pinned=pin_value,
        pin=pin_value,
        favorite=wf.favorite,
        lastRun=None,
    )


# --- Tortoise ORM Initialization State ---
_tortoise_initialized = False

@app.on_event("startup")
async def startup_event():
    global _tortoise_initialized
    try:
        await init_db(DB_URL)
        _tortoise_initialized = True
        logger.info("Tortoise ORM initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Tortoise ORM: {e}")
        _tortoise_initialized = False

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await close_db()
        logger.info("Tortoise ORM connections closed.")
    except Exception as e:
        logger.error(f"Error closing Tortoise ORM connections: {e}")


# --- Endpoints ---

def db_available() -> bool:
    return bool(_tortoise_initialized and Tortoise._inited)

@app.get("/workflows", response_model=List[Workflow])
async def list_workflows(credentials: HTTPBasicCredentials = Depends(check_auth)):
    if db_available():
        workflows = await WorkflowDB.all()
        return [workflowdb_to_pydantic(wf) for wf in workflows]
    return _load_workflows_from_file()


@app.post("/workflows", response_model=Workflow)
async def create_workflow(wf: WorkflowCreateRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    workflow_id = wf.id or _next_workflow_id()
    pin_value = _workflow_pin_value(wf.pin, wf.pinned)
    created = Workflow(
        id=workflow_id,
        name=wf.name,
        category=wf.category,
        description=wf.description,
        steps=wf.steps or [],
        pinned=pin_value,
        pin=pin_value,
        favorite=wf.favorite,
        lastRun=wf.lastRun,
    )

    if db_available():
        obj = await WorkflowDB.create(
            id=created.id,
            name=created.name,
            category=created.category,
            steps=created.steps,
            pinned=created.pinned,
            favorite=created.favorite,
        )
        return workflowdb_to_pydantic(obj)

    workflows = _load_workflows_from_file()
    workflows.append(created)
    _save_workflows_to_file(workflows)
    return created


@app.put("/workflows/{id}", response_model=Workflow)
async def update_workflow(id: str, wf: WorkflowUpdateRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    if db_available():
        try:
            obj = await WorkflowDB.get(id=id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if wf.name is not None:
            obj.name = wf.name
        if wf.category is not None:
            obj.category = wf.category
        if wf.steps is not None:
            obj.steps = wf.steps
        if wf.favorite is not None:
            obj.favorite = wf.favorite
        pin_value = _workflow_pin_value(wf.pin, wf.pinned)
        if wf.pin is not None or wf.pinned is not None:
            obj.pinned = pin_value
        await obj.save()
        return workflowdb_to_pydantic(obj)

    workflows = _load_workflows_from_file()
    for index, item in enumerate(workflows):
        if item.id != id:
            continue
        updated = Workflow(
            id=id,
            name=wf.name if wf.name is not None else item.name,
            category=wf.category if wf.category is not None else item.category,
            description=wf.description if wf.description is not None else item.description,
            steps=wf.steps if wf.steps is not None else item.steps,
            pinned=_workflow_pin_value(wf.pin, wf.pinned) if (wf.pin is not None or wf.pinned is not None) else item.pinned,
            pin=_workflow_pin_value(wf.pin, wf.pinned) if (wf.pin is not None or wf.pinned is not None) else item.pinned,
            favorite=wf.favorite if wf.favorite is not None else item.favorite,
            lastRun=wf.lastRun if wf.lastRun is not None else item.lastRun,
        )
        workflows[index] = updated
        _save_workflows_to_file(workflows)
        return updated

    raise HTTPException(status_code=404, detail="Workflow not found")


@app.delete("/workflows/{id}")
async def delete_workflow(id: str, credentials: HTTPBasicCredentials = Depends(check_auth)):
    if db_available():
        deleted = await WorkflowDB.filter(id=id).delete()
        if not deleted:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return {"ok": True}

    workflows = _load_workflows_from_file()
    filtered = [item for item in workflows if item.id != id]
    if len(filtered) == len(workflows):
        raise HTTPException(status_code=404, detail="Workflow not found")
    _save_workflows_to_file(filtered)
    return {"ok": True}


@app.post("/workflows/export")
async def export_workflows(req: WorkflowsExportRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    if db_available():
        workflows = await WorkflowDB.filter(id__in=req.ids)
        return [workflowdb_to_pydantic(wf) for wf in workflows]
    workflows = _load_workflows_from_file()
    if not req.ids:
        return workflows
    target_ids = set(req.ids)
    return [workflow for workflow in workflows if workflow.id in target_ids]


@app.post("/workflows/backup")
async def backup_workflows(_: WorkflowsBackupRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    if db_available():
        workflows = await WorkflowDB.all()
        return [workflowdb_to_pydantic(wf) for wf in workflows]
    return _load_workflows_from_file()


@app.post("/workflows/restore")
async def restore_workflows(req: WorkflowsRestoreRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    items = req.data
    if isinstance(items, dict):
        candidate = items.get("workflows", [])
        items = candidate if isinstance(candidate, list) else []
    workflows_in = [_dict_to_workflow(item) for item in items if isinstance(item, dict)]

    if db_available():
        for wf in workflows_in:
            await WorkflowDB.update_or_create(
                defaults={
                    "name": wf.name,
                    "category": wf.category,
                    "steps": wf.steps,
                    "pinned": wf.pinned,
                    "favorite": wf.favorite,
                },
                id=wf.id,
            )
        return {"ok": True}

    existing = {workflow.id: workflow for workflow in _load_workflows_from_file()}
    for workflow in workflows_in:
        existing[workflow.id] = workflow
    _save_workflows_to_file(list(existing.values()))
    return {"ok": True}


@app.post("/workflows/pin")
async def pin_workflow(req: WorkflowPinRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    if db_available():
        try:
            obj = await WorkflowDB.get(id=req.id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Workflow not found")
        obj.pinned = req.pin
        await obj.save()
        return workflowdb_to_pydantic(obj)

    workflows = _load_workflows_from_file()
    for index, item in enumerate(workflows):
        if item.id != req.id:
            continue
        updated = item.model_copy(update={"pinned": req.pin, "pin": req.pin})
        workflows[index] = updated
        _save_workflows_to_file(workflows)
        return updated
    raise HTTPException(status_code=404, detail="Workflow not found")


@app.post("/workflows/favorite")
async def favorite_workflow(req: WorkflowFavoriteRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    if db_available():
        try:
            obj = await WorkflowDB.get(id=req.id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Workflow not found")
        obj.favorite = req.favorite
        await obj.save()
        return workflowdb_to_pydantic(obj)

    workflows = _load_workflows_from_file()
    for index, item in enumerate(workflows):
        if item.id != req.id:
            continue
        updated = item.model_copy(update={"favorite": req.favorite})
        workflows[index] = updated
        _save_workflows_to_file(workflows)
        return updated
    raise HTTPException(status_code=404, detail="Workflow not found")


@app.post("/workflows/run")
async def run_workflow(req: WorkflowRunRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    if db_available():
        try:
            await WorkflowDB.get(id=req.id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Workflow not found")
    else:
        workflows = _load_workflows_from_file()
        if not any(item.id == req.id for item in workflows):
            raise HTTPException(status_code=404, detail="Workflow not found")
    # NIM VM integration placeholder
    if req.mode == "nim":
        return {"id": req.id, "mode": req.mode, "status": "nim_vm_placeholder", "message": "NIM VM integration not yet implemented."}
    return {"id": req.id, "mode": req.mode, "status": "started"}

# --- Persistent Storage Placeholders ---
@app.post("/storage/google-drive/upload")
def upload_google_drive(credentials: HTTPBasicCredentials = Depends(check_auth)):
    # Placeholder for Google Drive upload
    return {"status": "placeholder", "message": "Google Drive upload not implemented."}

@app.post("/storage/dropbox/upload")
def upload_dropbox(credentials: HTTPBasicCredentials = Depends(check_auth)):
    # Placeholder for Dropbox upload
    return {"status": "placeholder", "message": "Dropbox upload not implemented."}

@app.post("/storage/icloud/upload")
def upload_icloud(credentials: HTTPBasicCredentials = Depends(check_auth)):
    # Placeholder for iCloud upload
    return {"status": "placeholder", "message": "iCloud upload not implemented."}

@app.post("/storage/other/upload")
def upload_other(credentials: HTTPBasicCredentials = Depends(check_auth)):
    # Placeholder for other storage providers
    return {"status": "placeholder", "message": "Other storage provider upload not implemented."}

# --- App Config ---
@app.get("/config")
def get_config(credentials: HTTPBasicCredentials = Depends(check_auth)):
    return APP_CONFIG

@app.post("/config")
def update_config(req: ConfigUpdateRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    payload = req.model_dump(exclude_none=True)
    APP_CONFIG.update(payload)
    if "modelsDir" in payload:
        global DEFAULT_MODELS_DIR
        DEFAULT_MODELS_DIR = payload["modelsDir"]
    return APP_CONFIG

# --- Models Directory Config ---
@app.get("/config/models-dir")
def get_models_dir(credentials: HTTPBasicCredentials = Depends(check_auth)):
    value = APP_CONFIG.get("modelsDir") or DEFAULT_MODELS_DIR or ""
    return {"models_dir": value, "dir_path": value, "modelsDir": value}

@app.post("/config/models-dir")
def set_models_dir(req: ModelsDirRequest, credentials: HTTPBasicCredentials = Depends(check_auth)):
    global DEFAULT_MODELS_DIR
    resolved = req.dir_path or req.models_dir or req.modelsDir
    if resolved is None:
        raise HTTPException(status_code=422, detail="Expected one of dir_path, models_dir, or modelsDir")
    DEFAULT_MODELS_DIR = resolved
    APP_CONFIG["modelsDir"] = resolved
    return {"models_dir": DEFAULT_MODELS_DIR, "dir_path": DEFAULT_MODELS_DIR, "modelsDir": DEFAULT_MODELS_DIR}




# --- Script Entrypoint ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="127.0.0.1", port=9001, reload=True)
