import fitz

def extract_annotations(pdf_path: str) -> list[dict]:

    doc = fitz.open(pdf_path)
    extracted_annots = []

    ANNOT_TYPES = {
        0: "Sticky Note",
        2: "FreeText Margin",
        4: "Square/Table Highlights",
        8: "Highlight",
        11: "Redaction",
        14: "Insertion Caret"
    }

    for page_num in range(len(doc)):
        page = doc[page_num]

        page_text = page.get_text("text")
        normalized_page_text = " ".join(page_text.split())
        words_with_coords = page.get_text("words")

        image_list = page.get_images(full=True)
        image_rects = [page.get_image_bbox(img) for img in image_list] if image_list else []

        derotation_matrix = page.rotation_matrix

        for annot in page.annots():
            annot_type_int = annot.type[0]
            if annot_type_int not in ANNOT_TYPES:
                continue
            
            true_rect = annot.rect * derotation_matrix

            author = annot.info.get("title", "Unknown")
            creation_date = annot.info.get("creationDate", "")
            mod_date = annot.info.get("modDate", "")
            comment_text = annot.info.get("content", "").strip()

            parent_id = str(annot.irt_xref) if annot.irt_xref > 0 else None

            highlighted_text = ""
            context_window = ""
            anchor_strategy = "semantic_text" #default

            # Highlight and Redaction Annotations
            if annot_type_int in [8, 11]:
                highlighted_text = " ".join(page.get_text("text", clip=true_rect).split()).strip()

            # Insertion Caret Annotations
            elif annot_type_int == 14:
                closest_words = sorted(
                    words_with_coords,
                    key=lambda w: abs(w[1] - true_rect.y0) + abs(w[0] - true_rect.x0)
                )
                if closest_words:
                    target_word = closest_words[0][4]
                    highlighted_text = target_word if target_word in normalized_page_text else "[Insertion]"

            # Margin and square annotations    
            elif annot_type_int in [0, 2, 4]:
                is_image_anchor = False

                # Check if the annotation overlaps an image
                for img_rect in image_rects:
                    if true_rect.intersects(img_rect):
                        is_image_anchor = True
                        highlighted_text = "[Image Anchor]"
                        anchor_strategy = "image_caption"
                        break
                
                if not is_image_anchor:
                    same_line_words = [w for w in words_with_coords if abs(w[1] - true_rect.y0) < 15]
                    if same_line_words:
                        same_line_words.sort(key=lambda w: w[0])
                        highlighted_text = same_line_words[0][4]
                    else:
                        # Blank space fallback
                        anchor_strategy = "relative_geometry"

                
                # Context window generation
            if anchor_strategy == "semantic_text" and highlighted_text and highlighted_text in normalized_page_text:
                start_idx = normalized_page_text.find(highlighted_text)
                end_idx = start_idx + len(highlighted_text)
                prefix = normalized_page_text[max(0, start_idx - 50):start_idx]
                suffix = normalized_page_text[end_idx:end_idx + 50]
                context_window = f"{prefix}{highlighted_text}{suffix}"

            elif anchor_strategy == "image_caption":
                # Fallback context to be handled by geometry caption search later
                context_window = "[Image Alignment Logic Required]"
                
            elif anchor_strategy == "relative_geometry":
                # Save percentage based co-ordinates instead of exact text
                page_width, page_height = page.rect.width, page.rect.height
                context_window = f"REL_X:{true_rect.x0 / page_width: .3f}_REL_Y:{true_rect.y0 / page_height: .3f}"

                
            #Append structure object
            extracted_annots.append({
                "id": str(annot.xref),
                "parent_id": parent_id,
                "type": ANNOT_TYPES[annot_type_int],
                "page": page_num,
                "strategy": anchor_strategy,
                "coordinates": {
                    "x0": true_rect.x0, "y0": true_rect.y0,
                    "x1": true_rect.x1, "y1": true_rect.y1
                },
                "metadata": {
                    "author": author,
                    "creation_date": creation_date,
                    "modification_date": mod_date
                },
                "anchor_text": highlighted_text,
                "comment_text": comment_text,
                "context_window": context_window
            })

        doc.close()
        return extracted_annots
