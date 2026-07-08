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

img = cv2.imread("test.jpeg.jpeg")
reader = easyocr.Reader(["tr"], gpu=False)

col_boundaries = {
    "AD": (75, 345),
    "SOYAD": (375, 640),
    "MASA_NO": (700, 800)
}
row_ys = [337, 370, 401, 432, 463, 493, 524, 555, 586, 617, 648]

for row_idx in range(5):
    ymin = max(0, row_ys[row_idx] - 3)
    ymax = min(img.shape[0], row_ys[row_idx + 1] + 3)
    
    print(f"\n--- Row {row_idx+1} ---")
    for col_name, (xmin, xmax) in col_boundaries.items():
        cell_img = img[ymin:ymax, xmin:xmax]
        
        # 1. Binary method (from our previous run)
        c_gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
        c_thresh = cv2.adaptiveThreshold(
            c_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 10
        )
        # Erase border on binary
        c_thresh_clean = c_thresh.copy()
        c_thresh_clean[0:4, :] = 0
        c_thresh_clean[-4:, :] = 0
        c_thresh_clean[:, 0:4] = 0
        c_thresh_clean[:, -4:] = 0
        
        binary_cleaned = cv2.bitwise_not(c_thresh_clean)
        binary_zoomed = cv2.resize(binary_cleaned, (0, 0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        binary_padded = cv2.copyMakeBorder(binary_zoomed, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255,255,255])
        
        # 2. Grayscale method (No thresholding, soft edges preserved)
        gray_cell = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
        # Erase border by painting it white (255)
        gray_cleaned = gray_cell.copy()
        gray_cleaned[0:4, :] = 255
        gray_cleaned[-4:, :] = 255
        gray_cleaned[:, 0:4] = 255
        gray_cleaned[:, -4:] = 255
        
        gray_zoomed = cv2.resize(gray_cleaned, (0, 0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        gray_padded = cv2.copyMakeBorder(gray_zoomed, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255,255,255])
        
        # OCR
        res_bin = reader.readtext(binary_padded)
        res_gray = reader.readtext(gray_padded)
        
        text_bin = " ".join([r[1] for r in res_bin]).strip() if res_bin else ""
        text_gray = " ".join([r[1] for r in res_gray]).strip() if res_gray else ""
        
        print(f"  {col_name}:")
        print(f"    Binary:    '{text_bin}'")
        print(f"    Grayscale: '{text_gray}'")