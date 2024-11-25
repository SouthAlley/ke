import os
import re
import requests

# 创建一个全局的 requests.Session
session = requests.Session()
session.headers.update({
    "User-Agent": "Surge iOS/3374"
})

def download_plugins(base_url, filenames):
    """
    下载 .plugin 文件到 Plugins 文件夹。
    """
    os.makedirs("Plugins", exist_ok=True)
    downloaded_files = []
    for filename in filenames:
        url = f"{base_url}/{filename}.plugin"  # 动态拼接 URL
        try:
            response = session.get(url, timeout=2)  # 使用全局 session
            response.raise_for_status()
            file_path = os.path.join("Plugins", f"{filename}.plugin")
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"Downloaded: {file_path}")
            downloaded_files.append(file_path)
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
            response = session.get(url, timeout=2)  # 使用全局 session
            response.raise_for_status()
            file_name = os.path.basename(url)
            file_path = os.path.join(output_folder, file_name)
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"Downloaded: {file_path}")
            downloaded.add(url)  # 添加到已下载集合
        except requests.RequestException as e:
            print(f"Failed to download {url}. Error: {e}")

def process_plugins(base_url, filenames):
    """
    先下载 .plugin 文件，再从中提取 script-path 并下载 JS 文件。
    """
    print("Step 1: Downloading .plugin files...")
    plugin_files = download_plugins(base_url, filenames)  # 下载 .plugin 文件

    print("\nStep 2: Extracting script paths and downloading .js files...")
    all_script_paths = set()  # 用集合去重所有提取到的 script-path

    for plugin_file in plugin_files:
        print(f"\nProcessing file: {plugin_file}")
        script_paths = extract_script_paths(plugin_file)  # 提取 script-path
        all_script_paths.update(script_paths)  # 合并到全局集合

    # 下载所有唯一的 JS 文件
    if all_script_paths:
        print(f"\nUnique script paths to download: {all_script_paths}")
        download_js_files(all_script_paths)
    else:
        print("No script-path URLs found in the files.")

if __name__ == "__main__":
    base_url = "https://kelee.one/Tool/Loon/Plugin"
    filenames = ["NeteaseCloudMusic_remove_ads",
                 "Taobao_remove_ads",
                 "WexinMiniPrograms_Remove_ads",
                 "Cainiao_remove_ads.plugin",
                 "Remove_ads_by_keli",
                 "BlockAdvertisers",
                 "Tieba_remove_ads",
                 "Zhihu_remove_ads",
                 "CoolApk_remove_ads",
                 "RedPaper_remove_ads",
                 "JD_remove_ads",
                 "ZhuanZhuan_remove_ads",
                 "XiaoHeiHe_remove_ads",
                 "FleaMarket_remove_ads",
                 "PinDuoDuo_remove_ads",
                 "Amap_remove_ads"
                ]
    process_plugins(base_url, filenames)
