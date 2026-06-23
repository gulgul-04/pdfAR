# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class EngineConfig:

    # 1. ENVIRONMENT AND SECURITY CONFIGURATIONS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://localhost:5173").split(",")
    API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "5/minute")

    # 2. FILE & DIRECTORY CONFIGURATIONS
    TEMP_WORKSPACE_DIR = "temp_jobs"
    OUTPUT_DIR_NAME = "test_docs"
    FINAL_PDF_FILENAME = "final_restored.pdf"
    
    # 3. MATCHING & FUZZY LOGIC THRESHOLDS
    MIN_CONFIDENCE_AUTO = 60.0    
    MIN_CONFIDENCE_REVIEW = 50.0  
    CONTEXT_WINDOW_SIZE = 60    
    
    # 4. GEOMETRY & SPATIAL TOLERANCES
    Y_AXIS_TOLERANCE = 15 
    X_AXIS_PADDING = 5    
    Y_AXIS_PADDING = 3    
    
    # 5. UNIVERSAL ADOBE PDF SUBTYPE MAPPINGS
    ANNOT_SUBTYPE_MAPPING = {
        "Text": "Sticky Note", 
        "FreeText": "FreeText Margin", 
        "Square": "Square/Table Highlights",
        "Highlight": "Highlight", 
        "Redact": "Redaction", 
        "Caret": "Insertion Caret"
    }

    @classmethod
    def get_final_output_path(cls) -> str:
        return os.path.join(cls.OUTPUT_DIR_NAME, cls.FINAL_PDF_FILENAME)