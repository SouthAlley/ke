import os
import re
import requests

# 保持全局 headers，方便复用
headers = {
    'User-Agent': 'Surge iOS/3374'
}

# ==============================================================================
# 变化 1: 引入新的、统一的下载函数
# 这个函数将取代原来在 download_plugins 和 download_js_files 中的下载逻辑
# ==============================================================================
def download_file(url, file_path, item_name="文件"):
    """
    一个健壮的、支持代理的统一文件下载函数。
    - item_name: 用于在日志中显示更友好的名称 (例如 "插件", "JS 文件")
    - 返回 True 表示成功, False 表示失败
    """
    proxy_url = os.environ.get('HTTP_PROXY_URL')
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    } if proxy_url else None
    
    proxy_info = " (使用代理)" if proxies else ""

    try:
        response = requests.get(url, headers=headers, timeout=20, proxies=proxies)
        response.raise_for_status()  # 如果 HTTP 状态码表示错误, 则抛出异常

        # 确保保存文件的目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as file:
            file.write(response.content)
        
        # 使用 os.path.basename 只显示文件名，让日志更整洁
        print(f"✅ {item_name}下载成功: {os.path.basename(file_path)}")
        return True
        
    except requests.RequestException as e:
        print(f"❌ {item_name}下载失败{proxy_info}: {url} -> {e}")
        return False

# ==============================================================================
# 无需修改的函数
# ==============================================================================
def extract_plugin_urls(md_file_path):
    """
    从 README.md 中提取 .plugin 文件的 URL (此函数保持不变)
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

def extract_script_paths(file_path):
    """
    从 .plugin 文件中提取 script-path 的 URL (此函数保持不变)
    """
    script_paths = []
    try:
        # 使用 errors='ignore' 增强文件读取的鲁棒性
        with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
            content = file.read()
            script_paths = re.findall(r'script-path\s*=\s*(https?://[^\s]+\.js)', content)
    except Exception as e:
        print(f"无法读取文件 {file_path}: {e}")

    return script_paths

# ==============================================================================
# 变化 2: 修改 download_plugins 函数以调用新的 download_file
# ==============================================================================
def download_plugins(plugin_entries):
    """
    下载 .plugin 文件到 Plugins 目录 (已重构)
    """
    os.makedirs("Plugins", exist_ok=True)
    downloaded_files = []

    for title, url in plugin_entries:
        filename = os.path.basename(url)
        file_path = os.path.join("Plugins", filename)

        # 直接调用新的下载函数，代码更简洁
        if download_file(url, file_path, item_name=f"插件 '{title}'"):
            downloaded_files.append(file_path)

    return downloaded_files

# ==============================================================================
# 变化 3: 修改 download_js_files 函数以调用新的 download_file
# ==============================================================================
def download_js_files(script_paths, output_folder="Scripts"):
    """
    下载 script-path 对应的 JS 文件 (已重构)
    """
    os.makedirs(output_folder, exist_ok=True)
    downloaded = set()

    for url in script_paths:
        if url in downloaded:
            # print(f"跳过 (已下载): {url}") # 可以选择性保留或移除
            continue

        # 清理 URL，移除可能的查询参数以生成文件名
        file_name = os.path.basename(url.split('?')[0])
        file_path = os.path.join(output_folder, file_name)
        
        # 同样调用新的下载函数
        if download_file(url, file_path, item_name="JS 文件"):
            downloaded.add(url)


# ==============================================================================
# 主逻辑函数，无需修改
# ==============================================================================
def process_plugins_from_local_readme(readme_path="README.md"):
    """
    直接从本地 README.md 开始处理 (此函数保持不变)
    """
    print("步骤 1: 提取 .plugin 文件 URL")
    plugin_entries = extract_plugin_urls(readme_path)

    if not plugin_entries:
        print("未找到任何 .plugin 文件")
        return

    print(f"找到 {len(plugin_entries)} 个插件:")
    # for title, link in plugin_entries:
    #     print(f"- {title}") # 可以简化打印，避免刷屏

    print("\n步骤 2: 下载 .plugin 文件")
    plugin_files = download_plugins(plugin_entries)

    print("\n步骤 3: 提取 script-path 并下载 .js 文件")
    all_script_paths = set()

    for plugin_file in plugin_files:
        script_paths = extract_script_paths(plugin_file)
        all_script_paths.update(script_paths)
    
    unique_script_paths = sorted(list(all_script_paths))

    if unique_script_paths:
        print(f"\n找到 {len(unique_script_paths)} 个唯一的 JS 文件需要下载:")
        download_js_files(unique_script_paths)
    else:
        print("未找到任何 script-path URL")
        
    print("\n所有任务已完成。")

if __name__ == "__main__":
    process_plugins_from_local_readme("README.md")
