import os
import shutil
import uuid
from fastapi import UploadFile
from .config import EngineConfig

TEMP_BASE_DIR = EngineConfig.TEMP_WORKSPACE_DIR

async def create_job_workspace() -> tuple[str, str]:
    """
    Creates a unique and isolated directory for a processing job or task.
    Using UUIDs ensures that if two clients upload PDFs at the same time, 
    their files will not collide or overwrite each other. 
    """
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_BASE_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    return job_id, job_dir

async def save_uploaded_file(upload_file: UploadFile, destination_path: str) -> str:
    with open(destination_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return destination_path

def cleanup_workspace(job_dir: str):
    if os.path.exists(job_dir):
        shutil.rmtree(job_dir)
        print(f"Secured & wiped workspace: {job_dir}")