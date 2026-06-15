import fitz

def extract_annotations(pdf_path: str) -> list[dict]:

    doc = fitz.open(pdf_path)
    extracted_annots = []

    ANNOT_TYPES = {
        0: "Sticky Note",
        2: "FreeText Margin",
        8: "Highlight",
        14: "Insertion Caret"
    }

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text("text")
        normalized_page_text = " ".join(page_text.split())
        for annot in page.annots():
            if annot.type[0] == 8:
                # Get the annotation's rectangle coordinates
                rect = annot.rect

                # Extract the text within the annotation's rectangle
                highlighted_text = page.get_text("text", clip=rect).strip()
                normalized_highlight = " ".join(highlighted_text.split())

                # Get actual annotation content 
                comment_text = annot.info.get("content", "").strip()

                # Generate semantic context window
                context_window = ""
                if normalized_highlight in normalized_page_text:
                    start_idx = normalized_page_text.find(normalized_highlight)
                    end_idx = start_idx + len(normalized_highlight)

                    prefix = normalized_page_text[max(0, start_idx -50):start_idx]
                    suffix = normalized_page_text[end_idx:end_idx + 50]
                    context_window = f"{prefix}{normalized_highlight}{suffix}"

                # Append the structured "fingerprint" dictionary
                extracted_annots.append({
                    "id": annot.id,
                    "page":page_num,
                    "highlighted_text": normalized_highlight,
                    "comment_text": comment_text,
                    "context_window": context_window
                })
    doc.close()
    return extracted_annots

