import os 
import json
from engine.extractor import extract_annotations
from engine.matcher import match_annotations
from engine.schemas import ExtractedAnnotation

def run_test():
    print("\n" + "="*50)
    print("INITIATING PDF ENGINE TEST PIPELINE")
    print("="*50 + "\n")

    # Define Paths
    original_pdf = os.path.join("test_docs", "original.pdf")
    edited_pdf = os.path.join("test_docs", "edited_pdf")

    if not os.path.exists(original_pdf) or not os.path.exists(edited_pdf):
        print("ERROR: Missing test PDFs.")
        print(f"Please ensure '{original_pdf}' and '{edited_pdf}' exists.")
        return
    
    # Extraction 
    print("Phase 1: Extracting from Original PDF...")
    try:
        raw_extracted_dicts = extract_annotations(original_pdf)
        extracted_objects = [ExtractedAnnotation(**annot) for annot in raw_extracted_dicts]
        
        print(f"Successfully extracted {len(extracted_objects)} annotations.")
        for idx, annot in enumerate(extracted_objects):
            print(f"[{idx+1}]{annot.type} -> '{annot.anchor_text}'(Strategy: {annot.strategy})")

    except Exception as e:
        print(f"EXTRACTION FAILED: {e}")
        return
    print("-" * 50)

    # Matching
    print("Phase 2: Searching Edited PDF (Fuzzy Match)...")
    try:
        matched_results = match_annotations(extracted_objects, edited_pdf)
        
        print(f"Successfully processed {len(matched_results)} matches.\n")

        for idx, match in enumerate (matched_results):
            score = match.confidence_score
            status = "AUTO" if score >= 85 else ("REVIEW" if score >= 60 else "FAIL")

            print(f" [{idx+1}] {status} | Score: {score}% | Reason: {match.match_reason}")
            print(f"     Comment: '{match.comment_text}'")
            print(f"     Mapped to Page: {match.new_page}")
            print()

    except Exception as e: 
        print(f"MATCHING FAILED: {e}")
        return
    
    print("="*50)
    print("PIPELINE TEST COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_test()
    