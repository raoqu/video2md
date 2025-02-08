import os
import requests
from config import *
from image import format_timestamp

def process_with_local_llm(text):
    """使用本地LLM处理文本
    
    Args:
        text (str): 需要处理的原始文本
        
    Returns:
        str: 处理后的文本，如果处理失败则返回原文
    """
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
        response = requests.post(LLM_SERVER_URL, 
                               headers=headers, 
                               json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"LLM处理失败: {response.text}")
            return text  # 处理失败时返回原文
            
    except requests.exceptions.RequestException as e:
        print(f"LLM服务器连接失败: {str(e)}")
        return text
    except Exception as e:
        print(f"LLM处理异常: {str(e)}")
        return text

def generate_markdown(text, image_paths, positions, output_md):
    """生成 Markdown 文件
    
    Args:
        text (str): 要处理的文本内容
        image_paths (list): 图片文件路径列表
        positions (list): 图片对应的视频时间戳列表
        output_md (str): 输出的markdown文件路径
    """
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
    """保存文本到文件
    
    Args:
        text (str): 要保存的文本内容
        txt_path (str): 文本文件保存路径
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(txt_path), exist_ok=True)
        
        # 保存文本文件
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
    except Exception as e:
        raise Exception(f"保存文本文件失败: {str(e)}")