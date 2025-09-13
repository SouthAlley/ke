
import os
import re
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# 定义一个全局的请求头，方便复用
HEADERS = {
    "User-Agent": "Surge iOS/3374"
}

def download_file(url, file_path):
    """
    一个健壮的、支持代理的文件下载函数。
    
    它会自动从环境变量 HTTP_PROXY_URL 中读取代理设置。
    返回一个元组 (file_path, success_boolean)，表示下载的文件路径和是否成功。
    """
    if not url:
        return None, False

    # 1. 从环境变量中获取代理设置
    proxy_url = os.environ.get('HTTP_PROXY_URL')
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    } if proxy_url else None
    
    # 调试信息：如果使用了代理，就打印出来
    proxy_info = " (使用代理)" if proxies else ""

    try:
        # 2. 在请求中加入 proxies 参数
        response = requests.get(url, headers=HEADERS, timeout=20, proxies=proxies)
        response.raise_for_status()  # 如果状态码不是 2xx，则抛出 HTTPError

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as file:
            file.write(response.content)
        # 返回成功下载的文件路径
        return file_path, True
        
    except requests.exceptions.HTTPError as e:
        status_code_info = f"(HTTP {e.response.status_code})" if e.response else ""
        print(f"❌ 下载失败 {status_code_info}{proxy_info} for {url}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败{proxy_info} for {url}: {e}")
    except IOError as e:
        print(f"❌ 文件写入失败 for {file_path}: {e}")
    
    # 如果发生任何错误，返回 URL 和失败状态
    return url, False

def batch_download(urls_to_paths_map, max_workers=10):
    """使用线程池并发下载多个文件。"""
    successful_downloads = []
    if not urls_to_paths_map:
        return successful_downloads

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(download_file, url, path): url for url, path in urls_to_paths_map.items()}
        
        total_files = len(urls_to_paths_map)
        for i, future in enumerate(as_completed(future_to_url), 1):
            url = future_to_url[future]
            try:
                path, success = future.result()
                if success:
                    print(f"✅ [{i}/{total_files}] 下载成功: {os.path.basename(path)}")
                    successful_downloads.append(path)
                else:
                    # 具体的错误信息已在 download_file 中打印
                    print(f"➖ [{i}/{total_files}] 未能下载: {url}")
            except Exception as e:
                print(f"❌ [{i}/{total_files}] 下载 {url} 时发生意外错误: {e}")
    return successful_downloads

def extract_plugin_urls(md_file_path):
    """从 Markdown 文件中解析插件 URL。"""
    try:
        with open(md_file_path, "r", encoding="utf-8") as file:
            content = file.read()
        pattern = re.compile(r'https://www.nsloon.com/openloon/import\?plugin=([^"]+)')
        return sorted(list(set(pattern.findall(content))))
    except FileNotFoundError:
        print(f"❌ 错误: 文件 '{md_file_path}' 未找到。")
        return []
    except Exception as e:
        print(f"❌ 解析 {md_file_path} 失败: {e}")
        return []

def extract_script_urls(file_path):
    """从插件文件中解析出 script-path 的 URL。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
            content = file.read()
        return set(re.findall(r'script-path\s*=\s*(https?://[^\s,]+\.js)', content))
    except Exception as e:
        print(f"⚠️ 无法读取或解析 {file_path}: {e}")
        return set()

def main(args):
    """主处理函数"""
    # 步骤 1: 从 README 中提取 .plugin 文件的 URL
    print(f"▶️ 步骤 1: 正在解析 '{args.readme}' 以查找插件...")
    plugin_urls = extract_plugin_urls(args.readme)

    if not plugin_urls:
        print("未找到任何 .plugin 文件，程序退出。")
        return

    print(f"   找到 {len(plugin_urls)} 个插件 URL。")

    # 步骤 2: 并发下载所有 .plugin 文件
    print("\n▶️ 步骤 2: 正在下载 .plugin 文件...")
    plugins_dir = os.path.join(args.outdir, "Plugins")
    
    plugin_download_map = {
        url: os.path.join(plugins_dir, os.path.basename(url))
        for url in plugin_urls
    }
    downloaded_plugin_files = batch_download(plugin_download_map, max_workers=args.workers)

    # 步骤 3: 从所有下载的插件中提取 script-path
    print("\n▶️ 步骤 3: 正在从已下载的插件中提取脚本 URL...")
    all_script_urls = set()
    for plugin_file in downloaded_plugin_files:
        script_urls = extract_script_urls(plugin_file)
        if script_urls:
            all_script_urls.update(script_urls)
    
    if not all_script_urls:
        print("   在所有插件中均未找到 script-path URL，程序完成。")
        return
        
    print(f"   共找到 {len(all_script_urls)} 个唯一的 JS 脚本需要下载。")

    # 步骤 4: 并发下载所有唯一的 .js 文件
    print(f"\n▶️ 步骤 4: 正在下载所有 JS 脚本...")
    scripts_dir = os.path.join(args.outdir, "Scripts")
    
    script_download_map = {
        url: os.path.join(scripts_dir, os.path.basename(url.split('?')[0])) 
        for url in all_script_urls
    }
    batch_download(script_download_map, max_workers=args.workers)
    
    print("\n✨ 所有任务已完成。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 README.md 文件中下载 Loon 插件及其关联的 JS 脚本。")
    parser.add_argument(
        "--readme",
        type=str,
        default="README.md",
        help="输入的 README.md 文件路径。"
    )
    parser.add_argument(
        "-o", "--outdir",
        type=str,
        default=".",
        help="输出目录，'Plugins' 和 'Scripts' 文件夹将被创建在这里。"
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=10,
        help="并发下载的线程数。"
    )
    
    args = parser.parse_args()
    main(args)
