# -*- coding: utf-8 -*-
#
# Adı Soyadı: Ceydanur Arslan
# Öğrenci Numarası: 262484066
#
# Adı Soyadı: Sude Yılmaz
# Öğrenci Numarası: 262484068
#
import cv2
import easyocr
import numpy as np

img = cv2.imread("test.jpeg.jpeg")
reader = easyocr.Reader(["tr"], gpu=False)

col_boundaries = {
    "MASA_NO": (700, 800)
}
row_ys = [337, 370, 401, 432, 463, 493, 524, 555, 586, 617, 648]

targets = [2, 6] # Row 3 and Row 7

for row_idx in targets:
    ymin = max(0, row_ys[row_idx] - 4)
    ymax = min(img.shape[0], row_ys[row_idx + 1] + 4)
    xmin, xmax = col_boundaries["MASA_NO"]
    cell_img = img[ymin:ymax, xmin:xmax]
    
    gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 10
    )
    
    # Line subtraction
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
    h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=1)
    subtracted = cv2.subtract(thresh, h_lines)
    
    # Let's test different dilation kernels
    kernels = {
        "No Dilation": None,
        "Dilate 2x2": cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)),
        "Dilate 3x3": cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
        "Dilate 1x2 (vertical)": cv2.getStructuringElement(cv2.MORPH_RECT, (1, 2)),
        "Dilate 2x1 (horizontal)": cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
    }
    
    print(f"\n--- Row {row_idx+1} (Expected: 7) ---")
    for name, kernel in kernels.items():
        if kernel is not None:
            processed = cv2.dilate(subtracted, kernel, iterations=1)
        else:
            processed = subtracted
            
        cleaned = cv2.bitwise_not(processed)
        zoomed = cv2.resize(cleaned, (0, 0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        padded = cv2.copyMakeBorder(zoomed, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        
        result = reader.readtext(padded, allowlist="0123456789")
        text = "".join([res[1] for res in result]).strip() if result else ""
        print(f"  {name:<25} -> OCR: '{text}'")