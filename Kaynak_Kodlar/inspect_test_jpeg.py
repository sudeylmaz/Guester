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
import sys

img_path = "test.jpeg"
img = cv2.imread(img_path)

if img is None:
    print("test.jpeg not found")
    sys.exit(1)

H, W = img.shape[:2]
print(f"test.jpeg dimensions: {W}x{H} (WxH)")

reader = easyocr.Reader(['tr'], gpu=False)
results = reader.readtext(img)

# Print all detected texts with their coordinates
print("\n--- Detected Text Coordinates ---")
for idx, res in enumerate(results):
    box, text, conf = res
    y_center = sum([p[1] for p in box]) / 4.0
    x_center = sum([p[0] for p in box]) / 4.0
    height = max([p[1] for p in box]) - min([p[1] for p in box])
    print(f"[{idx:02d}] Text: '{text:<30}' | x={x_center:.1f}, y={y_center:.1f}, h={height:.1f} | Box: {box}")
