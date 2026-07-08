# -*- coding: utf-8 -*-
#
# Adı Soyadı: Ceydanur Arslan
# Öğrenci Numarası: 262484066
#
# Adı Soyadı: Sude Yılmaz
# Öğrenci Numarası: 262484068
#
import cv2
import numpy as np

img_path = "uploads/WhatsApp Image 2026-05-13 at 14.43.56.jpeg"
img = cv2.imread(img_path)

if img is None:
    print("Image not found")
    exit(1)

H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Test multiple binarization methods
thresh_gaussian = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 5)
cv2.imwrite("debug_thresh_gaussian.png", cv2.resize(thresh_gaussian, (800, 800)))

# Test horizontal lines detection with different kernel sizes
for k_size in [20, 50, 100]:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, 1))
    h_lines = cv2.morphologyEx(thresh_gaussian, cv2.MORPH_OPEN, kernel, iterations=1)
    cv2.imwrite(f"debug_h_lines_{k_size}.png", cv2.resize(h_lines, (800, 800)))
    print(f"Saved h_lines_{k_size} (Active pixels: {np.sum(h_lines > 0)})")

# Test vertical lines detection with different kernel sizes
for k_size in [20, 50, 100]:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, k_size))
    v_lines = cv2.morphologyEx(thresh_gaussian, cv2.MORPH_OPEN, kernel, iterations=1)
    cv2.imwrite(f"debug_v_lines_{k_size}.png", cv2.resize(v_lines, (800, 800)))
    print(f"Saved v_lines_{k_size} (Active pixels: {np.sum(v_lines > 0)})")
