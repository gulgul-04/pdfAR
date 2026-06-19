import os 
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from engine import file_handler, extractor, matcher, injector, schemas
from engine.config import EngineConfig

app = FastAPI(
    title="PDF Annotation Restoration API",
    description="Enterprise-grade backend for semantic PDF comment porting.",
    version="1.0.0"
)

# 1. Security: Strict CORS Middleware
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://myvercelapp" # Change when app is initialised
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"]
)

# 2. Security: DOS Protection & Sanitization Constants
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024 # 50 MB limit
ALLOWED_MIME_TYPE = "application/pdf"

async def validate_file(file: UploadFile, file_type_name: str):
    if file.content_type != ALLOWED_MIME_TYPE:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            details=f"Security Violation: {file_type_name} must be a valid PDF document."
        )
    
    # Check Payload size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Security Violation: {file_type_name} exceeds the 50MB payload limit."
        )
    
# 3. Utility and Background Tasks
async def schedule_cleanup(job_dir: str, delay_seconds: int):
    await asyncio.sleep(delay_seconds)
    file_handler.cleanup_workspace(job_dir)

# 4. Core Processing Endpoint
@app.post("/api/v1/process-pdfs", response_model=schemas.ProcessPDFResponse)
async def process_pdfs(
    background_tasks: BackgroundTasks, 
    original_pdf: UploadFile = File(...),
    edited_pdf: UploadFile = File(...)
):
    # Step 1: Security sanitization
    await validate_file(original_pdf, "Original PDF")
    await validate_file(edited_pdf, "Edited PDF")

    # Step 2: Provision secure workspace
    job_id, job_dir = await file_handler.create_job_workspace()
    background_tasks.add_task(schedule_cleanup, job_dir, delay_seconds=900)

    try:
        # Step 3: Safely stream files to the isolated workspace
        orig_path = os.path.join(job_dir, "original.pdf")
        edited_path = os.path.join(job_dir, "edited.pdf")
        final_path = os.path.join(job_dir, EngineConfig.FINAL_PDF_FILENAME)

        await file_handler.save_uploaded_file(original_pdf, orig_path)
        await file_handler.save_uploaded_file(edited_pdf, edited_path)

        # Step 4: Execute Engine Pipeline
        extracted_annots = extractor.extract_annotations(orig_path)

        if not extracted_annots:
            return schemas.ProcessPDFResponse(
                status="success",
                message="No annotations found in the original document.",
                total_annotations_found=0,
                successful_matches=0,
                needs_review=0,
                auto_injected=[],
                review_queue=[],
                download_token=job_id
            )

        matched_annots = matcher.match_annotations(extracted_annots, edited_path)

        injector.inject_annotations(matched_annots, edited_path, final_path)

        # Step 5: Route Data for the React Frontend
        auto_injected = []
        review_queue = []

        for annot in matched_annots:
            if annot.confidence_score >= EngineConfig.MIN_CONFIDENCE_AUTO:
                auto_injected.append(annot)
            else:
                review_queue.append(annot)

        return schemas.ProcessPDFResponse(
            status="success",
            message="Processing complete.",
            total_annotations_found=len(extracted_annots),
            successful_matches=len(auto_injected),
            needs_review=len(review_queue),
            auto_injected=auto_injected,
            review_queue=review_queue,
            download_token=job_id # Frontend uses this ID to download the final file
        )
    
    except Exception as e:
        # If the engine crashes, trigger an immediate wipe to protect data
        file_handler.cleanup_workspace(job_dir)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during engine execution: {str(e)}"
        )