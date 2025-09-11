# 共享变量区

temp_rects_storage = {}

connect_normal_ocr_result = {}        # 只走普通 OCR 识别的
connect_vague_high_result = {}         # vague 里高置信度当作普通字符的
connect_vague_low_result = {}          # degraded（低置信度）要补全的

# 用户反馈修改存储
user_feedback_modifications = {}

# 存储矩形框ID与extra_num_ocr_prob_dict中key的映射关系
rect_id_to_extra_key_mapping = {}

# 存储当前的extra_num_ocr_prob_dict（用于在各个阶段间传递）
current_extra_num_ocr_prob_dict = {}

# 调试信息存储
debug_info = {}
