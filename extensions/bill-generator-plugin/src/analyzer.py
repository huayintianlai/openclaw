"""PDF Analyzer"""
from dataclasses import dataclass
from typing import Tuple
import fitz

@dataclass
class TextSpan:
    text: str
    bbox: Tuple[float, float, float, float]
    font: str
    font_size: float
    color: Tuple[float, float, float]

class PDFAnalyzer:
    def extract_text_spans(self, pdf_path: str) -> list:
        doc = fitz.open(pdf_path)
        page = doc[0]
        spans = []
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Extract color from span
                        color_int = span.get("color", 0)
                        # Convert integer color to RGB tuple (0-1 range)
                        if color_int == 0:
                            color = (0, 0, 0)  # Black
                        else:
                            r = ((color_int >> 16) & 0xFF) / 255.0
                            g = ((color_int >> 8) & 0xFF) / 255.0
                            b = (color_int & 0xFF) / 255.0
                            color = (r, g, b)

                        spans.append(TextSpan(
                            text=span["text"],
                            bbox=(span["bbox"][0], span["bbox"][1], span["bbox"][2], span["bbox"][3]),
                            font=span["font"],
                            font_size=span["size"],
                            color=color
                        ))
        doc.close()
        return spans
