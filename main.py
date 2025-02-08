import cv2
import hashlib
import os
import numpy as np
import argparse
from datetime import datetime
from config import *
from download import is_url, download_video
from image import extract_key_frames, save_images, format_timestamp
from audio import extract_audio_from_video, transcribe_audio_with_whisper_server, process_with_local_llm


def get_video_md5(video_path):
    """计算视频文件的 MD5 值"""
    hash_md5 = hashlib.md5()
    with open(video_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def generate_markdown(text, image_paths, positions, output_md):
    """生成 Markdown 文件"""
    # 使用LLM处理文本
    if LLM_PROCESS:
        processed_text = process_with_local_llm(text)
    else:
        processed_text = text
    
    # 将图片路径转换为相对于markdown文件的路径
    relative_image_paths = [os.path.relpath(path, os.path.dirname(output_md)) for path in image_paths]
    
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(processed_text + "\n\n")
        f.write("# 关键帧图片\n\n")
        for img_path, pos in zip(relative_image_paths, positions):
            timestamp = format_timestamp(pos)
            f.write(f"![关键帧 {timestamp}]({img_path})\n\n")

def save_text(text, txt_path):
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        
        # 保存文本文件
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
    except Exception as e:
        raise Exception(f"保存文本文件失败: {str(e)}")

def main(input_path):
    """主函数"""
    try:
        # 如果输入是URL，先下载视频
        if is_url(input_path):
            print(f"正在从 {input_path} 下载视频...")
            video_path = download_video(input_path)
            print(f"视频已下载到: {video_path}")
        else:
            video_path = input_path
            
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 获取当前日期和视频MD5
        current_date = datetime.now().strftime('%Y%m%d')
        video_md5 = get_video_md5(video_path)
        
        # 准备输出路径
        audio_path = os.path.join(AUDIO_DIR, f"{current_date}-{video_md5}.wav")
        md_path = os.path.join(MD_DIR, f"{current_date}-{video_md5}.md")
        txt_path = os.path.join(MD_DIR, f"{current_date}-{video_md5}.txt")
        image_dir = os.path.join(MD_DIR, video_md5)
        
        # 确保必要的目录存在
        os.makedirs(AUDIO_DIR, exist_ok=True)
        os.makedirs(MD_DIR, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)
        
        print("开始处理视频...")
        
        # 1. 提取并转录音频
        print("正在提取音频...")
        extract_audio_from_video(video_path, audio_path)
        
        print("正在转录音频...")
        text = transcribe_audio_with_whisper_server(audio_path)
        save_text(text, txt_path)
        
        # 2. 提取并保存关键帧
        print("正在提取关键帧...")
        frames, positions = extract_key_frames(video_path)
        
        print("正在保存关键帧图片...")
        image_paths = save_images(frames, image_dir)
        
        # 3. 生成markdown文件
        print("正在生成Markdown文件...")
        generate_markdown(text, image_paths, positions, md_path)
        
        print(f"处理完成！Markdown文件已生成: {md_path}")
        
    except Exception as e:
        print(f"处理失败: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将视频文件或在线视频转换为包含音频转录文本和关键帧图片的 Markdown 文件")
    parser.add_argument('input_path', type=str, help="输入的视频文件路径或视频URL")
    args = parser.parse_args()
    main(args.input_path)
