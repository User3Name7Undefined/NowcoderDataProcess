import os
import json
import time
import re
import mimetypes
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def load_config(config_file='config.json'):
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def read_user_ids(path):
    ids = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if s:
                    ids.append(s)
    except FileNotFoundError:
        print(f"用户ID清单文件不存在: {path}")
    return ids


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def download_image(url, dst_path, headers=None, timeout=10):
    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=timeout)
        if resp.status_code == 200:
            # 检查 content-type
            content_type = resp.headers.get('Content-Type', '')
            if not content_type.startswith('image'):
                # 有些链接会重定向到 HTML，跳过
                return False, 'not-image'
            with open(dst_path, 'wb') as f:
                for chunk in resp.iter_content(1024 * 8):
                    if chunk:
                        f.write(chunk)
            return True, None
        return False, f'status-{resp.status_code}'
    except Exception as e:
        return False, str(e)


def find_avatar_url_from_profile(html):
    soup = BeautifulSoup(html, 'html.parser')
    # 通常头像在 <a class="head-pic"> <img src=...>
    a = soup.find('a', class_=lambda c: c and 'head-pic' in c)
    if a:
        img = a.find('img')
        if img and img.get('src'):
            return img.get('src')

    # 备选：直接找页面中的第一个 img，或带"avatar"/"head"关键词的
    imgs = soup.find_all('img')
    for img in imgs:
        src = img.get('src', '')
        if 'avatar' in src or 'head' in src or 'profile' in src:
            return src
    return None


def main():
    cfg = load_config()
    files_cfg = cfg.get('files', {})
    
    # 添加Output/前缀
    user_ids_file_raw = files_cfg.get('user_id_list')
    user_ids_file = f'Output/{user_ids_file_raw}' if user_ids_file_raw and not user_ids_file_raw.startswith('Output/') else user_ids_file_raw
    
    avatar_dir_raw = files_cfg.get('avatar_dir')
    avatar_dir = f'Output/{avatar_dir_raw}' if avatar_dir_raw and not avatar_dir_raw.startswith('Output/') else avatar_dir_raw

    ids = read_user_ids(user_ids_file)
    if not ids:
        print('没有要处理的用户ID，退出。')
        return

    ensure_dir(avatar_dir)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/116.0 Safari/537.36'
    }

    for idx, uid in enumerate(ids, 1):
        print(f'[{idx}/{len(ids)}] 处理用户 {uid} ...')
        profile_url = f'https://ac.nowcoder.com/acm/contest/profile/{uid}'
        try:
            r = requests.get(profile_url, headers=headers, timeout=10)
            if r.status_code != 200:
                print(f'  无法获取用户页面: HTTP {r.status_code}')
                continue
            avatar_url = find_avatar_url_from_profile(r.text)
            if not avatar_url:
                print('  未找到头像链接')
                continue

            # 处理相对或协议相对的 URL
            if avatar_url.startswith('//'):
                avatar_url = 'https:' + avatar_url
            elif avatar_url.startswith('/'):
                parsed = urlparse(profile_url)
                avatar_url = f"{parsed.scheme}://{parsed.netloc}{avatar_url}"

            # 决定扩展名
            parsed = urlparse(avatar_url)
            root, ext = os.path.splitext(parsed.path)
            ext = ext.split('?')[0]
            if not ext:
                # 通过请求头判断
                head = requests.head(avatar_url, headers=headers, allow_redirects=True, timeout=8)
                ct = head.headers.get('Content-Type', '')
                guessed = mimetypes.guess_extension(ct.split(';')[0]) if ct else None
                ext = guessed or '.png'

            # 保存到 avatar_dir/id/photo.png
            user_dir = os.path.join(avatar_dir, uid)
            os.makedirs(user_dir, exist_ok=True)
            dst = os.path.join(user_dir, f"photo{ext}")

            ok, err = download_image(avatar_url, dst, headers=headers)
            if ok:
                print(f'  已保存头像: {dst}')
            else:
                print(f'  下载失败: {err}')

            # 避免被频繁请求封禁，稍作等待
            time.sleep(0.5)

        except Exception as e:
            print(f'  处理时出错: {e}')


if __name__ == '__main__':
    main()
