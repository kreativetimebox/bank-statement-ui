from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
from extraction import process_invoice_document, process_receipt_document
from image_processor import ImageProcessor , INVOICE_PROMPT, RECEIPT_PROMPT
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import tempfile
import json
from fastapi import FastAPI, File, UploadFile
import uuid
from bankstatement import process_pdf_with_gemma , extract_text_from_pdf, classify_document_type
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import logging

# Configure logger
logger = logging.getLogger("gemma3")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/parse-invoice/")
async def parse_invoice(file: UploadFile = File(...)):
    try:
        if not file.filename:
            return JSONResponse(content={"error": "No filename provided."}, status_code=400)
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = process_invoice_document(pdf_path=file_path)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/parse-receipt/")
async def parse_receipt(file: UploadFile = File(...)):
    try:
        if not file.filename:
            return JSONResponse(content={"error": "No filename provided."}, status_code=400)
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = process_receipt_document(pdf_path=file_path)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    


GEMINI_API_KEY = "AIzaSyAVa8rPSAh8WFQXGbX8sUmSQNGY17vuD4Q"
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

@app.post("/api/invoice")
async def process_invoice(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        logger.error("Invalid file type: %s", file.content_type)
        raise HTTPException(status_code=400, detail="File must be an image (png, jpg, jpeg)")

    temp_path = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            content = await file.read()
            if not content:
                logger.error("Empty file uploaded")
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            tmp.write(content)
            temp_path = tmp.name
        logger.info("Temporary file created: %s", temp_path)

        # Process image with Gemini API
        processor = ImageProcessor(prompt=INVOICE_PROMPT)
        logger.info("Validating image as invoice")
        result = processor.analyze_image(temp_path, expected_type="invoice")
        logger.info("Image processing completed")

        # Ensure all required fields are present
        required_fields = {
            "supplier_name": "",
            "invoice_date": "",
            "total_amount": "",
            "tax_amount": "",
            "due_date": None,
            "currency": None,
            "items": []
        }
        for field in required_fields:
            if field not in result:
                logger.warning("Missing field %s in result, setting default", field)
                result[field] = required_fields[field]

        # Ensure items have all required subfields
        item_fields = ["description", "quantity", "unit_price", "total_price"]
        for item in result.get("items", []):
            for field in item_fields:
                if field not in item:
                    logger.warning("Missing item field %s, setting to None", field)
                    item[field] = None

        return result
    except ValueError as ve:
        logger.error("Validation error: %s", str(ve))
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(ve)}")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing invoice: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info("Temporary file deleted: %s", temp_path)
            except Exception as e:
                logger.error("Error deleting temporary file: %s", str(e))

@app.post("/api/receipt")
async def process_receipt(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        logger.error("Invalid file type: %s", file.content_type)
        raise HTTPException(status_code=400, detail="File must be an image (png, jpg, jpeg)")

    temp_path = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            content = await file.read()
            if not content:
                logger.error("Empty file uploaded")
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            tmp.write(content)
            temp_path = tmp.name
        logger.info("Temporary file created: %s", temp_path)

        # Process image with Gemini API
        processor = ImageProcessor(prompt=RECEIPT_PROMPT)
        logger.info("Validating image as receipt")
        result = processor.analyze_image(temp_path, expected_type="receipt")
        logger.info("Image processing completed")

        # Ensure all required fields are present
        required_fields = {
            "store_name": "",
            "date": "",
            "currency": "",
            "total_amount": "",
            "tax_details": "",
            "transaction_number": "",
            "card_details": "",
            "service_fee": "",
            "items": []
        }
        for field in required_fields:
            if field not in result:
                logger.warning("Missing field %s in result, setting default", field)
                result[field] = required_fields[field]

        # Ensure items have all required subfields
        item_fields = ["name", "description", "price", "unit_price", "quantity", "discount", "total", "line_total"]
        for item in result.get("items", []):
            for field in item_fields:
                if field not in item:
                    logger.warning("Missing item field %s, setting to empty string", field)
                    item[field] = ""

        return result
    except ValueError as ve:
        logger.error("Validation error: %s", str(ve))
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(ve)}")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing receipt: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info("Temporary file deleted: %s", temp_path)
            except Exception as e:
                logger.error("Error deleting temporary file: %s", str(e))

@app.options("/api/invoice")
async def options_invoice():
    return {}

@app.options("/api/receipt")
async def options_receipt():
    return {}

GEMMA_PROMPT = """
You are UKBankParseGPT, a financial AI specialized in parsing **UK bank statements**.

GOAL: From raw OCR/text of a bank statement, return valid JSON with:

Top-Level Fields:
- account_holder_name (string)
- account_number       (string)
- bank_name            (string)
- statement_period     (string)
- opening_balance      (string)
- closing_balance      (string)
- currency             (string)

transactions (array of objects):
- date         (string, yyyy-mm-dd)
- description  (string)
- money_in     (string|null)
- money_out    (string|null)
- balance      (string|null)

RULES:
- Output STRICT JSON only — no markdown, comments, or explanations.
- Use null for missing or ambiguous fields.
- Dates must be yyyy-mm-dd
- Ignore non-transactional content
Only return the final JSON object.
"""


UPLOAD_DIR1 = "uploads"
os.makedirs(UPLOAD_DIR1, exist_ok=True)
@app.post("/parse-bank-statement/")
async def parse_bank_statement(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            return JSONResponse(content={"error": "Only PDF files are allowed."}, status_code=400)

        # Save uploaded PDF
        pdf_path = os.path.join(UPLOAD_DIR1, file.filename)
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        

        raw_text = extract_text_from_pdf(pdf_path)

        '''doc_type = classify_document_type(raw_text)

        if doc_type != "bank_statement":
            return JSONResponse(
                content={"error": f"Invalid document type: {doc_type}. Only bank statements are supported."},
                status_code=400
            )'''



        # Process PDF (includes classification and bank statement check)
        result = process_pdf_with_gemma(pdf_path, GEMMA_PROMPT)

        # Check if result is an error message
        if result.startswith("Error"):
            return JSONResponse(content={"error": result}, status_code=400)

        # Strip markdown formatting and parse JSON
        clean_json_str = result.strip().removeprefix("```json").removesuffix("```").strip()
        parsed = json.loads(clean_json_str)  # Convert to JSON object

        return {"result": parsed}

    except Exception as e:
        return JSONResponse(content={"error": f"Failed to process the bank statement: {str(e)}"}, status_code=500)


'''@app.post("/parse-bank-statement/")
async def parse_bank_statement(file: UploadFile = File(...)):
    pdf_path = None
    try:
        if not file.filename.lower().endswith(".pdf"):
            return JSONResponse(content={"error": "Only PDF files are allowed."}, status_code=400)

        pdf_path = os.path.join(UPLOAD_DIR1, file.filename)
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = process_pdf_with_gemma(pdf_path, GEMMA_PROMPT)
        if result.startswith("Error"):
            return JSONResponse(content={"error": result}, status_code=400)

        clean_json_str = result.strip()
        logger.debug(f"Raw LLM JSON response: {clean_json_str}")

        try:
            parsed = json.loads(clean_json_str)
            return {"result": parsed}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return JSONResponse(
                content={"error": f"Invalid JSON response from model: {str(e)}"},
                status_code=400
            )
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return JSONResponse(content={"error": f"Failed to process the bank statement: {str(e)}"}, status_code=500)
    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)'''