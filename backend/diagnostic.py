"""
Diagnostic script to test conversion pipeline
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.file_utils import get_temp_dir
from utils.model_utils import create_chat_model, call_model_with_image
from pdf2image import convert_from_path
from PyPDF2 import PdfReader

def test_pdf_conversion(pdf_path):
    """Test PDF to image conversion"""
    print(f"\n=== Testing PDF conversion ===")
    print(f"PDF path: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        print(f"[OK] PDF has {page_count} pages")

        print("Converting first page to image (150 DPI)...")
        images = convert_from_path(pdf_path, dpi=150, first_page=1, last_page=1)
        print(f"[OK] Converted {len(images)} page(s)")

        test_dir = os.path.join(get_temp_dir(), "diagnostic")
        os.makedirs(test_dir, exist_ok=True)
        test_img_path = os.path.join(test_dir, "test_page.png")
        images[0].save(test_img_path, "PNG")
        img_size = os.path.getsize(test_img_path)
        print(f"[OK] Saved test image: {test_img_path}")
        print(f"  Image size: {img_size / 1024 / 1024:.2f} MB")

        return test_img_path

    except Exception as e:
        print(f"[FAIL] PDF conversion failed: {e}")
        traceback.print_exc()
        return None

def test_model_api(model_name, image_path):
    """Test model API call"""
    print(f"\n=== Testing model API ===")
    print(f"Model: {model_name}")

    try:
        if model_name not in settings.MODELS:
            print(f"[FAIL] Model '{model_name}' not found in config")
            return False

        model_config = settings.MODELS[model_name]
        print(f"[OK] Model config found")

        api_key_env = model_config.get("api_key_env")
        api_key = os.getenv(api_key_env, "") if api_key_env else ""
        if not api_key:
            print(f"[FAIL] API key not set for env var: {api_key_env}")
            return False
        print(f"[OK] API key found (length: {len(api_key)})")

        print("Creating chat model...")
        llm = create_chat_model(model_name)
        print(f"[OK] Model created")

        if image_path and os.path.exists(image_path):
            print("Testing multimodal call with image...")
            prompt = "Please describe this image in one sentence."
            result = call_model_with_image(
                model_name=model_name,
                prompt=prompt,
                image_path=image_path,
                system_prompt="You are an image description assistant."
            )
            print(f"[OK] API call successful")
            print(f"  Response: {result[:200]}")
            return True
        else:
            print("[WARN] No image to test multimodal call")
            return False

    except Exception as e:
        print(f"[FAIL] Model API test failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Chip Spec Agent - Diagnostic Test")
    print("=" * 60)

    temp_dir = get_temp_dir()
    pdf_path = None

    print(f"\nLooking for PDF files in: {temp_dir}")
    if os.path.exists(temp_dir):
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                for f in os.listdir(item_path):
                    if f.endswith('.pdf'):
                        pdf_path = os.path.join(item_path, f)
                        break
            if pdf_path:
                break

    if not pdf_path:
        print("[ERROR] No PDF files found in temp directory")
        print("  Please upload a PDF first via the web interface")
        return

    print(f"Found PDF: {pdf_path}")

    test_img_path = test_pdf_conversion(pdf_path)
    test_model_api("Kimi-K2.6", test_img_path)

    print("\n" + "=" * 60)
    print("Diagnostic complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
