# 共享变量区

temp_rects_storage = {}

connect_normal_ocr_result = {}        # 只走普通 OCR 识别的
connect_vague_high_result = {}         # vague 里高置信度当作普通字符的
connect_vague_low_result = {}          # degraded（低置信度）要补全的
