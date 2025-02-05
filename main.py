import cv2
import ffmpeg
import hashlib
import os
import numpy as np
import requests
import argparse
from datetime import datetime

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
    stream = ffmpeg.output(stream, audio_path, ar='16000', acodec='pcm_s16le')
    ffmpeg.run(stream, overwrite_output=True)

def transcribe_audio_with_whisper_server(audio_path):
    """使用 whisper-server 转录音频"""
    url = 'http://127.0.0.1:8080/inference'
    with open(audio_path, 'rb') as audio_file:
        files = {
            'file': ('audio.wav', audio_file, 'audio/wav')
        }
        data = {
            'temperature': '0.0',
            'temperature_inc': '0.2',
            'response_format': 'json'
        }
        response = requests.post(url, files=files, data=data)
        if response.status_code != 200:
            raise Exception(f"Whisper-server 错误: {response.text}")
        result = response.json()
        print(result)
        return result['text']

def extract_key_frames(video_path, max_images=5):
    """从视频中提取关键帧"""
    cap = cv2.VideoCapture(video_path)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    key_frames = []
    prev_frame = None
    for i in range(0, frame_count, int(frame_rate)):
        ret, frame = cap.read()
        if not ret:
            break
        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, frame)
            non_zero_count = np.count_nonzero(diff)
            if non_zero_count > 10000:  # 阈值，可根据需要调整
                key_frames.append(frame)
        prev_frame = frame
        if len(key_frames) >= max_images:
            break
    cap.release()
    return key_frames

def save_images(images, output_dir):
    """保存图片到指定目录"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    image_paths = []
    for idx, img in enumerate(images):
        img_path = os.path.join(output_dir, f"{idx + 1}.jpg")
        cv2.imwrite(img_path, img)
        image_paths.append(img_path)
    return image_paths

# LLM提示词配置
PROMPT_TEMPLATE = """
请对以下文本进行处理和优化：
```
{text}
```

要求：
1. 如果内容不是中文，将内容首先翻译成中文
2. 保持原文的主要内容
3. 优化文本的组织结构
4. 修正可能的语法错误
"""

def process_with_local_llm(text):
    """使用本地LLM处理文本"""
    url = 'http://127.0.0.1:1234/v1/chat/completions'
    headers = {'Content-Type': 'application/json'}
    
    # 构造请求数据
    data = {
        'messages': [
            {
                'role': 'system',
                'content': '你是一个专业的文本处理助手，擅长优化和改进文本内容。'
            },
            {
                'role': 'user',
                'content': PROMPT_TEMPLATE.format(text=text)
            }
        ],
        'temperature': 0.7,
        'max_tokens': 2000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"LLM处理失败: {response.text}")
            return text  # 如果处理失败，返回原文
    except Exception as e:
        print(f"LLM请求异常: {str(e)}")
        return text  # 发生异常时返回原文

def generate_markdown(text, image_paths, output_md):
    """生成 Markdown 文件"""
    # 使用LLM处理文本
    processed_text = process_with_local_llm(text)
    
    # 将图片路径转换为相对于markdown文件的路径
    relative_image_paths = [os.path.relpath(path, os.path.dirname(output_md)) for path in image_paths]
    
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write("# 视频转录与关键帧\n\n")
        f.write("## 转录文本\n\n")
        f.write(processed_text + "\n\n")
        f.write("## 关键帧图片\n\n")
        for img_path in relative_image_paths:
            f.write(f"![关键帧]({img_path})\n\n")

def main(video_path):
    """主函数"""
    # 获取当前日期
    current_date = datetime.now().strftime('%Y%m%d')
    # 获取视频文件的 MD5 值
    video_md5 = get_video_md5(video_path)
    # 构造音频和 Markdown 文件的路径
    audio_dir = 'audio'
    md_dir = 'md'
    
    # 确保目录存在
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)
    
    audio_path = os.path.join(audio_dir, f"{current_date}-{video_md5}.wav")
    md_path = os.path.join(md_dir, f"{current_date}-{video_md5}.md")
    # 提取音频并转换为 16kHz 的 WAV 格式
    extract_audio_from_video(video_path, audio_path)
    # 使用 whisper-server 转录音频
    text = transcribe_audio_with_whisper_server(audio_path)
    # 提取关键帧
    key_frames = extract_key_frames(video_path)
    # 保存关键帧图片
    image_dir = os.path.join(md_dir, video_md5)
    os.makedirs(image_dir, exist_ok=True)
    image_paths = save_images(key_frames, image_dir)
    # 生成 Markdown 文件
    generate_markdown(text, image_paths, md_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将视频文件转换为包含音频转录文本和关键帧图片的 Markdown 文件")
    parser.add_argument('video_path', type=str, help="输入的视频文件路径")
    args = parser.parse_args()
    main(args.video_path)
