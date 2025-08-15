import os
import re
import requests

# 相当于 http-request header-replace User-Agent
headers = {
    'User-Agent': 'Surge iOS/3374'
}

# 响应头模拟（Python不能直接改服务器的响应头，但可以自己加到对象上）
response_headers_override = {
    'Content-Disposition': 'inline',
    'Content-Type': 'text/plain; charset=utf-8'
}

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

def request_with_override(url):
    """
    发起请求，并模拟 http-response 规则
    """
    response = requests.get(url, headers=headers, timeout=5)
    # 在返回的 response 对象中添加自定义响应头（仅本地使用）
    for k, v in response_headers_override.items():
        response.headers[k] = v
    return response

def download_plugins(plugin_entries):
    os.makedirs("Plugins", exist_ok=True)
    downloaded_files = []

    for title, url in plugin_entries:
        filename = os.path.basename(url)
        file_path = os.path.join("Plugins", filename)

        try:
            response = request_with_override(url)
            response.raise_for_status()
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"插件下载成功: {file_path} (模拟响应头: {response_headers_override})")
            downloaded_files.append(file_path)
        except requests.RequestException as e:
            print(f"插件 {title} 下载失败: {e}")

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

        try:
            response = request_with_override(url)
            response.raise_for_status()
            file_name = os.path.basename(url)
            file_path = os.path.join(output_folder, file_name)
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"JS 文件下载成功: {file_path} (模拟响应头: {response_headers_override})")
            downloaded.add(url)
        except requests.RequestException as e:
            print(f"JS 文件 {url} 下载失败: {e}")

def process_plugins_from_local_readme(readme_path="README.md"):
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
