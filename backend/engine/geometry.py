import fitz
from typing import Tuple, List, Dict, Any
import math

def get_true_coordinates(rect: fitz.Rect, derotation_matrix: fitz.Matrix) -> fitz.Rect:
    # Applies derotation matrix to a bounding box
    # Crucial for PDFs where users have rotated individual pages.

    return rect * derotation_matrix

def calculate_overlap_percentage(rect1: fitz.Rect, rect2: fitz.Rect) -> float:
    # Calculates how much of rect1 covered by rect2.
    # Used to determine if a comment is truly attached to an image/table or just near it.
    intersect = rect1.intersect(rect2)
    if intersect.is_empty:
        return 0.0
    
    area_rect1 = rect1.get_area()
    if area_rect1 == 0:
        return 0.0
    
    return intersect.get_area() / area_rect1

def to_relative_coordinates(rect: fitz.Rect, page_width: float, page_height: float) -> dict:
    # Converts absolute pixel coordinates to percentage-based layout coordinates

    return {
        "rel_x0": rect.x0 / page_width,
        "rel_y0": rect.y0 / page_height,
        "rel_x1": rect.x1 / page_width,
        "rel_y1": rect.y1 / page_height
    }

def from_relative_coordinates(rel_coords: dict, new_page_width: float, new_page_height: float) -> fitz.Rect:
    # Translates percentage based coordinates back into exact pixels for a new page. 
    return fitz.Rect(
        rel_coords["rel_x0"] * new_page_width,
        rel_coords["rel_y0"] * new_page_height,
        rel_coords["rel_x1"] * new_page_width,
        rel_coords["rel_y1"] * new_page_height
    )

def find_closest_word(target_x: float, target_y: float, words_list: List[Tuple]) -> str:
    # Finds the specific word closest to an exact X/Y coordinate point
    if not words_list:
        return ""
    
    closest_word = sorted(
        words_list,
        key=lambda w: math.hypot(w[0] - target_x, w[1] - target_y)
    )
    return closest_word[0][4]

def is_same_line(y1:float, y2: float, tolderance: float = 10.0) -> bool:
    # Determines if two Y-coordinates belong to the same visual text line. 
    return abs(y1 - y2) <= tolderance
