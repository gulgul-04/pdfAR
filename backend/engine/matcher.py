import fitz
from rapidfuzz import fuzz
from .schemas import ExtractedAnnotation, MatchedAnnotation, Coordinates
from .config import EngineConfig

def match_annotations(extracted_annots: list[ExtractedAnnotation], edited_pdf_path: str) -> list[MatchedAnnotation]:
    # Searches edited PDF for the semantic anchors of the orignal annotations.
    doc = fitz.open(edited_pdf_path)
    matched_results = []
    parent_matches = {}

    edited_pages_text = {}
    for i in range(len(doc)):
        raw_text = doc[i].get_text("text")
        edited_pages_text[i] = " ".join(raw_text.split())

    parents = [a for a in extracted_annots if not a.parent_id]
    children = [a for a in extracted_annots if a.parent_id]

    for annot in parents:
        # Strategy 1 Relative Geometry
        if annot.strategy == "relative_geometry":
            matched = MatchedAnnotation(
                original_id=annot.id,
                parent_id=None,
                type=annot.type,
                confidence_score=100.0,
                match_reason="Relative Geometric Anchor",
                anchor_text=annot.anchor_text,
                context_window=annot.context_window,
                new_page=annot.page,
                new_coordinates=annot.coordinates,
                metadata=annot.metadata,
                comment_text=annot.comment_text
            )
            matched_results.append(matched)
            parent_matches[annot.id] = matched
            continue

        # Strategy 2 Semantic Text Matching
        best_score = 0.0
        best_page = -1

        target_search_string = annot.context_window if annot.context_window else annot.anchor_text
        
        orig_page = annot.page if annot.page is not None else 0
        search_order = sorted(edited_pages_text.keys(), key=lambda p: abs(p - orig_page))

        # Pass 1: Exact Match
        for page_num in search_order:
            page_text = edited_pages_text[page_num]
            if target_search_string in page_text:
                best_score = 100.0
                best_page = page_num
                break

        # Pass 2: Fuzzy sliding window 
        if best_score < 100.0:
            for page_num in search_order:
                page_text = edited_pages_text[page_num]
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
                if score < EngineConfig.MIN_CONFIDENCE_REVIEW and annot.anchor_text:
                    score_anchor = fuzz.partial_ratio(annot.anchor_text, page_text)

                    if len(annot.anchor_text.split()) < 3:
                        score_anchor = 0
                    elif score_anchor > 80.0:
                        score_anchor = 75.0

                    score = max(score, score_anchor)

                if score > best_score:
                    best_score = score
                    best_page = page_num

                if best_score >= 85:
                    break


        # Confidence Routing
        if best_score >= EngineConfig.MIN_CONFIDENCE_AUTO:
            reason = "Exact Text Match" if best_score == 100.0 else "High Confidence Fuzzy Match"
        elif best_score >= EngineConfig.MIN_CONFIDENCE_REVIEW:
            reason = "Needs Manual Review (Text Heavily Altered)"
        else:
            reason = "Failed to Locate Anchor"
            best_page = None 

        matched = MatchedAnnotation(
            original_id=annot.id,
            parent_id=None,
            type=annot.type,
            confidence_score=round(best_score, 2),
            match_reason=reason,
            anchor_text=annot.anchor_text,
            context_window=annot.context_window,
            new_page=best_page,
            metadata=annot.metadata,
            comment_text=annot.comment_text
        )
        matched_results.append(matched)
        parent_matches[annot.id] = matched

    # Process children

    unresolved_children = children.copy()
    previous_unresolved_count = -1

    # Keep looping until all grandchildren and great-grandchildren are resolved
    while unresolved_children and len(unresolved_children) != previous_unresolved_count:
        previous_unresolved_count = len(unresolved_children)
        still_unresolved = []

        for annot in unresolved_children:
            parent = parent_matches.get(annot.parent_id)
            
            if parent:
                if parent.new_page is not None:
                    # Parent passed! Piggyback on its exact location.
                    matched = MatchedAnnotation(
                        original_id=annot.id, 
                        parent_id=annot.parent_id, 
                        type="Reply Thread",
                        confidence_score=parent.confidence_score, 
                        match_reason=f"Inherited from Parent",
                        anchor_text=annot.anchor_text, 
                        context_window=annot.context_window,
                        new_page=parent.new_page, 
                        new_coordinates=parent.new_coordinates,
                        metadata=annot.metadata, 
                        comment_text=annot.comment_text
                    )
                else:
                    # Parent explicitly failed, so the thread dies.
                    matched = MatchedAnnotation(
                        original_id=annot.id, 
                        parent_id=annot.parent_id, 
                        type="Reply Thread",
                        confidence_score=0.0, 
                        match_reason="Parent Failed",
                        anchor_text=annot.anchor_text, 
                        context_window=annot.context_window,
                        new_page=None, 
                        metadata=annot.metadata, 
                        comment_text=annot.comment_text
                    )
                
                matched_results.append(matched)
                # THE MAGIC FIX: Save the child so its own grandchildren can find it!
                parent_matches[annot.id] = matched 
            else:
                # The parent hasn't been processed yet (it is further down the list)
                still_unresolved.append(annot)
                
        unresolved_children = still_unresolved

    # Failsafe for orphaned children (e.g., if a root parent was completely deleted)
    for annot in unresolved_children:
        matched = MatchedAnnotation(
            original_id=annot.id, 
            parent_id=annot.parent_id, 
            type="Reply Thread",
            confidence_score=0.0, 
            match_reason="Orphaned Thread (Parent Missing)",
            anchor_text=annot.anchor_text, 
            context_window=annot.context_window,
            new_page=None, 
            metadata=annot.metadata, 
            comment_text=annot.comment_text
        )
        matched_results.append(matched)
        parent_matches[annot.id] = matched

    doc.close()
    return matched_results