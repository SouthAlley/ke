import os
import re
import requests

# 创建会话并统一设置 User-Agent
session = requests.Session()
session.headers.update({"User-Agent": "Surge iOS/3374"})

def extract_plugin_urls(md_file_path):
    """
    从 README.md 中提取 .plugin 文件的 URL
    """
    try:
        with open(md_file_path, "r", encoding="utf-8") as file:
            content = file.read()

        pattern = re.compile(
            r'<td><a href="https://www.nsloon.com/openloon/import\?plugin=([^"]+)">([^<]+)</a></td>'
        )
        results = [(title, plugin_url) for plugin_url, title in pattern.findall(content)]
        return results
    except Exception as e:
        print(f"解析 {md_file_path} 失败: {e}")
        return []

def download_plugins(plugin_entries):
    """
    下载 .plugin 文件到 Plugins 目录
    """
    os.makedirs("Plugins", exist_ok=True)
    downloaded_files = []

    for title, url in plugin_entries:
        filename = os.path.basename(url)
        file_path = os.path.join("Plugins", filename)

        try:
            response = session.get(url, timeout=5)  # 使用统一 UA
            response.raise_for_status()
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"插件下载成功: {file_path}")
            downloaded_files.append(file_path)
        except requests.RequestException as e:
            print(f"插件 {title} 下载失败: {e}")

    return downloaded_files

def extract_script_paths(file_path):
    """
    从 .plugin 文件中提取 script-path 的 URL
    """
    script_paths = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            script_paths = re.findall(r'script-path\s*=\s*(https?://[^\s]+\.js)', content)
    except Exception as e:
        print(f"无法读取文件 {file_path}: {e}")

    return script_paths

def download_js_files(script_paths, output_folder="Scripts"):
    """
    下载 script-path 对应的 JS 文件
    """
    os.makedirs(output_folder, exist_ok=True)
    downloaded = set()

    for url in script_paths:
        if url in downloaded:
            print(f"跳过 (已下载): {url}")
            continue

        try:
            response = session.get(url, timeout=5)  # 使用统一 UA
            response.raise_for_status()
            file_name = os.path.basename(url)
            file_path = os.path.join(output_folder, file_name)
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"JS 文件下载成功: {file_path}")
            downloaded.add(url)
        except requests.RequestException as e:
            print(f"JS 文件 {url} 下载失败: {e}")

def process_plugins_from_local_readme(readme_path="README.md"):
    """
    直接从本地 README.md 开始处理
    """
    print("步骤 1: 提取 .plugin 文件 URL")
    plugin_entries = extract_plugin_urls(readme_path)

    if not plugin_entries:
        print("未找到任何 .plugin 文件")
        return

    print(f"找到 {len(plugin_entries)} 个插件:")
    for title, link in plugin_entries:
        print(f"{title}: {link}")

    print("\n步骤 2: 下载 .plugin 文件")
    plugin_files = download_plugins(plugin_entries)

    print("\n步骤 3: 提取 script-path 并下载 .js 文件")
    all_script_paths = set()

    for plugin_file in plugin_files:
        script_paths = extract_script_paths(plugin_file)
        all_script_paths.update(script_paths)

    if all_script_paths:
        print(f"\n找到 {len(all_script_paths)} 个 JS 文件:")
        download_js_files(all_script_paths)
    else:
        print("未找到任何 script-path URL")

if __name__ == "__main__":
    process_plugins_from_local_readme("README.md")
