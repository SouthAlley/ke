import os
import requests

def download_content():
    url = "https://kelee.one/Resource/Script/NeteaseCloudMusic/NeteaseCloudMusic_remove_ads.js"  # 这里替换成实际的URL
    headers = {
        "User-Agent": "Surge iOS/3374"
    }
    
    # 检查Scripts文件夹是否存在，如果不存在则创建
    os.makedirs("Scripts", exist_ok=True)
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        with open("Scripts/downloaded_content", "wb") as file:
            file.write(response.content)
        print("Download successful!")
    else:
        print(f"Failed to download content. Status code: {response.status_code}")

if __name__ == "__main__":
    download_content()
