import os 
import json
from engine.extractor import extract_annotations
from engine.matcher import match_annotations
from engine.injector import inject_annotations
from engine.schemas import ExtractedAnnotation
from engine.config import EngineConfig

def run_test():
    print("\n" + "="*50)
    print("INITIATING PDF ENGINE TEST PIPELINE")
    print("="*50 + "\n")

    # Define Paths
    original_pdf = os.path.join("test_docs", "original.pdf")
    edited_pdf = os.path.join("test_docs", "edited.pdf")

    if not os.path.exists(original_pdf) or not os.path.exists(edited_pdf):
        print("ERROR: Missing test PDFs.")
        print(f"Please ensure '{original_pdf}' and '{edited_pdf}' exists.")
        return
    
    # Phase 1: Extraction 
    print("Phase 1: Extracting from Original PDF...")
    try:
        extracted_objects = extract_annotations(original_pdf)
        
        print(f"Successfully extracted {len(extracted_objects)} annotations.")
        for idx, annot in enumerate(extracted_objects):
            thread_tag = "[REPLY] " if annot.parent_id else ""
            print(f"[{idx+1}]{thread_tag}{annot.type} -> '{annot.anchor_text}'(Strategy: {annot.strategy})")

    except Exception as e:
        print(f"EXTRACTION FAILED: {e}")
        return
    print("-" * 50)

    # Phase 2: Matching
    print("Phase 2: Searching Edited PDF (Fuzzy Match)...")
    try:
        matched_results = match_annotations(extracted_objects, edited_pdf)
        
        print(f"Successfully processed {len(matched_results)} matches.\n")

        for idx, match in enumerate (matched_results):
            score = match.confidence_score
            if score >= EngineConfig.MIN_CONFIDENCE_AUTO:
                status = "AUTO"
            elif score >= EngineConfig.MIN_CONFIDENCE_REVIEW:
                status = "REVIEW"
            else:
                status = "FAIL"

            thread_tag = "[REPLY] " if match.parent_id else ""
            print(f" [{idx+1}] {thread_tag}{status} | Score: {score}% | Reason: {match.match_reason}")
            print(f"     Comment: '{match.comment_text}'")
            print(f"     Mapped to Page: {match.new_page}")
            print()

    except Exception as e: 
        print(f"MATCHING FAILED: {e}")
        return
    
    # Phase 3: Injection
    print("-" * 50)
    print("Phase 3: Injecting Comments into Final PDF...")
    try: 
        final_output = os.path.join("test_docs", "final_restored.pdf")
        inject_annotations(matched_results, edited_pdf, final_output)
        print(f"SUCCESS! Final PDF saved to: {final_output}")
    except Exception as e:
        print(f"Injection Failed: {e}")
        return
    
    print("="*50)
    print("PIPELINE TEST COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_test()
    