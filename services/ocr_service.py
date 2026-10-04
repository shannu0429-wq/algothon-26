import os
import re
from PIL import Image
import pytesseract

def get_tesseract_command():
    standard_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for path in standard_paths:
        if os.path.exists(path):
            return path
    return "tesseract"

def is_ocr_available():
    cmd = get_tesseract_command()
    pytesseract.pytesseract.tesseract_cmd = cmd
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def clean_ocr_text(text):
    if not text:
        return ""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()

def extract_text_from_image(image_path):
    cmd = get_tesseract_command()
    pytesseract.pytesseract.tesseract_cmd = cmd
    try:
        with Image.open(image_path) as img:
            img = img.convert("L")
            raw_text = pytesseract.image_to_string(img)
            cleaned = clean_ocr_text(raw_text)
            if not cleaned:
                return "", "no readable text could be detected from this image."
            return cleaned, None
    except Exception as exc:
        return "", f"ocr processing is unavailable: {str(exc).lower()}"
