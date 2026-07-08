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

reader = easyocr.Reader(['tr'], gpu=False)

def test_cell(path, allowlist=None):
    img = cv2.imread(path)
    # pre-process
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    zoomed = cv2.resize(gray, (0, 0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    padded = cv2.copyMakeBorder(zoomed, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    
    # Read without allowlist
    res_raw = reader.readtext(padded)
    text_raw = " ".join([r[1] for r in res_raw]).strip() if res_raw else ""
    
    # Read with allowlist if provided
    text_allowed = ""
    if allowlist:
        res_allow = reader.readtext(padded, allowlist=allowlist)
        text_allowed = " ".join([r[1] for r in res_allow]).strip() if res_allow else ""
        
    return text_raw, text_allowed

files_to_test = [
    ("debug_row_4_AD.png", "abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ- "),
    ("debug_row_4_SOYAD.png", "abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ- "),
    ("debug_row_4_MASA_NO.png", "0123456789"),
    ("debug_row_6_AD.png", "abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ- "),
    ("debug_row_6_SOYAD.png", "abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ- "),
    ("debug_row_6_MASA_NO.png", "0123456789")
]

print("--- OCR CELL TEST ---")
for path, allow in files_to_test:
    raw, allowed = test_cell(path, allow)
    print(f"File: {path}")
    print(f"  Raw: '{raw}'")
    if allow:
        print(f"  With Allowlist: '{allowed}'")
