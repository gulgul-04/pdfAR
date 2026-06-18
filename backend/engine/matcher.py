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
                anchor_text=annot.anchor_text,
                context_window=annot.context_window,
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

                score = 0

                # Try full context window : Prefix + Anchor + Suffix
                if annot.context_window: 
                    score = fuzz.partial_ratio(annot.context_window, page_text)

                # Try 'half contexts' by comparing with suffix and prefix
                if score < 80.0 and annot.anchor_text in annot.context_window:
                    try: 
                        prefix, suffix = annot.context_window.split(annot.anchor_text, 1)
                        
                        left_context = f"{prefix}{annot.anchor_text}"
                        score_left = fuzz.partial_ratio(left_context, page_text)

                        rigth_context = f"{annot.anchor_text}{suffix}"
                        score_right = fuzz.partial_ratio(rigth_context, page_text)

                        score = max(score, score_left, score_right)
                    except ValueError:
                        pass # Failsafe if the split acts weirdly, just rely on the base score. 

                # Last Resort: just the anchor text - score is penalized and forces for a manual review
                if score < 60.0 and annot.anchor_text:
                    score_anchor = fuzz.partial_ratio(annot.anchor_text, page_text)
                    if score_anchor > 80.0:
                        score_anchor = 75.0
                    score = max(score, score_anchor)

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
            anchor_text=annot.anchor_text,
            context_window=annot.context_window,
            new_page=best_page,
            metadata=annot.metadata,
            comment_text=annot.comment_text
        ))

    doc.close()
    return matched_results