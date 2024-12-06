import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# 创建一个全局的 requests.Session
session = requests.Session()
session.headers.update({
    "User-Agent": "Surge iOS/3374"
})

# 设置替换的 base URL
REPLACE_BASE_URL = "https://raw.githubusercontent.com/SouthAlley/ke/main/Scripts/AliYunDrive/"

def download_file(url, output_folder="Plugins"):
    """
    下载单个文件到指定文件夹，返回文件路径。
    """
    os.makedirs(output_folder, exist_ok=True)
    # 从 URL 中提取 "Enhanced" 和文件名
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')  # 分割 URL 路径
    prefix = path_parts[1]  # 获取 URL 路径中的第二个部分作为前缀（例如 'Enhanced'）
    base_name = os.path.basename(parsed_url.path)  # 提取文件名部分
    custom_filename = f"{prefix}.{base_name}"  # 拼接文件名前缀

    file_path = os.path.join(output_folder, custom_filename)

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded and saved as: {file_path}")
        return file_path
    except requests.RequestException as e:
        print(f"Failed to download {url}. Error: {e}")
        return None

def extract_script_paths(file_path):
    """
    从 .sgmodule 文件中提取 script-path 的 URL。
    """
    script_paths = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            # 使用正则表达式提取 script-path
            script_paths = re.findall(r'script-path\s*=\s*(https?://[^\s]+\.js)', content)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return script_paths

def save_js_with_custom_name(url, output_folder="Scripts"):
    """
    下载 JS 文件并保存为自定义命名，使用从 URL 中提取的前缀和文件名。
    """
    # 从 URL 中提取 "Enhanced" 和文件名
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')  # 分割 URL 路径
    prefix = path_parts[1]  # 获取 URL 路径中的第二个部分作为前缀（例如 'Enhanced'）
    js_filename = os.path.basename(url)  # 提取原文件名
    custom_filename = f"{prefix}.{js_filename}"  # 拼接 Enhanced 和文件名
    file_path = os.path.join(output_folder, custom_filename)

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded and saved as: {file_path}")
        return custom_filename  # 返回自定义的文件名
    except requests.RequestException as e:
        print(f"Failed to download {url}. Error: {e}")
        return None

def replace_script_paths(file_path, script_paths, downloaded_js_files):
    """
    替换本地 .sgmodule 文件中的 script-path URL 为新的路径。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # 遍历提取到的 script-path 替换为新 URL
        for script_path in script_paths:
            js_filename = os.path.basename(script_path)
            if js_filename in downloaded_js_files:
                # 创建新的 URL 替换路径
                new_url = REPLACE_BASE_URL + js_filename
                content = content.replace(script_path, new_url)

        # 保存更新后的文件
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Replaced script-path URLs and saved to: {file_path}")
    except Exception as e:
        print(f"Error replacing script-paths in file {file_path}: {e}")

def download_js_files(script_paths, output_folder="Scripts"):
    """
    下载从 script-path 提取的 JS 文件到 Scripts 文件夹，避免重复下载。
    """
    os.makedirs(output_folder, exist_ok=True)
    downloaded = set()  # 使用集合跟踪已下载的文件 URL
    downloaded_files = []  # 记录下载成功的文件名

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for url in script_paths:
            if url not in downloaded:
                futures[executor.submit(save_js_with_custom_name, url, output_folder)] = url
                downloaded.add(url)

        for future in as_completed(futures):
            url = futures[future]
            try:
                custom_filename = future.result()
                if custom_filename:
                    downloaded_files.append(custom_filename)
            except Exception as e:
                print(f"Failed to download {url}: {e}")

    return downloaded_files

def process_multiple_files(url_list):
    """
    处理多个 .sgmodule 文件链接，只替换本地下载的 .sgmodule 文件。
    """
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for url in url_list:
            futures[executor.submit(process_single_file, url)] = url

        for future in as_completed(futures):
            try:
                future.result()  # 获取每个任务的执行结果
            except Exception as e:
                print(f"Error processing file from URL {futures[future]}: {e}")

def process_single_file(url):
    """
    处理单个 .sgmodule 文件的下载、JS 提取、替换和保存过程，仅替换本地文件。
    """
    print(f"\nProcessing URL: {url}")

    # Step 1: 下载 .sgmodule 文件
    sgmodule_file = download_file(url)

    if sgmodule_file:
        # Step 2: 提取 script-path
        print("\nExtracting script paths...")
        script_paths = extract_script_paths(sgmodule_file)

        if script_paths:
            print(f"Found script paths: {script_paths}")

            # Step 3: 下载提取到的 JS 文件，并保存为自定义文件名
            print("\nDownloading JS files...")
            downloaded_js_files = download_js_files(script_paths)

            # Step 4: 替换本地下载的 .sgmodule 文件中的 script-path
            if downloaded_js_files:
                print("\nReplacing script paths in the .sgmodule file...")
                replace_script_paths(sgmodule_file, script_paths, downloaded_js_files)
        else:
            print("No script-path URLs found in the .sgmodule file.")

if __name__ == "__main__":
    # 多个下载链接
    url_list = [
        "https://github.com/BiliUniverse/Enhanced/releases/latest/download/BiliBili.Enhanced.sgmodule"
    ]

    # 处理所有链接，只替换本地下载的 .sgmodule 文件
    process_multiple_files(url_list)
