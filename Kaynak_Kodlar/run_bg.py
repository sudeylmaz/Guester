# -*- coding: utf-8 -*-
#
# Adı Soyadı: Ceydanur Arslan
# Öğrenci Numarası: 262484066
#
# Adı Soyadı: Sude Yılmaz
# Öğrenci Numarası: 262484068
#
import sys
import os
import traceback

sys.path.insert(0, "C:\\Users\\cydnr\\Desktop\\Hosteasy")

try:
    import app
except Exception as e:
    with open("C:\\Users\\cydnr\\Desktop\\Hosteasy\\bg_error.log", "w") as f:
        f.write(traceback.format_exc())
