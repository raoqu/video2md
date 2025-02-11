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

    def select_format(self, url, resolution):
        """根据分辨率选择最佳的视频格式
        
        Args:
            url (str): 视频URL
            resolution (int): 目标分辨率，例如480表示480p
            
        Returns:
            str: 匹配的format_id，如果没有找到合适的格式则返回None
        """
        formats = self.list_formats(url)
        matched_formats = []
        
        for fmt in formats:
            # 跳过没有文件大小信息的格式
            if fmt.get('filesize_str') == 'N/A':
                continue
                
            # 获取分辨率信息
            resolution_str = fmt.get('resolution', '')
            if not resolution_str:
                continue
                
            # 解析分辨率
            try:
                width, height = map(int, resolution_str.split('x'))
                # 如果高度匹配目标分辨率，添加到候选列表
                if height == resolution:
                    matched_formats.append(fmt)
            except (ValueError, TypeError):
                continue
        
        # 如果找到匹配的格式，返回文件大小最小的那个的format_id
        if matched_formats:
            smallest_format = min(matched_formats, 
                                key=lambda x: int(x.get('filesize', float('inf'))))
            return smallest_format.get('format_id')
            
        return None

    def download(self, url):
        raise NotImplementedError

class YoutubeDownloader(VideoDownloader):
    """YouTube视频下载器"""
    def download(self, url):
        # 确保下载目录存在
        os.makedirs(VIDEO_DIR, exist_ok=True)
        
        def try_download(format_spec):
            """尝试使用指定的格式下载视频"""
            ydl_opts = {**self.default_opts, 'format': format_spec}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                if os.path.exists(video_path):
                    return video_path
                raise FileNotFoundError("下载完成但找不到视频文件")
        
        try:
            # 首先尝试使用配置的质量设置
            return try_download(YOUTUBE_DOWNLOAD_QUALITY)
        except Exception as first_error:
            print(f"\n使用配置的质量设置下载失败: {str(first_error)}")
            print("正在尝试使用备选分辨率...")
            
            # 尝试使用select_format选择合适的格式
            format_id = self.select_format(url, TARGET_RESOLUTION)
            if format_id:
                print(f"找到合适的格式: {format_id}")
                try:
                    return try_download(format_id)
                except Exception as second_error:
                    print(f"\n使用备选格式下载失败: {str(second_error)}")
            
            # 如果都失败了，显示可用格式并抛出异常
            print("\n所有下载尝试都失败了！正在获取可用格式信息...")
            self.list_formats(url)
            raise Exception(f"YouTube视频下载失败: {str(first_error)}\n"
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
