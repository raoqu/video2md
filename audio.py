import ffmpeg
import requests
import os
from config import *

def extract_audio_from_video(video_path, audio_path):
    """从视频中提取音频并转换为指定采样率的 WAV 格式
    
    Args:
        video_path (str): 输入视频文件路径
        audio_path (str): 输出音频文件路径
        
    Raises:
        Exception: 音频提取失败时抛出异常
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        # 配置ffmpeg流
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(stream, 
                             audio_path, 
                             ar=AUDIO_SAMPLE_RATE,  # 设置采样率
                             acodec=AUDIO_CODEC)    # 设置音频编码
        
        # 执行转换
        ffmpeg.run(stream, overwrite_output=True)
        
        if not os.path.exists(audio_path):
            raise Exception("音频文件未生成")
            
    except Exception as e:
        raise Exception(f"音频提取失败: {str(e)}")

def transcribe_audio_with_whisper_server(audio_path):
    """使用 whisper-server 转录音频
    
    Args:
        audio_path (str): 音频文件路径
        
    Returns:
        str: 转录的文本
        
    Raises:
        Exception: 转录失败时抛出异常
    """
    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
        with open(audio_path, 'rb') as audio_file:
            files = {
                'file': ('audio.wav', audio_file, 'audio/wav')
            }
            data = {
                'temperature': '0.0',
                'temperature_inc': '0.2',
                'response_format': 'json'
            }
            
            # 发送请求到Whisper服务器
            response = requests.post(WHISPER_SERVER_URL, 
                                  files=files, 
                                  data=data)
            
            if response.status_code != 200:
                raise Exception(f"Whisper服务器错误: {response.text}")
                
            result = response.json()
            if 'text' not in result:
                raise Exception("Whisper服务器返回的数据格式不正确")
                
            print("音频转录完成")
            return result['text']
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Whisper服务器连接失败: {str(e)}")
    except Exception as e:
        raise Exception(f"音频转录失败: {str(e)}")
