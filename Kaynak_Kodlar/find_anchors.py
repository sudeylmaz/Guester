# -*- coding: utf-8 -*-
#
# Adı Soyadı: Ceydanur Arslan
# Öğrenci Numarası: 262484066
#
# Adı Soyadı: Sude Yılmaz
# Öğrenci Numarası: 262484068
#
import easyocr
import cv2
import sys

img_path = "uploads/WhatsApp Image 2026-05-13 at 14.43.56.jpeg"
img = cv2.imread(img_path)

if img is None:
    print("Image not found")
    sys.exit(1)

print("Initializing EasyOCR...")
reader = easyocr.Reader(['tr'], gpu=False)

print("Running OCR on full image to locate anchors...")
results = reader.readtext(img)

print("\n--- Detected Texts ---")
for res in results:
    box, text, conf = res
    text_clean = text.upper().strip()
    if any(k in text_clean for k in ["AD", "SOYAD", "MASA"]):
        print(f"ANCHOR FOUND: '{text}' | Box: {box} | Conf: {conf:.2f}")
    else:
        # Print first 20 characters of other text
        print(f"  Text: '{text[:20]}' | Box: {box}")
