import fitz
from rapidfuzz import fuzz
from .schemas import MatchedAnnotation
import re
from .config import EngineConfig

def clean_str(text: str) -> str:
    cleaned = re.sub(r'[^\w\s]', '', text).strip().lower()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned

def inject_annotations(matched_annots: list[MatchedAnnotation], edited_pdf_path: str, output_path: str) -> str:
    # takes matched annotations and physically writes them into the final pdf. 
    doc = fitz.open(edited_pdf_path)

    for annot in matched_annots:
        # Skip failed matches or items waiting in manual review queue
        if annot.new_page is None or annot.confidence_score < EngineConfig.MIN_CONFIDENCE_AUTO:
            continue

        page = doc[annot.new_page]

        try:
            # Strategy 1: Gemoetric Injection
            if annot.match_reason == "Relative Geometric Anchor" and annot.new_coordinates:
                # Using raw Coordinates
                rect_tuple = (annot.new_coordinates.x0, annot.new_coordinates.y0, annot.new_coordinates.x1, annot.new_coordinates.y1)
                new_annot = page.add_text_annot((rect_tuple[0], rect_tuple[1]), annot.comment_text)
            # Strategy 2: Semantic Injection
            else:
                # Try exact visual search
                text_instances = page.search_for(annot.anchor_text)

                if text_instances:
                    target_rect = text_instances[0]
                    if annot.type == "Highlight":
                        new_annot = page.add_highlight_annot(target_rect)
                    elif annot.type == "Redaction":
                        new_annot = page.add_redact_annot(target_rect)
                        new_annot.set_colors(stroke=(1, 0, 0))
                    elif annot.type == "Square/Table Highlights":
                        expanded = fitz.Rect(
                            target_rect.x0 - EngineConfig.X_AXIS_PADDING, 
                            target_rect.y0 - EngineConfig.Y_AXIS_PADDING, 
                            target_rect.x1 + EngineConfig.X_AXIS_PADDING, 
                            target_rect.y1 + EngineConfig.Y_AXIS_PADDING
                        )
                        new_annot = page.add_rect_annot(expanded)
                        new_annot.set_colors(stroke=(1, 0, 0))
                    else:
                        new_annot = page.add_text_annot((target_rect.x0 - 20, target_rect.y0), annot.comment_text)
                
                # Spatial Fuzzy Fallback
                else:
                    blocks = page.get_text("blocks")
                    best_block = None
                    best_block_score = 0
                    # Use complete context window if available
                    search_string = annot.context_window if annot.context_window else annot.anchor_text

                    # Find correct paragraph block
                    for b in blocks:
                        if b[6] != 0:
                            continue

                        block_text = b[4].replace("\n", " ")
                        score = fuzz.partial_ratio(search_string, block_text)

                        if score > best_block_score:
                            best_block_score = score
                            best_block = b

                    if best_block and best_block_score > EngineConfig.MIN_CONFIDENCE_REVIEW:
                        # Find specific word inside the block
                        block_rect = fitz.Rect(best_block[:4])
                        all_words = page.get_text("words")

                        block_words = [w for w in all_words if fitz.Rect(w[:4]).intersects(block_rect)]
                        block_words.sort(key=lambda w: (w[1], w[0]))

                        clean_anchor = clean_str(annot.anchor_text)

                        anchor_word_count = len(clean_anchor.split())
                        best_phrase_score = 0
                        target_rect = block_rect

                        # Slide window using cleaned text phrase comparision
                        for window_size in [anchor_word_count - 1, anchor_word_count, anchor_word_count + 1]:
                            if window_size <= 0:
                                continue

                            for i in range(len(block_words) - window_size + 1):
                                window = block_words[i : i + window_size]
                                window_text = " ".join([w[4] for w in window])
                                clean_window = clean_str(window_text)

                                phrase_score = fuzz.ratio(clean_anchor, clean_window)

                                if phrase_score > best_phrase_score:
                                    best_phrase_score = phrase_score

                                    # Calculate custom bounding box containing just these words
                                    x0 = min([w[0] for w in window])
                                    y0 = min([w[1] for w in window])
                                    x1 = max([w[2] for w in window])
                                    y1 = max([w[3] for w in window])
                                    target_rect = fitz.Rect(x0, y0, x1, y1)

                        if annot.type == "Highlight":
                            new_annot = page.add_highlight_annot(target_rect)
                        elif annot.type == "Redaction":
                            new_annot = page.add_redact_annot(target_rect)
                            new_annot.set_colors(stroke=(1, 0, 0))
                        elif annot.type == "Square/Table Highlights":
                            expanded = fitz.Rect(
                            target_rect.x0 - EngineConfig.X_AXIS_PADDING, 
                            target_rect.y0 - EngineConfig.Y_AXIS_PADDING, 
                            target_rect.x1 + EngineConfig.X_AXIS_PADDING, 
                            target_rect.y1 + EngineConfig.Y_AXIS_PADDING
                        )
                            new_annot = page.add_rect_annot(expanded)
                            new_annot.set_colors(stroke=(1, 0, 0))
                        elif annot.type == "Insertion Caret":
                            new_annot = page.add_caret_annot(target_rect.top_left)
                        elif annot.type == "FreeText Margin":
                            new_annot = page.add_freetext_annot(target_rect, annot.comment_text)
                        else:
                            new_annot = page.add_text_annot((target_rect.x0 - 20, target_rect.y0), annot.comment_text)

                    else: 
                        new_annot = page.add_text_annot((50, 50), annot.comment_text)


            # Preserve Chain of Custody
            new_annot.set_info({
                "title": annot.metadata.author,
                "content": annot.comment_text,
                "creationDate": annot.metadata.creation_date,
                "modDate":annot.metadata.modification_date
            })
            new_annot.update()

        except Exception as e:
            print(f"Warning: Failed to inject comment '{annot.comment_text}' - {e}")
            continue

    doc.save(output_path)
    doc.close()
    return output_path