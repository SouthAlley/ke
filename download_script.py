import os
import re
import requests

# 保留你指定的详细请求头
# 这个请求头对于防止 403 Forbidden 错误至关重要
headers = {
    # 'accept-encoding' requests库会自动处理，通常无需手动设置
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    # 'content-type' 通常在POST请求中指定，对于GET请求不是必需的
    "connection": "keep-alive",
    # 解决 403 错误的关键 User-Agent
    "user-agent": "Surge iOS/3374"
}


def download_file(url, file_path):
    print(f"  -> 正在尝试下载: {url}")
    try:
        # 使用 requests.get() 发送请求，带上 headers 和 timeout
        response = requests.get(url, headers=headers, timeout=10)

        # 检查HTTP响应状态码，如果不是 2xx，则会抛出 HTTPError 异常
        response.raise_for_status()

        # 使用 'wb' (二进制写入) 模式保存文件，这对于任何类型的文件都是安全的
        with open(file_path, "wb") as file:
            file.write(response.content)
            
        return True # 下载成功，返回 True

    # 捕获并处理各种可能的异常，提供更清晰的错误信息
    except requests.exceptions.HTTPError as e:
        print(f"❌ 下载失败 (HTTP错误): {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 下载失败 (连接错误): {e}")
    except requests.exceptions.Timeout as e:
        print(f"❌ 下载失败 (请求超时): {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败 (未知请求错误): {e}")
    except IOError as e:
        print(f"❌ 文件写入失败: {e}")
        
    return False # 下载失败，返回 False


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
        # 调用我们的通用下载函数
        if download_file(url, file_path):
            print(f"✅ 插件下载成功: {file_path}") # 已移除 response_headers_override 的打印
            downloaded_files.append(file_path)
        # 失败信息已在 download_file 函数中打印

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

        # 再次调用我们的通用下载函数
        if download_file(url, file_path):
            print(f"✅ JS 文件下载成功: {file_path}") # 已移除 response_headers_override 的打印
            downloaded.add(url)
        # 失败信息已在 download_file 函数中打印


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
