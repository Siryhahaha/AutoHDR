from flask import Flask, render_template, request, url_for
import os
import json  # 添加json import
from demo_flask_utils.lib.rect_interface import RectInterface
from demo_flask_utils.connect.main_connect import get_ocr_rects  # 修改导入路径

######################################################
from demo_flask_utils.lib.rect_interface import RectInterface
from infer_pipeline import main
from infer_pipeline_api import *
from demo_flask_utils.connect.shared_vars import *

from PIL import Image
# import infer_pipeline_api as pipline_qwen_multisptk_api
import infer_pipeline as pipline_qwen_multisptk_api
import argparse
from transformers import set_seed
import os
import shutil
import torch  # 确保导入torch包
import json
######################################################


app = Flask(__name__, 
           template_folder='demo_flask_utils/templates',
           static_folder='demo_flask_utils/static')

# 简化配置
STATIC_SUBFOLDERS = ['uploads', 'outputs']
for folder in STATIC_SUBFOLDERS:
    os.makedirs(os.path.join(app.static_folder, folder), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    images_dir = os.path.join(app.static_folder, 'images')
    example_images = []
    if os.path.exists(images_dir):
        example_images = [(f, i) for i, f in enumerate(sorted(os.listdir(images_dir))) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    return render_template('upload.html', example_images=example_images)

def init_model_config(filepath):
    config_file = './ckpt/damage_detect.py'  # 网络模型py文件
    damage_detect_checkpoint_file = './ckpt/damage_detect.pth'  # 训练好的模型参数
    model_name_or_path = './ckpt/AutoHDR-Qwen2-1.5B'
    ocr_det_weights = './ckpt/best.pt'

    parser = argparse.ArgumentParser(prog='test.py')
    parser.add_argument('--ocr_det_weights', nargs='+', type=str, default=ocr_det_weights, help='model.pt path(s)')
    parser.add_argument('--vague_det_weights', nargs='+', type=str, default=damage_detect_checkpoint_file, help='model.pth path(s)')
    parser.add_argument('--vague_det_config', nargs='+', type=str, default=config_file, help='mmdetection config.py path(s)')
    parser.add_argument('--model_name_or_path', nargs='+', type=str, default=model_name_or_path, help='llm weight path(s)')
    
    # 添加所有其他参数
    parser.add_argument('--det-batch-size', type=int, default=1, help='size of each image batch')
    parser.add_argument('--reg-batch-size', type=int, default=36, help='size of each image batch')
    parser.add_argument('--img-size', type=int, default=2048, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.45, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.2, help='IOU threshold for NMS')
    parser.add_argument('--device', default='0', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--image_channel", type=int, default=3)
    parser.add_argument("--pipeline", type=str, default="DPM-Solver++",
                        choices=['DDPM', 'DPM-Solver', 'DPM-Solver++'])
    parser.add_argument("--classifier_free", action="store_false")
    parser.add_argument("--content_mask_guidance_scale", type=float, default=1.5)
    parser.add_argument("--degraded_guidance_scale", type=float, default=1.2)
    parser.add_argument("--solver_order", type=int, default=2)
    parser.add_argument("--num_inference_steps", type=int, default=20)
    parser.add_argument("--ddpm_num_steps", type=int, default=1000)
    parser.add_argument("--ddpm_beta_schedule", type=str, default="linear")
    parser.add_argument("--prediction_type", type=str, default="sample")
    parser.add_argument("--batch_infer", action="store_true")
    parser.add_argument("--gt_image_path", type=str, default=None)
    parser.add_argument("--data_dir", type=str, default=None)
    parser.add_argument("--degrade_modes", nargs='+', default=['removal', 'hole', 'ink'])
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--num_workers", type=int, default=8)

    opt = parser.parse_args()
    if opt.seed is not None:
        set_seed(opt.seed)

    save_path = './results'
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    img_dir = os.path.join(save_path, 'img')
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    combined_dir = os.path.join(save_path, 'combined')
    if not os.path.exists(combined_dir):
        os.makedirs(combined_dir)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    opt.data = filepath

    img = Image.open(filepath).convert('RGB')
    img_invert = invert_image(img)
    os.makedirs('tmp_img', exist_ok=True)
    img_invert_path = 'tmp_img/api_tmp.jpg'
    img_invert.save(img_invert_path)

    return device, opt, img_invert_path

def process_rect_results(all_rect_results):
    """
    处理OCR结果，生成矩形框数据
    :param all_rect_results: 包含normal_ocr、vague_high、vague_low结果的字典
    :return: 处理后的矩形框列表
    """
    rects = []
    id_counter = 1
    
    for result_type, ocr_result_dict in all_rect_results.items():
        if not ocr_result_dict:  # 检查结果集是否为空
            continue
        for bbox_str, (labels, confs) in ocr_result_dict.items():
            try:
                # 解析边界框字符串
                bbox = eval(bbox_str)
                x1, y1, x2, y2 = bbox
                # 计算宽度和高度
                width = x2 - x1
                height = y2 - y1
                # 提取第一个字符作为标签
                first_char = labels[0] if labels else ""
                # 根据类型确定颜色
                color_map = {
                    'normal_ocr': "#7fffd4",  # 绿色
                    'vague_high': "#060ac9",  # 蓝色
                    'vague_low': "#ff0000"    # 红色
                }
                color = color_map.get(result_type, "#ff0000")
                
                # 准备备选项：取前5个OCR候选结果
                alternatives = labels[:5] if len(labels) >= 5 else labels
                # 确保有5个选项
                while len(alternatives) < 5:
                    alternatives.append(f"选项{len(alternatives)+1}")
                
                # 使用RectInterface创建标准格式的矩形对象
                rect = RectInterface.create_rect_data(
                    x=int(x1),
                    y=int(y1), 
                    width=int(width),
                    height=int(height),
                    color=color,
                    label=first_char,
                    alternatives=alternatives
                )
                rect["id"] = id_counter
                rects.append(rect)
                id_counter += 1
            except Exception as e:
                print(f"处理框数据时出错: {e}, bbox_str: {bbox_str}")
                continue

    if not rects:
        rects = [
            RectInterface.create_rect_data(150, 300, 80, 40, "#ff0000", "没看到字", 
                                         ["没看到字", "备选1", "备选2", "备选3", "备选4"])
        ]
        rects[0]["id"] = 1

    return rects

@app.route('/upload', methods=['POST'])
def upload_file():
    logs = []
    original = None
    try:
        is_example = request.form.get('is_example', '0') == '1'
        
        if is_example:
            filename = request.form.get('example_filename')
            if not filename:
                return render_template('localize_results.html', logs=["错误：未指定例子图片文件名"])
            filepath = os.path.join(app.static_folder, 'images', filename)
            if not os.path.exists(filepath):
                return render_template('localize_results.html', logs=["错误：例子图片不存在"])
            logs.append(f"[选择例子图片] {filename}")
            
        else:
            file = request.files.get('file')
            if not file or file.filename == '' or not allowed_file(file.filename):
                return render_template('localize_results.html', logs=["错误：无效的文件"])
            filename = file.filename
            filepath = os.path.join(app.static_folder, 'uploads', filename)
            file.save(filepath)
            logs.append(f"[上传成功] {filename}")
        
        print(f"Processing file: {filepath}")
        logs.append(f"[开始处理] {filename}")
        
        # 使用新函数替换原有的配置代码
        device, opt, img_invert_path = init_model_config(filepath)
        logs.append("[模型初始化完成]")
        
        char_str, extra_num_ocr_prob_dict = localize(device, opt, img_invert_path)
        logs.append(f"[OCR识别完成] 识别到 {len(extra_num_ocr_prob_dict)} 个区域")

        normal_ocr_result = connect_normal_ocr_result.get('result', {})
        vague_high_result = connect_vague_high_result.get('result', {})
        vague_low_result = connect_vague_low_result.get('result', {})
        
        all_ocr_results = {
            'normal_ocr': normal_ocr_result,
            'vague_high': vague_high_result,
            'vague_low': vague_low_result
        }

        # 使用新函数处理OCR结果
        ocr_rects = process_rect_results(all_ocr_results)
        logs.append(f"[生成框数据] 共 {len(ocr_rects)} 个框")
        
        print(f"Sample rect data: {ocr_rects[0] if ocr_rects else 'No rects'}")
        
        # 传入OCR识别框数据
        output_path, rects_json = RectInterface.process_with_rects(
            filepath, 
            os.path.join(app.static_folder, 'outputs'), 
            filename,
            ocr_rects
        )
        
        # 确保图片路径正确
        image_url = url_for('static', filename=os.path.relpath(output_path, app.static_folder))
        logs.append(f"[处理完成] 输出路径: {output_path}")
        logs.append(f"[图片URL] {image_url}")
        
        # 检查输出文件是否真实存在
        if not os.path.exists(output_path):
            logs.append(f"[警告] 输出文件不存在: {output_path}")
        
        return render_template('localize_results.html',
                             original=filename,
                             processed=os.path.basename(output_path),
                             logs=logs,
                             image_url=image_url,
                             initial_rects=rects_json)
                             
    except Exception as e:
        import traceback
        error_msg = f"异常：{str(e)}"
        logs.append(error_msg)
        logs.append(f"详细错误：{traceback.format_exc()}")
        print(f"Error in upload_file: {traceback.format_exc()}")
        
        return render_template('localize_results.html', 
                             original=original or "未知文件", 
                             logs=logs,
                             image_url=None,
                             initial_rects="[]")

@app.route('/update_rects', methods=['POST'])
def update_rects():
    """处理用户对矩形框的修改反馈"""
    try:
        data = request.get_json()
        rects_data = data.get('rects', [])
        
        # 清空之前的反馈
        user_feedback_modifications.clear()
        
        # 处理每个矩形框的修改
        for rect in rects_data:
            rect_id = rect.get('id')
            selected_index = rect.get('selectedIndex', 0)
            alternatives = rect.get('alternatives', [])
            
            if rect_id and alternatives and selected_index < len(alternatives):
                selected_text = alternatives[selected_index]
                user_feedback_modifications[f'rect_{rect_id}'] = {
                    'selected_text': selected_text,
                    'selected_index': selected_index,
                    'bbox': (rect.get('x', 0), rect.get('y', 0), rect.get('width', 0), rect.get('height', 0))
                }
        
        return {'status': 'success', 'message': f'已更新 {len(user_feedback_modifications)} 个框的反馈'}
    except Exception as e:
        return {'status': 'error', 'message': f'更新失败: {str(e)}'}

@app.route('/predict', methods=['POST'])
def predict_page():
    logs = []
    try:
        original_filename = request.form.get('original_filename')
        rects_data = request.form.get('rects_data')
        
        if not original_filename:
            return render_template('localize_results.html', logs=["错误：缺少原始文件名"])
        
        logs.append(f"[进入预测阶段] {original_filename}")
        
        # 重新构建文件路径
        filepath = None
        uploads_path = os.path.join(app.static_folder, 'uploads', original_filename)
        if os.path.exists(uploads_path):
            filepath = uploads_path
        else:
            examples_path = os.path.join(app.static_folder, 'images', original_filename)
            if os.path.exists(examples_path):
                filepath = examples_path
        
        if not filepath:
            return render_template('localize_results.html', logs=["错误：找不到原始文件"])
        
        # 初始化模型配置
        device, opt, img_invert_path = init_model_config(filepath)
        
        # 先执行localize获取char_str和extra_num_ocr_prob_dict
        char_str, extra_num_ocr_prob_dict = localize(device, opt, img_invert_path)
        
        # 处理用户的矩形框修改反馈 - 在predict之前修改extra_num_ocr_prob_dict
        if rects_data:
            try:
                rects_list = json.loads(rects_data)
                modification_count = 0
                
                # 首先建立坐标到extra_key的映射
                coord_to_extra_key = {}
                for extra_key, bbox_info in extra_num_ocr_prob_dict.items():
                    if 'bbox' in bbox_info:
                        bbox = bbox_info['bbox']
                        coord_key = f"{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}"
                        coord_to_extra_key[coord_key] = extra_key
                
                for rect in rects_list:
                    rect_id = rect.get('id')
                    selected_index = rect.get('selectedIndex', 0)
                    alternatives = rect.get('alternatives', [])
                    
                    if rect_id and alternatives and selected_index < len(alternatives):
                        selected_text = alternatives[selected_index]
                        rect_x = rect.get('x', 0)
                        rect_y = rect.get('y', 0)
                        rect_w = rect.get('width', 0)
                        rect_h = rect.get('height', 0)
                        
                        # 寻找匹配的extra_key
                        found_match = False
                        for extra_key, bbox_info in extra_num_ocr_prob_dict.items():
                            if 'bbox' in bbox_info:
                                bbox = bbox_info['bbox']
                                bbox_x, bbox_y, bbox_w, bbox_h = bbox
                                
                                # 坐标匹配 (考虑一些容差)
                                if (abs(bbox_x - rect_x) <= 5 and 
                                    abs(bbox_y - rect_y) <= 5 and
                                    abs(bbox_w - rect_w) <= 5 and
                                    abs(bbox_h - rect_h) <= 5):
                                    
                                    # 直接修改extra_num_ocr_prob_dict
                                    extra_num_ocr_prob_dict[extra_key]['txt'] = selected_text
                                    
                                    # 更新alternatives，将选中的文字移到第一位
                                    if 'alternatives' in extra_num_ocr_prob_dict[extra_key]:
                                        old_alternatives = extra_num_ocr_prob_dict[extra_key]['alternatives'].copy()
                                        if selected_text in old_alternatives:
                                            old_alternatives.remove(selected_text)
                                        extra_num_ocr_prob_dict[extra_key]['alternatives'] = [selected_text] + old_alternatives
                                    
                                    # 标记为用户修改
                                    extra_num_ocr_prob_dict[extra_key]['user_modified'] = True
                                    modification_count += 1
                                    found_match = True
                                    
                                    logs.append(f"[用户修改] 框{rect_id}({extra_key}) 坐标({bbox_x},{bbox_y},{bbox_w},{bbox_h}) -> {selected_text}")
                                    break
                        
                        if not found_match:
                            logs.append(f"[警告] 未找到匹配的框: 坐标({rect_x},{rect_y},{rect_w},{rect_h})")
                
                logs.append(f"[用户反馈] 已处理 {modification_count} 个框的修改")
            except Exception as e:
                logs.append(f"[警告] 解析用户反馈数据失败: {str(e)}")
                import traceback
                logs.append(f"详细错误: {traceback.format_exc()}")
        
        # 执行predict - 现在extra_num_ocr_prob_dict已经包含了用户的修改
        updated_extra_num_ocr_prob_dict = predict(device, opt, char_str, extra_num_ocr_prob_dict)
        
        # 处理predict结果，生成新的矩形框数据
        predict_rects = process_predict_results(updated_extra_num_ocr_prob_dict)
        
        # 处理图片并生成输出
        output_path, rects_json = RectInterface.process_with_rects(
            filepath, 
            os.path.join(app.static_folder, 'outputs'), 
            f"predict_{original_filename}",
            predict_rects
        )
        image_url = url_for('static', filename=os.path.relpath(output_path, app.static_folder))
        
        return render_template('predict_results.html',
                             original=original_filename,
                             logs=logs,
                             image_url=image_url,
                             initial_rects=rects_json,
                             extra_dict_json=json.dumps(updated_extra_num_ocr_prob_dict))
                             
    except Exception as e:
        import traceback
        return render_template('localize_results.html', 
                             logs=[f"预测阶段异常：{str(e)}", f"详细错误：{traceback.format_exc()}"])

def process_predict_results(extra_num_ocr_prob_dict):
    """
    处理predict结果，生成矩形框数据
    """
    rects = []
    id_counter = 1
    
    # 清空之前的映射关系
    rect_id_to_extra_key_mapping.clear()
    
    for key, bbox_info in extra_num_ocr_prob_dict.items():
        if 'extra_' in key:  # 只处理需要预测的框
            bbox = bbox_info['bbox']
            x, y, w, h = bbox
            
            # 获取预测的文字
            predicted_text = bbox_info.get('txt', '')
            
            # 获取备选项（LLM + OCR 融合后的top5）
            alternatives = []
            if 'ocr_llm_topk' in bbox_info:
                alternatives = bbox_info['ocr_llm_topk'][:5]
            elif 'alternatives' in bbox_info:
                alternatives = bbox_info['alternatives'][:5]
            else:
                alternatives = [predicted_text]
            
            # 确保有5个选项
            while len(alternatives) < 5:
                alternatives.append(f"选项{len(alternatives)+1}")
            
            # 根据预测质量设置颜色
            color = "#ff6b35"  # 橙色表示预测结果
            if 'llm_prob' in bbox_info and bbox_info['llm_prob']:
                # 如果有LLM概率且较高，使用蓝色
                if bbox_info['llm_prob'][0][1] > 0.8:
                    color = "#2196f3"  # 蓝色表示高置信度预测
            
            rect = {
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "color": color,
                "label": predicted_text,
                "id": id_counter,
                "alternatives": alternatives,
                "selectedIndex": 0
            }
            rects.append(rect)
            
            # 建立ID映射关系
            rect_id_to_extra_key_mapping[id_counter] = key
            id_counter += 1
    
    if not rects:
        rects = [
            RectInterface.create_rect_data(150, 300, 80, 40, "#ff6b35", "预测结果为空", 
                                         ["预测结果为空", "选项1", "选项2", "选项3", "选项4"])
        ]
    
    return rects

@app.route('/restore', methods=['POST'])
def restore_page():
    logs = []
    try:
        original_filename = request.form.get('original_filename')
        rects_data = request.form.get('rects_data')
        extra_dict_data = request.form.get('extra_dict_data')
        
        if not original_filename:
            return render_template('predict_results.html', logs=["错误：缺少原始文件名"])
        
        logs.append(f"[进入修复阶段] {original_filename}")
        
        # 重新构建文件路径
        filepath = None
        uploads_path = os.path.join(app.static_folder, 'uploads', original_filename)
        if os.path.exists(uploads_path):
            filepath = uploads_path
        else:
            examples_path = os.path.join(app.static_folder, 'images', original_filename)
            if os.path.exists(examples_path):
                filepath = examples_path
        
        if not filepath:
            return render_template('predict_results.html', logs=["错误：找不到原始文件"])
        
        # 解析extra_dict_data
        extra_num_ocr_prob_dict = {}
        if extra_dict_data:
            try:
                extra_num_ocr_prob_dict = json.loads(extra_dict_data)
                logs.append(f"[数据解析] 成功解析包含 {len(extra_num_ocr_prob_dict)} 个框的数据")
            except Exception as e:
                logs.append(f"警告：无法解析额外字典数据: {str(e)}")
                return render_template('predict_results.html', logs=logs)
        
        # 处理用户在predict页面的最新修改反馈
        if rects_data:
            try:
                rects_list = json.loads(rects_data)
                modification_count = 0
                
                for rect in rects_list:
                    rect_id = rect.get('id')
                    selected_index = rect.get('selectedIndex', 0)
                    alternatives = rect.get('alternatives', [])
                    
                    if rect_id and alternatives and selected_index < len(alternatives):
                        selected_text = alternatives[selected_index]
                        rect_x = rect.get('x', 0)
                        rect_y = rect.get('y', 0)
                        rect_w = rect.get('width', 0)
                        rect_h = rect.get('height', 0)
                        
                        # 在extra_num_ocr_prob_dict中寻找匹配的框
                        for extra_key, bbox_info in extra_num_ocr_prob_dict.items():
                            if 'bbox' in bbox_info:
                                bbox = bbox_info['bbox']
                                bbox_x, bbox_y, bbox_w, bbox_h = bbox
                                
                                # 坐标匹配
                                if (abs(bbox_x - rect_x) <= 5 and 
                                    abs(bbox_y - rect_y) <= 5 and
                                    abs(bbox_w - rect_w) <= 5 and
                                    abs(bbox_h - rect_h) <= 5):
                                    
                                    # 直接修改extra_num_ocr_prob_dict
                                    extra_num_ocr_prob_dict[extra_key]['txt'] = selected_text
                                    
                                    # 更新alternatives
                                    if 'alternatives' in extra_num_ocr_prob_dict[extra_key]:
                                        old_alternatives = extra_num_ocr_prob_dict[extra_key]['alternatives'].copy()
                                        if selected_text in old_alternatives:
                                            old_alternatives.remove(selected_text)
                                        extra_num_ocr_prob_dict[extra_key]['alternatives'] = [selected_text] + old_alternatives
                                    
                                    # 更新ocr_llm_topk
                                    if 'ocr_llm_topk' in extra_num_ocr_prob_dict[extra_key]:
                                        old_topk = extra_num_ocr_prob_dict[extra_key]['ocr_llm_topk'].copy()
                                        if selected_text in old_topk:
                                            old_topk.remove(selected_text)
                                        extra_num_ocr_prob_dict[extra_key]['ocr_llm_topk'] = [selected_text] + old_topk
                                    
                                    # 标记为用户修改
                                    extra_num_ocr_prob_dict[extra_key]['user_modified'] = True
                                    modification_count += 1
                                    
                                    logs.append(f"[用户修改] 框{rect_id}({extra_key}) -> {selected_text}")
                                    break
                
                logs.append(f"[用户反馈] 已处理 {modification_count} 个框的修改")
            except Exception as e:
                logs.append(f"[警告] 解析用户反馈数据失败: {str(e)}")
        
        # 初始化模型配置并执行restore
        device, opt, img_invert_path = init_model_config(filepath)
        
        # 执行restore阶段 - 传入修改后的extra_num_ocr_prob_dict
        restored_image = restore(device, opt, img_invert_path, extra_num_ocr_prob_dict)
        
        # 保存修复后的图像
        restore_filename = f"restored_{original_filename}"
        restore_path = os.path.join(app.static_folder, 'outputs', restore_filename)
        restored_image.save(restore_path)
        
        # 生成图像URL
        restore_url = url_for('static', filename=os.path.relpath(restore_path, app.static_folder))
        original_url = url_for('static', filename=os.path.relpath(filepath, app.static_folder))
        
        return render_template('restore_results.html',
                             original=original_filename,
                             logs=logs,
                             restore_url=restore_url,
                             original_url=original_url,
                             restore_filename=restore_filename)
                             
    except Exception as e:
        import traceback
        return render_template('predict_results.html', 
                             logs=[f"修复阶段异常：{str(e)}", f"详细错误：{traceback.format_exc()}"])

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001,  debug=True)