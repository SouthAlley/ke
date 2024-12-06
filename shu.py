import os
import re
import requests

# 创建一个全局的 requests.Session
session = requests.Session()
session.headers.update({
    "User-Agent": "Surge iOS/3374"
})

def download_file(url, output_folder="Plugins"):
    """
    下载单个文件到指定文件夹。
    """
    os.makedirs(output_folder, exist_ok=True)  # 确保目标文件夹存在
    file_name = os.path.basename(url)  # 从 URL 提取文件名
    file_path = os.path.join(output_folder, file_name)

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Downloaded: {file_path}")
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

def download_js_files(script_paths, output_folder="Scripts"):
    """
    下载从 script-path 提取的 JS 文件到 Scripts 文件夹，避免重复下载。
    """
    os.makedirs(output_folder, exist_ok=True)
    downloaded = set()  # 使用集合跟踪已下载的文件 URL

    for url in script_paths:
        if url in downloaded:
            print(f"Skipped (already downloaded): {url}")
            continue

        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            file_name = os.path.basename(url)
            file_path = os.path.join(output_folder, file_name)
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"Downloaded: {file_path}")
            downloaded.add(url)
        except requests.RequestException as e:
            print(f"Failed to download {url}. Error: {e}")

def process_multiple_files(url_list):
    """
    处理多个 .sgmodule 文件链接。
    """
    for url in url_list:
        print(f"\nProcessing URL: {url}")

        # Step 1: 下载 .sgmodule 文件
        sgmodule_file = download_file(url)

        if sgmodule_file:
            # Step 2: 提取 script-path
            print("\nExtracting script paths...")
            script_paths = extract_script_paths(sgmodule_file)

            if script_paths:
                print(f"Found script paths: {script_paths}")

                # Step 3: 下载提取到的 JS 文件
                print("\nDownloading JS files...")
                download_js_files(script_paths)
            else:
                print("No script-path URLs found in the .sgmodule file.")

if __name__ == "__main__":
    url_list = [
        "https://github.com/BiliUniverse/Enhanced/releases/latest/download/BiliBili.Enhanced.sgmodule"
    ]

    # 处理所有链接
    process_multiple_files(url_list)
