# LLM 配置
LLM_PROCESS = True
LLM_SERVER_URL = 'http://127.0.0.1:1234/v1/chat/completions'
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2000

# 提示词配置
ROLE_PROMPT = "你是一个专业的文本处理助手"
PROMPT_TEMPLATE = """
```
{text}
```
 
请对以上文本处理成markdown格式，要求：

1. 如果内容不是简体中文，将内容首先忠实地翻译成简体中文
2. 保持原文的主要内容，尽可能多的保持原文细节
3. 除了新增章节标题外，不要新增任何其他内容
4. 修正可能的语法错误
"""

# Whisper Server 配置
WHISPER_SERVER_URL = 'http://127.0.0.1:8080/inference'

# 文件目录配置
AUDIO_DIR = 'audio'
MD_DIR = 'md'

# 视频下载配置
VIDEO_DIR = 'videos'
SUPPORTED_VIDEO_DOMAINS = {
    'youtube.com': 'youtube',
    'youtu.be': 'youtube',
    'bilibili.com': 'bilibili'
}

# 下载器配置
YOUTUBE_DOWNLOAD_QUALITY = 'best'

BILIBILI_FORMAT = '30033'  # 可以是具体的format ID，如'80'表示1080P，或'best'表示最佳质量
# --------------------------------------------------------------------------------
# 格式ID       扩展名      分辨率          文件大小       说明                  
# --------------------------------------------------------------------------------
# 30216      m4a      audio only   N/A                            
# 30232      m4a      audio only   N/A                            
# 30280      m4a      audio only   N/A                            
# 100046     mp4      640x360      N/A                            
# 30011      mp4      640x360      N/A                            
# 100022     mp4      640x360      N/A                            
# 100047     mp4      852x480      N/A                            
# 30033      mp4      852x480      N/A                            
# 100023     mp4      852x480      N/A                            
# 100048     mp4      1280x720     N/A                            
# 30066      mp4      1280x720     N/A                            
# 100024     mp4      1280x720     N/A                            
# 100050     mp4      1920x1080    N/A                            
# 30077      mp4      1920x1080    N/A                            
# 100026     mp4      1920x1080    N/A                            
# --------------------------------------------------------------------------------

# 音频配置
AUDIO_SAMPLE_RATE = '16000'
AUDIO_CODEC = 'pcm_s16le'
