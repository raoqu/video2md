import os
import re
from urllib.parse import urlparse
import yt_dlp
from config import *

def is_url(path):
    """检查路径是否为URL"""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_domain(url):
    """获取URL的主域名"""
    domain = urlparse(url).netloc
    # 移除www.前缀
    domain = re.sub(r'^www\.', '', domain)
    return domain

def get_downloader(url):
    """根据URL获取对应的下载器"""
    domain = get_domain(url)
    
    # 检查是否支持该域名
    for supported_domain, platform in SUPPORTED_VIDEO_DOMAINS.items():
        if supported_domain in domain:
            if platform == 'youtube':
                return YoutubeDownloader()
            elif platform == 'bilibili':
                return BilibiliDownloader()
    
    raise ValueError(f"不支持的视频网站: {domain}")

class VideoDownloader:
    """视频下载器基类"""
    def __init__(self):
        self.default_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': os.path.join(VIDEO_DIR, '%(title)s.%(ext)s')
        }

    def list_formats(self, url):
        """列出视频可用的格式"""
        print("\n可用的视频格式：")
        print("-" * 80)
        print(f"{'格式ID':<10} {'扩展名':<8} {'分辨率':<12} {'文件大小':<10} {'说明':<20}")
        print("-" * 80)
        
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            for f in formats:
                format_id = f.get('format_id', 'N/A')
                ext = f.get('ext', 'N/A')
                resolution = f.get('resolution', 'N/A')
                filesize = f.get('filesize', 0)
                filesize_str = f"{filesize/1024/1024:.1f}MB" if filesize else 'N/A'
                note = f.get('format_note', '')
                
                print(f"{format_id:<10} {ext:<8} {resolution:<12} {filesize_str:<10} {note:<20}")
        print("-" * 80)
        return formats

    def download(self, url):
        raise NotImplementedError

class YoutubeDownloader(VideoDownloader):
    """YouTube视频下载器"""
    def download(self, url):
        # 确保下载目录存在
        os.makedirs(VIDEO_DIR, exist_ok=True)
        
        # 合并配置选项
        ydl_opts = {
            **self.default_opts,
            'format': YOUTUBE_DOWNLOAD_QUALITY
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                if os.path.exists(video_path):
                    return video_path
                raise FileNotFoundError("下载完成但找不到视频文件")
                
        except Exception as e:
            print("\n下载失败！正在获取可用格式信息...")
            self.list_formats(url)
            raise Exception(f"YouTube视频下载失败: {str(e)}\n"
                          f"请在config.py中调整YOUTUBE_DOWNLOAD_QUALITY设置")

class BilibiliDownloader(VideoDownloader):
    """Bilibili视频下载器"""
    def download(self, url):
        # 确保下载目录存在
        os.makedirs(VIDEO_DIR, exist_ok=True)
        
        try:
            # 首先获取可用格式
            print("正在获取视频信息...")
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                if not formats:
                    raise Exception("没有找到可用的视频格式")
                
                # 检查指定的格式是否可用
                format_ids = [f.get('format_id') for f in formats]
                if BILIBILI_FORMAT != 'best' and BILIBILI_FORMAT not in format_ids:
                    print(f"\n警告: 配置的格式ID '{BILIBILI_FORMAT}' 不可用")
                    self.list_formats(url)
                    print("\n请在config.py中设置正确的BILIBILI_FORMAT")
                    raise Exception(f"格式ID '{BILIBILI_FORMAT}' 不可用")
            
            # 设置下载选项
            ydl_opts = {
                **self.default_opts,
                'format': BILIBILI_FORMAT
            }
            
            # 下载视频
            print(f"使用格式: {BILIBILI_FORMAT}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                if os.path.exists(video_path):
                    return video_path
                raise FileNotFoundError("下载完成但找不到视频文件")
                
        except Exception as e:
            if "formats" not in locals():
                # 如果连格式信息都没获取到，重新尝试获取
                print("\n获取可用格式信息...")
                self.list_formats(url)
            
            raise Exception(f"Bilibili视频下载失败: {str(e)}\n"
                          f"请在config.py中设置BILIBILI_FORMAT为上述可用的format ID之一")

def download_video(url):
    """下载视频的主函数"""
    try:
        downloader = get_downloader(url)
        video_path = downloader.download(url)
        print(f"视频下载成功：{video_path}")
        return video_path
    except Exception as e:
        raise Exception(f"视频下载失败: {str(e)}")
