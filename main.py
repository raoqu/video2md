import cv2
import ffmpeg
import hashlib
import os
import numpy as np
import requests
import argparse
from datetime import datetime
from config import *
from download import is_url, download_video


def get_video_md5(video_path):
    """计算视频文件的 MD5 值"""
    hash_md5 = hashlib.md5()
    with open(video_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_audio_from_video(video_path, audio_path):
    """从视频中提取音频并转换为 16kHz 的 WAV 格式"""
    stream = ffmpeg.input(video_path)
    stream = ffmpeg.output(stream, audio_path, ar=AUDIO_SAMPLE_RATE, acodec=AUDIO_CODEC)
    ffmpeg.run(stream, overwrite_output=True)

def transcribe_audio_with_whisper_server(audio_path):
    """使用 whisper-server 转录音频"""
    with open(audio_path, 'rb') as audio_file:
        files = {
            'file': ('audio.wav', audio_file, 'audio/wav')
        }
        data = {
            'temperature': '0.0',
            'temperature_inc': '0.2',
            'response_format': 'json'
        }
        response = requests.post(WHISPER_SERVER_URL, files=files, data=data)
        if response.status_code != 200:
            raise Exception(f"Whisper-server 错误: {response.text}")
        result = response.json()
        print(result)
        return result['text']

def extract_key_frames(video_path, max_images=5):
    """从视频中提取关键帧"""
    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / frame_rate
    
    frames = []
    positions = []  # 存储每个关键帧的时间位置
    
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
    
    cap.release()
    return frames, positions

def save_images(frames, output_dir):
    """保存图片到指定目录"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    image_paths = []
    for i, frame in enumerate(frames, 1):
        img_path = os.path.join(output_dir, f"{i}.jpg")
        cv2.imwrite(img_path, frame)
        image_paths.append(img_path)
    return image_paths

def format_timestamp(seconds):
    """将秒数格式化为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def process_with_local_llm(text):
    """使用本地LLM处理文本"""
    headers = {'Content-Type': 'application/json'}
    
    # 构造请求数据
    data = {
        'messages': [
            {
                'role': 'system',
                'content': ROLE_PROMPT
            },
            {
                'role': 'user',
                'content': PROMPT_TEMPLATE.format(text=text)
            }
        ],
        'temperature': LLM_TEMPERATURE,
        'max_tokens': LLM_MAX_TOKENS
    }
    
    try:
        response = requests.post(LLM_SERVER_URL, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"LLM处理失败: {response.text}")
            return text  # 如果处理失败，返回原文
    except Exception as e:
        print(f"LLM请求异常: {str(e)}")
        return text  # 发生异常时返回原文

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
        f.write("# 视频转录与关键帧\n\n")
        f.write("## 转录文本\n\n")
        f.write(processed_text + "\n\n")
        f.write("## 关键帧图片\n\n")
        for img_path, pos in zip(relative_image_paths, positions):
            timestamp = format_timestamp(pos)
            f.write(f"![关键帧 {timestamp}]({img_path})\n\n")

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
        
        # 获取当前日期
        current_date = datetime.now().strftime('%Y%m%d')
        # 获取视频文件的 MD5 值
        video_md5 = get_video_md5(video_path)
        
        # 确保目录存在
        os.makedirs(AUDIO_DIR, exist_ok=True)
        os.makedirs(MD_DIR, exist_ok=True)
        
        audio_path = os.path.join(AUDIO_DIR, f"{current_date}-{video_md5}.wav")
        md_path = os.path.join(MD_DIR, f"{current_date}-{video_md5}.md")
        # 提取音频并转换为 16kHz 的 WAV 格式
        extract_audio_from_video(video_path, audio_path)
        # 使用 whisper-server 转录音频
        text = transcribe_audio_with_whisper_server(audio_path)
        # 提取关键帧
        frames, positions = extract_key_frames(video_path)
        # 保存关键帧图片
        image_dir = os.path.join(MD_DIR, video_md5)
        os.makedirs(image_dir, exist_ok=True)
        image_paths = save_images(frames, image_dir)
        # 生成 Markdown 文件
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
