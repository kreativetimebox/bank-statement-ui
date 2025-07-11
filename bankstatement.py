# service.py
import os
import pdfplumber
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import google.generativeai as genai

# Configure the API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY","AIzaSyBKF4R4QfdKcrAVvQh2KAZk5jlnB_cKEsg" ))
model = genai.GenerativeModel("gemma-3-27b-it")


def classify_document_type(text: str) -> str:
    """
    Uses an LLM to classify the document type from raw text (PDF or OCR).
    Returns one of: bank_statement, invoice, receipt, utility_bill, unknown
    """
    classification_prompt = f"""
You are a document classification AI.

Your task is to read the raw OCR or extracted text from a document, including text extracted from scanned documents such as scanned bank statements, and proceed with classifying it into one of the following categories:

bank_statement
invoice
receipt
utility_bill
unknown
Ensure that scanned bank statements are processed and classified as "bank_statement" when appropriate, even if the text is extracted from a scanned source.

Respond with only the document type — no extra words, explanation, or formatting.

TEXT:
{text}
"""

    try:
        response = model.generate_content(
            classification_prompt,
            generation_config={"temperature": 0.0, "max_output_tokens": 10}
        )
        doc_type = response.text.strip().lower()

        # Sanitize & validate response
        allowed = ["bank_statement", "invoice", "receipt", "utility_bill", "unknown"]
        return doc_type if doc_type in allowed else "unknown"

    except Exception as e:
        print(f"[LLM Classification Error]: {e}")
        return "unknown"


def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join([p.extract_text() or "" for p in pdf.pages])
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_images_from_pdf(pdf_path, output_folder="images"):
    try:
        os.makedirs(output_folder, exist_ok=True)
        images = convert_from_path(pdf_path)
        paths = []
        for i, img in enumerate(images):
            path = f"{output_folder}/page_{i+1}.png"
            img.save(path, "PNG")
            paths.append(path)
        return paths
    except Exception as e:
        return f"Error extracting images: {str(e)}"

def ocr_image(image_path):
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"Error performing OCR: {str(e)}"

def process_pdf_with_gemma(pdf_path, prompt: str) -> str:
    text = extract_text_from_pdf(pdf_path)
    image_paths = extract_images_from_pdf(pdf_path)

    # OCR fallback
    if isinstance(image_paths, list):
        for path in image_paths:
            text += "\n" + ocr_image(path)

    # Input to Gemini
    inputs = [f"{prompt}:\n{text}"]
    if isinstance(image_paths, list) and image_paths:
        try:
            inputs.append(genai.upload_file(image_paths[0]))
        except Exception as e:
            print(f"Error uploading image to Gemini: {str(e)}")

    try:
        response = model.generate_content(
            inputs,
            generation_config={"max_output_tokens": 50000, "temperature": 0.7}
        )
        return response.text
    except Exception as e:
        return f"Error querying Gemini: {str(e)}"