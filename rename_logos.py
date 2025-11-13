#!/usr/bin/env python3
"""
rename_logos.py

命令行工具：将目标目录下的图片重命名（并转换为 PNG）为 logo<宽>x<高>.png

用法示例:
  python rename_logos.py . --recursive --delete-original

功能:
 - 支持递归或仅当前目录
 - 支持 dry-run 模式只打印将要执行的操作
 - 支持删除原始文件（可选）
 - 如果目标文件名已存在，自动追加序号避免覆盖（logo800x600_1.png）
"""
import os
import argparse
from PIL import Image


def find_image_files(target_dir, exts, recursive=False):
    exts = tuple('.' + e.lower().lstrip('.') for e in exts)
    if recursive:
        for root, _, files in os.walk(target_dir):
            for f in files:
                if f.lower().endswith(exts):
                    yield os.path.join(root, f)
    else:
        for f in os.listdir(target_dir):
            path = os.path.join(target_dir, f)
            if os.path.isfile(path) and f.lower().endswith(exts):
                yield path


def unique_target_path(dirpath, base_name):
    """如果 base_name 已存在，在文件名后追加 _1, _2 ... 返回可用完整路径"""
    candidate = os.path.join(dirpath, base_name)
    if not os.path.exists(candidate):
        return candidate
    name, ext = os.path.splitext(base_name)
    i = 1
    while True:
        new_name = f"{name}_{i}{ext}"
        candidate = os.path.join(dirpath, new_name)
        if not os.path.exists(candidate):
            return candidate
        i += 1


def process_file(path, delete_original=False, dry_run=False, verbose=False):
    try:
        with Image.open(path) as im:
            w, h = im.size
            dirpath = os.path.dirname(path)
            base = f"logo{w}x{h}.png"
            target = unique_target_path(dirpath, base)

            if dry_run:
                print(f"[DRY] {path} -> {target}")
                return True

            # 如果原文件已与目标相同（路径相同，扩展名可能相同），跳过
            if os.path.abspath(path) == os.path.abspath(target):
                if verbose:
                    print(f"跳过（已是目标名）: {path}")
                return True

            # 保存为 PNG（会覆盖同名文件已由 unique_target_path 避免）
            # 保证转换为 RGB 或 RGBA 以正确保存
            mode = im.mode
            if mode in ("RGBA", "LA"):
                out = im.convert("RGBA")
            else:
                out = im.convert("RGB")
            out.save(target, format='PNG')
            if verbose:
                print(f"保存: {target}")

            if delete_original:
                try:
                    os.remove(path)
                    if verbose:
                        print(f"已删除原文件: {path}")
                except Exception as e:
                    print(f"无法删除原文件 {path}: {e}")

            return True
    except Exception as e:
        print(f"处理失败 {path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Rename/convert images to logo<WxH>.png')
    parser.add_argument('target', help='目标目录')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归遍历子目录')
    parser.add_argument('-e', '--ext', default='png,jpg,jpeg,gif,bmp,webp',
                        help='逗号分隔的文件扩展名列表（不含点），默认: png,jpg,jpeg,gif,bmp,webp')
    parser.add_argument('-n', '--dry-run', action='store_true', help='仅打印操作，不实际修改')
    parser.add_argument('-d', '--delete-original', action='store_true', help='保存后删除原始文件')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    target_dir = args.target
    if not os.path.isdir(target_dir):
        print(f"目标目录不存在: {target_dir}")
        return

    exts = [x.strip() for x in args.ext.split(',') if x.strip()]
    files = list(find_image_files(target_dir, exts, recursive=args.recursive))
    if not files:
        print("未找到匹配的图片文件。")
        return

    print(f"找到 {len(files)} 个文件。处理开始...")
    success = 0
    for p in files:
        ok = process_file(p, delete_original=args.delete_original, dry_run=args.dry_run, verbose=args.verbose)
        if ok:
            success += 1

    print(f"完成。成功处理 {success}/{len(files)} 个文件。")


if __name__ == '__main__':
    main()
