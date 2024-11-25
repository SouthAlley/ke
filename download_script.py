import os
import re
import requests
from urllib.parse import urlparse

def download_plugins(base_url, filenames):
    """
    下载 .plugin 文件到 Plugins 文件夹。
    """
    headers = {
        "User-Agent": "Surge iOS/3374"
    }

    # 检查 Plugins 文件夹是否存在，如果不存在则创建
    os.makedirs("Plugins", exist_ok=True)

    downloaded_files = []
    for filename in filenames:
        url = f"{base_url}/{filename}.plugin"  # 动态拼接 URL
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # 检查是否有 HTTP 错误

            # 保存文件
            file_path = os.path.join("Plugins", f"{filename}.plugin")
            with open(file_path, "wb") as file:
                file.write(response.content)

            print(f"Downloaded: {file_path}")
            downloaded_files.append(file_path)  # 记录已下载的文件路径
        except requests.RequestException as e:
            print(f"Failed to download {filename}.plugin. Error: {e}")
    return downloaded_files

def extract_script_paths(file_path):
    """
    从 .plugin 文件中提取 script-path 的 URL。
    """
    script_paths = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            # 使用正则表达式提取 script-path 的 URL
            script_paths = re.findall(r'script-path\s*=\s*(https?://[^\s]+\.js)', content)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return script_paths

def download_js_files(script_paths, output_folder="Scripts"):
    """
    下载从 script-path 提取的 JS 文件到 Scripts 文件夹。
    """
    os.makedirs(output_folder, exist_ok=True)

    for url in script_paths:
        try:
            # 提取文件名
            file_name = os.path.basename(url)
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # 保存到 Scripts 文件夹
            file_path = os.path.join(output_folder, file_name)
            with open(file_path, "wb") as file:
                file.write(response.content)
            
            print(f"Downloaded: {file_path}")
        except requests.RequestException as e:
            print(f"Failed to download {url}. Error: {e}")

def process_plugins(base_url, filenames):
    """
    先下载 .plugin 文件，再从中提取 script-path 并下载 JS 文件。
    """
    print("Step 1: Downloading .plugin files...")
    plugin_files = download_plugins(base_url, filenames)  # 下载 .plugin 文件

    print("\nStep 2: Extracting script paths and downloading .js files...")
    for plugin_file in plugin_files:
        print(f"\nProcessing file: {plugin_file}")
        script_paths = extract_script_paths(plugin_file)  # 提取 script-path
        if script_paths:
            print(f"Found script paths: {script_paths}")
            download_js_files(script_paths)  # 下载 .js 文件
        else:
            print("No script-path URLs found in the file.")

if __name__ == "__main__":
    # 基础 URL
    base_url = "https://kelee.one/Tool/Loon/Plugin"
    # 动态文件名列表
    filenames = ["Taobao_remove_ads", "NeteaseCloudMusic_remove_ads"]  # 替换成实际需要的文件名
    process_plugins(base_url, filenames)
