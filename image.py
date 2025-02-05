import cv2
import os
import numpy as np
from config import *

def extract_key_frames(video_path, max_images=15):
    """从视频中提取关键帧"""
    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / frame_rate
    
    frames = []
    positions = []  # 存储每个关键帧的时间位置
    
    try:
        # 计算关键帧的间隔
        if max_images > 1:
            interval = duration / (max_images - 1)
        else:
            interval = duration
        
        for i in range(max_images):
            # 计算目标时间点
            target_time = i * interval
            target_frame = int(target_time * frame_rate)
            
            # 设置帧位置
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            
            if ret:
                frames.append(frame)
                # 记录实际的时间位置（秒）
                actual_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                positions.append(actual_time)
            else:
                print(f"警告：无法读取第 {i+1} 个关键帧")
    
    except Exception as e:
        print(f"提取关键帧时发生错误: {str(e)}")
        raise
    
    finally:
        cap.release()
    
    if not frames:
        raise Exception("未能提取到任何关键帧")
    
    return frames, positions

def save_images(frames, output_dir):
    """保存图片到指定目录"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    image_paths = []
    for i, frame in enumerate(frames, 1):
        try:
            img_path = os.path.join(output_dir, f"{i}.jpg")
            cv2.imwrite(img_path, frame)
            image_paths.append(img_path)
        except Exception as e:
            print(f"保存图片 {i} 时发生错误: {str(e)}")
            continue
    
    if not image_paths:
        raise Exception("未能保存任何图片")
    
    return image_paths

def format_timestamp(seconds):
    """将秒数格式化为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
