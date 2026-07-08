# -*- coding: utf-8 -*-
#
# Adı Soyadı: Ceydanur Arslan
# Öğrenci Numarası: 262484066
#
# Adı Soyadı: Sude Yılmaz
# Öğrenci Numarası: 262484068
#
import cv2
import os
import glob

uploads_dir = "uploads"
images = glob.glob(os.path.join(uploads_dir, "*.*"))

print("--- Uploaded Images Info ---")
for img_path in images:
    if img_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        img = cv2.imread(img_path)
        if img is not None:
            print(f"File: {os.path.basename(img_path)} | Size: {img.shape[1]}x{img.shape[0]} (WxH)")
        else:
            print(f"File: {os.path.basename(img_path)} | Could not load")
