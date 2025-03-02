import ollama
import easyocr
import fitz
import os
from pathlib import Path
from datetime import datetime as dt
from enum import Enum

WITH_LOGS = True

class ChatModel(Enum):
    PHI4 = "phi4"
    MISTRAL = "mistral"
    LLAMA32 = "llama3.2"
    GRANITE32 = "granite3.2-vision"

def dt_now():
    return dt.now().strftime("%Y-%m-%d %H:%M:%S")

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

def extract_text_from_image(image_path):
    reader = easyocr.Reader(["en"])
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)

def process_document(file_path):
    ext = Path(file_path).suffix.replace(".", "")

    if ext in ["pdf"]:
        return extract_text_from_pdf(file_path)

    if ext in ["jpg", "jpeg", "png"]:
        return extract_text_from_image(file_path)

    return ""

def analyze_with_model(text):
    SYSTEM_PROMPT_PATH = os.path.join(os.getcwd(), r"ocr\system_prompts\ocr_expert.txt")
    USER_PROMPT_PATH = os.path.join(os.getcwd(), r"ocr\user_prompts\prompt_2.txt")

    with open(file=SYSTEM_PROMPT_PATH, mode="r", encoding="utf-8") as file:
        system_prompt = file.read()
        file.close()

    with open(file=USER_PROMPT_PATH, mode="r", encoding="utf-8") as file:
        user_prompt = file.read()
        user_prompt = user_prompt.replace("{document_text}", text)
        file.close()

    response = ollama.chat(
        model=ChatModel.PHI4.value,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0}
    )
    
    return response["message"]["content"]


def run_ocr():
    start_time = dt.now()
    if WITH_LOGS:
        print(f"START - {dt_now()}")
        print("=========================================")

    DOCUMENTS_PATH = os.path.join(os.getcwd(), r"ocr\documents")

    for file_name in os.listdir(DOCUMENTS_PATH):
        file_path = os.path.join(DOCUMENTS_PATH, file_name)

        if os.path.isfile(file_path):
            print(f"START - PROCESSING FILE {file_name} - {dt_now()}")
            extracted_text = process_document(file_path=file_path)
            print(f"END - PROCESSING FILE {file_name} - {dt_now()}")
            print("=========================================")
            if extracted_text:
                print(f"START - ANALYZING FILE {file_name} - {dt_now()}")
                print(analyze_with_model(extracted_text))
                print(f"END - ANALYZING FILE {file_name} - {dt_now()}")
                print("=========================================")
            else:
                print("NO TEXT")

    print(f"END - {dt_now()} - Total exec time:  {round((dt.now() - start_time).total_seconds() / 60)} minutes")

run_ocr()