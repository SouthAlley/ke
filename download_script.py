import os
import re
import requests

# 修改 headers，使用正确的 Referer 来通过防盗链检查
headers = {
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "connection": "keep-alive",
    # 关键：Referer 必须是资源的“来源”站点，这里是 nsloon.com
    "Referer": "https://www.nsloon.com/", 
    "user-agent": "Surge iOS/3374"
}


def download_file(url, file_path):
    """
    一个健壮的、可重用的文件下载函数。
    - 使用预设的 headers。
    - 包含详细的错误处理。
    - 返回 True 表示成功，False 表示失败。
    """
    print(f"  -> 正在尝试下载: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        with open(file_path, "wb") as file:
            file.write(response.content)
            
        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
             print(f"❌ 下载失败 (HTTP 403 Forbidden): 服务器拒绝了请求。请检查 headers (特别是 User-Agent 和 Referer) 是否正确。URL: {url}")
        else:
             print(f"❌ 下载失败 (HTTP错误): {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 下载失败 (连接错误): {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ 下载失败 (请求超时): {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败 (未知请求错误): {e}")
    except IOError as e:
        print(f"❌ 文件写入失败: {e}")
        
    return False


def extract_plugin_urls(md_file_path):
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
    os.makedirs("Plugins", exist_ok=True)
    downloaded_files = []

    for title, url in plugin_entries:
        filename = os.path.basename(url)
        file_path = os.path.join("Plugins", filename)
        
        print(f"处理插件: {title}")
        if download_file(url, file_path):
            print(f"✅ 插件下载成功: {file_path}")
            downloaded_files.append(file_path)

    return downloaded_files


def extract_script_paths(file_path):
    script_paths = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            script_paths = re.findall(r'script-path\s*=\s*(https?://[^\s]+\.js)', content)
    except Exception as e:
        print(f"无法读取文件 {file_path}: {e}")

    return script_paths


def download_js_files(script_paths, output_folder="Scripts"):
    os.makedirs(output_folder, exist_ok=True)
    downloaded = set()

    for url in script_paths:
        if url in downloaded:
            print(f"跳过 (已下载): {url}")
            continue

        file_name = os.path.basename(url)
        file_path = os.path.join(output_folder, file_name)

        if download_file(url, file_path):
            print(f"✅ JS 文件下载成功: {file_path}")
            downloaded.add(url)


def process_plugins_from_local_readme(readme_path="README.md"):
    print("步骤 1: 提取 .plugin 文件 URL")
    plugin_entries = extract_plugin_urls(readme_path)

    if not plugin_entries:
        print("未找到任何 .plugin 文件")
        return

    print(f"找到 {len(plugin_entries)} 个插件:")
    for title, link in plugin_entries:
        print(f"- {title}: {link}")

    print("\n步骤 2: 下载 .plugin 文件")
    plugin_files = download_plugins(plugin_entries)

    print("\n步骤 3: 提取 script-path 并下载 .js 文件")
    all_script_paths = set()

    for plugin_file in plugin_files:
        script_paths = extract_script_paths(plugin_file)
        all_script_paths.update(script_paths)

    if all_script_paths:
        print(f"\n找到 {len(all_script_paths)} 个唯一的 JS 文件 URL，准备下载...")
        download_js_files(all_script_paths)
    else:
        print("在已下载的插件中未找到任何 script-path URL")


if __name__ == "__main__":
    process_plugins_from_local_readme("README.md")
