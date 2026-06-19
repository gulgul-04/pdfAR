# config.py
import os

class EngineConfig:
    # 1. FILE & DIRECTORY CONFIGURATIONS
    TEMP_WORKSPACE_DIR = "temp_jobs"
    OUTPUT_DIR_NAME = "test_docs"
    FINAL_PDF_FILENAME = "final_restored.pdf"
    
    # 2. MATCHING & FUZZY LOGIC THRESHOLDS
    # RapidFuzz similarity scores (0.0 - 100.0)
    MIN_CONFIDENCE_AUTO = 85.0    
    MIN_CONFIDENCE_REVIEW = 60.0  
    # Text window expansion size when hunting for anchor text context
    CONTEXT_WINDOW_SIZE = 50    
    
    # 3. GEOMETRY & SPATIAL TOLERANCES
    Y_AXIS_TOLERANCE = 15 
    X_AXIS_PADDING = 5    
    Y_AXIS_PADDING = 3    
    
    # 4. UNIVERSAL ADOBE PDF SUBTYPE MAPPINGS
    # Maps official PDF string subtypes to your engine's internal names
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
        """Helper to safely construct the final PDF output destination path."""
        return os.path.join(cls.OUTPUT_DIR_NAME, cls.FINAL_PDF_FILENAME)