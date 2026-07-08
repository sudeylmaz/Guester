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

img = cv2.imread("test.jpeg")
H, W = img.shape[:2]
reader = easyocr.Reader(['tr'], gpu=False)
results = reader.readtext(img)

# Sort strictly by Y coordinate
results_sorted = sorted(results, key=lambda r: sum([p[1] for p in r[0]]) / 4.0)

print(f"Image dimensions: {W}x{H}")
print("\n--- ALL DETECTED TEXTS (TOP TO BOTTOM) ---")
for idx, res in enumerate(results_sorted):
    box, text, conf = res
    y_center = sum([p[1] for p in box]) / 4.0
    x_center = sum([p[0] for p in box]) / 4.0
    print(f"y={y_center:4.1f} | x={x_center:4.1f} | text='{text}'")
