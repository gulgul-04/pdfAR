import fitz
from rapidfuzz import fuzz
from .schemas import ExtractedAnnotation, MatchedAnnotation, Coordinates

MIN_CONFIDENCE_AUTO = 85.0
MIN_CONFIDENCE_REVIEW = 60.0

def match_annotations(extracted_annots: list[ExtractedAnnotation], edited_pdf_path: str) -> list[MatchedAnnotation]:
    # Searches edited PDF for the semantic anchors of the orignal annotations.
    doc = fitz.open(edited_pdf_path)
    matched_results = []

    edited_pages_text = {}
    for i in range(len(doc)):
        raw_text = doc[i].get_text("text")
        edited_pages_text[i] = " ".join(raw_text.split())

    for annot in extracted_annots:
        # Strategy 1 Relative Geometry
        if annot.strategy == "relative_geometry":
            matched_results.append(MatchedAnnotation(
                original_id=annot.id,
                type=annot.type,
                confidence_score=100.0,
                match_reason="Relative Geometric Anchor",
                new_page=annot.page,
                new_coordinates=annot.coordinates,
                metadata=annot.metadata,
                comment_text=annot.comment_text
            ))
            continue

        # Strategy 2 Semantic Text Matching
        best_score = 0.0
        best_page = -1

        target_search_string = annot.context_window if annot.context_window else annot.anchor_text

        # Pass 1: Exact Match
        for page_num, page_text in edited_pages_text.items():
            if target_search_string in page_text:
                best_score = 100.0
                best_page = page_num
                break

        # Pass 2: Fuzzy sliding window 
        if best_score < 100.0:
            for page_num, page_text in edited_pages_text.items():
                if not page_text:
                    continue

                score = fuzz.partial_ratio(target_search_string, page_text)
                if score > best_score:
                    best_score = score
                    best_page = page_num

        # Confidence Routing
        if best_score >= MIN_CONFIDENCE_AUTO:
            reason = "Exact Text Match" if best_score == 100.0 else "High Confidence Fuzzy Match"
        elif best_score >= MIN_CONFIDENCE_REVIEW:
            reason = "Needs Manual Review (Text Heavily Altered)"
        else:
            reason = "Failed to Locate Anchor"
            best_page = None 

        matched_results.append(MatchedAnnotation(
            original_id=annot.id,
            type=annot.type,
            confidence_score=round(best_score, 2),
            match_reason=reason,
            new_page=best_page,
            metadata=annot.metadata,
            comment_text=annot.comment_text
        ))

    doc.close()
    return matched_results