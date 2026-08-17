import os
import re
import html
import logging
from fpdf import FPDF
from config import DEJAVU_FONT, DEJAVU_BOLD, DEJAVU_OBLIQUE, APP_TITLE

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# SÉCURITÉ & NETTOYAGE
# ═══════════════════════════════════════════════════════════════════════════════
def sanitize_filename(name: str) -> str:
    """Supprime les caractères dangereux dans un nom de fichier."""
    name = os.path.basename(name)
    name = re.sub(r'[^\w\-. ]', '_', name)
    return name[:200]

def safe_html(text: str) -> str:
    """Échappe le HTML pour éviter les injections XSS."""
    return html.escape(text)

# ═══════════════════════════════════════════════════════════════════════════════
# LINGUISTIQUE
# ═══════════════════════════════════════════════════════════════════════════════
def is_arabic(text: str) -> bool:
    """Détecte si le texte contient des caractères arabes."""
    return bool(re.search(r'[\u0600-\u06FF]', text))

def extract_article_numbers(text: str, arabic_mode: bool = False) -> list:
    """Extrait les numéros d'articles mentionnés."""
    fr_raw = re.findall(r'(?:Art(?:icle|\.)?)\s*(\d+|premier|1er)', text, re.IGNORECASE)
    fr = ["1" if x.lower() in ("premier", "1er") else x for x in fr_raw]
    ar = re.findall(r'المادة\s*(\d+)', text)
    combined = (ar + fr) if arabic_mode else (fr + ar)
    return list(dict.fromkeys(combined))

# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR PDF
# ═══════════════════════════════════════════════════════════════════════════════
class LegalReportPDF(FPDF):
    """PDF professionnel avec support Unicode."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fonts_loaded = False

    def _load_fonts(self):
        if self._fonts_loaded:
            return True
        if not os.path.exists(DEJAVU_FONT):
            return False
        try:
            self.add_font("DejaVu", "", DEJAVU_FONT, uni=True)
            if os.path.exists(DEJAVU_BOLD):
                self.add_font("DejaVu", "B", DEJAVU_BOLD, uni=True)
            if os.path.exists(DEJAVU_OBLIQUE):
                self.add_font("DejaVu", "I", DEJAVU_OBLIQUE, uni=True)
            self._fonts_loaded = True
            return True
        except Exception as exc:
            logger.warning("DejaVu load failed: %s", exc)
            return False

    def _font(self, size: int = 11, style: str = ""):
        if self._load_fonts():
            self.set_font("DejaVu", style, size)
        else:
            self.set_font("Arial", style, size)

    def header(self):
        self._font(14, "B")
        self.set_text_color(220, 60, 60)
        self.cell(0, 10, APP_TITLE, align="C", ln=1)
        self._font(9)
        self.set_text_color(140, 140, 160)
        self.cell(0, 6, "Rapport de consultation juridique", align="C", ln=1)
        self.ln(4)
        self.set_draw_color(60, 65, 90)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self._font(8, "I")
        self.set_text_color(150, 150, 170)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

def build_pdf(question: str, answer: str, sources: list) -> bytes:
    """Génère un rapport PDF et retourne les bytes."""
    pdf = LegalReportPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    w = pdf.epw

    pdf._font(11, "B")
    pdf.set_text_color(200, 60, 60)
    pdf.multi_cell(w, 8, f"Question : {question or '—'}")
    pdf.ln(3)

    pdf._font(11, "B")
    pdf.set_text_color(60, 180, 140)
    pdf.cell(w, 8, "Réponse :", ln=1)
    pdf._font(10)
    pdf.set_text_color(30, 30, 40)
    pdf.multi_cell(w, 7, answer or "(Aucune réponse)")

    if sources:
        pdf.ln(8)
        pdf._font(11, "B")
        pdf.set_text_color(200, 60, 60)
        pdf.cell(w, 8, "Source(s) :", ln=1)
        for idx, src in enumerate(sources, 1):
            pdf.ln(3)
            pdf._font(9, "I")
            pdf.set_text_color(100, 110, 140)
            pdf.cell(w, 7, f"— Source {idx} :", ln=1)
            pdf._font(9)
            pdf.set_text_color(40, 40, 55)
            pdf.multi_cell(w, 6, src)

    raw = pdf.output()
    return bytes(bytearray(raw)) if isinstance(raw, bytearray) else bytes(raw)
