import os
import requests
from urllib.parse import urlparse

def download_plugins(base_url, filenames):
    headers = {
        "User-Agent": "Surge iOS/3374"
    }

    # 检查 Plugins 文件夹是否存在，如果不存在则创建
    os.makedirs("Plugins", exist_ok=True)

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
        except requests.RequestException as e:
            print(f"Failed to download {filename}.plugin. Error: {e}")

if __name__ == "__main__":
    # 基础 URL
    base_url = "https://kelee.one/Tool/Loon/Plugin"
    # 动态文件名列表
    filenames = ["plugin1", "plugin2", "plugin3"]  # 替换成实际需要的文件名
    download_plugins(base_url, filenames)
