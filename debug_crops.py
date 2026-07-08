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
import guester_ocr

img_path = "uploads/liste 1.jpg!bw800"
img = cv2.imread(img_path)

if img is None:
    print("Image not found")
    exit(1)

# Tablo tespiti ve warp
contour = guester_ocr.find_table_contour(img)
if contour is not None:
    warped = guester_ocr.warp_table(img, contour)
else:
    warped = cv2.resize(img, (750, 1640))

# Kaydet
cv2.imwrite("debug_warped.png", warped)

# Row 4 (r=4)
r = 4
row_height = 40
ymin = r * row_height
ymax = ymin + row_height

# Kolonlar
col_bounds = {
    "AD": (3, 297),
    "SOYAD": (303, 597),
    "MASA_NO": (603, 747)
}

for col_name, (xmin, xmax) in col_bounds.items():
    cell_img = warped[ymin+2:ymax-2, xmin:xmax]
    out_path = f"debug_row_{r}_{col_name}.png"
    cv2.imwrite(out_path, cell_img)
    print(f"Saved {out_path} with size {cell_img.shape[1]}x{cell_img.shape[0]}")

# Row 6 (r=6)
r = 6
ymin = r * row_height
ymax = ymin + row_height

for col_name, (xmin, xmax) in col_bounds.items():
    cell_img = warped[ymin+2:ymax-2, xmin:xmax]
    out_path = f"debug_row_{r}_{col_name}.png"
    cv2.imwrite(out_path, cell_img)
    print(f"Saved {out_path} with size {cell_img.shape[1]}x{cell_img.shape[0]}")
