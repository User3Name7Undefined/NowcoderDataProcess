
# 牛客竞赛数据爬虫工具集

本项目的目的是将牛客（NowCoder）导出的比赛榜单转换为另一个项目 MergeResolver (https://github.com/SXUas-acm-team/MergeResolver) 需要的榜单格式。
在 MergeResolver 中，理想的工作流是由牛客管理员导出带有用户 id 的榜单文件；但在实际情况中，比赛组织者并不总能及时获得带 id 的导出文件。所以本项目提供一组脚本，用以：

- 读取比赛组织者从牛客导出的榜单（Excel），并结合保存的排行榜 HTML 页面解析/匹配出用户 id；
- 生成包含用户 id 的榜单和用户 id 列表，便于后续在 MergeResolver 中使用；
- 下载用户头像并按竞赛数据包规范重命名/组织图片（便于滚榜时显示学校/队伍标识）。

输入说明：
- 本项目的输入 Excel 是比赛举办者在比赛结束后从牛客上导出的榜单文件（由组织者在牛客管理后台导出或通过“导出”功能生成），请将该文件放在 `Input/` 目录下以供脚本读取。

头像与校徽处理：
- 为了在滚榜或合并榜单时显示学校/队伍标识，本项目支持下载用户头像并按 ICPC tools 的竞赛数据包规范组织图片：
   - 校徽（组织标识 / logo）应存放为：`organizations/<id>/logo<宽>x<高>`
   - 选手/队伍照片应存放为：`teams/<id>/photo`
- 因此仓库中提供了两个相关脚本：`get_user_avatar.py`（抓取并保存用户头像）和 `rename_logos.py`（批量重命名/转换图片以匹配上述命名规范）。详见下面的功能说明。

## 📋 目录

- [功能概述](#功能概述)
- [安装依赖](#安装依赖)
- [配置文件](#配置文件)
- [使用方法](#使用方法)
   - [1. 解析用户ID并生成清单](#1-解析用户id并生成清单)
   - [2. 下载用户头像](#2-下载用户头像)
   - [3. 批量重命名图片](#3-批量重命名图片)
- [常见问题](#常见问题)

---

## 功能概述

### 📊 `get_user_id.py`
- 从本地保存的牛客排行榜 HTML 文件中解析并提取用户昵称 -> 用户ID 的映射（支持多个 HTML 文件）
- 如果仓库中不存在 `config.json`，脚本会自动创建一个配置模板并退出，提示用户编辑后重新运行；配置中的文件名无需包含 `Input/` / `Output/` 前缀，脚本会自动添加。
- 读取比赛组织者导出的 Excel 文件（兼容多种读取引擎：pandas 默认、xlrd、openpyxl）并根据昵称等字段做模糊匹配以尝试填充用户ID。
   - 支持对列名进行宽松匹配（例如昵称列会尝试匹配 `昵称`/`昵称名称`/`nick` 等变体；真实姓名匹配 `真实姓名`/`真实名称`/`姓名`；学校匹配 `学校`/`院校`/`单位` 等）。
- 生成一个精简的输出表，包含列：`用户ID`、`昵称`、`真实姓名`、`学校`（以 `output_file` 为名保存为 Excel，并同时导出为 UTF-8 带 BOM 的 CSV）。
- 输出去重后的 `user_ids.txt`（每行一个用户ID）以供 `get_user_avatar.py` 下载头像使用；同时会生成 `not_found_users.txt` 列出未匹配到 ID 的昵称以便人工核查。

### 🖼️ `get_user_avatar.py`
- 从用户ID清单文件读取所有用户ID
- 访问牛客用户个人主页
- 自动解析并下载用户头像
- 保存为 `avatars/<用户ID>/photo.png`

### 🏷️ `rename_logos.py`
- 批量重命名/转换图片文件
- 按图片尺寸重命名为 `logo<宽>x<高>.png`
- 支持递归处理、预览模式、删除原文件等选项

---

## 安装依赖

确保已安装 Python 3.7+，然后运行：

```powershell
python -m pip install -r requirements.txt
```

依赖包括：
- `pandas` - Excel/CSV 数据处理
- `openpyxl` / `xlrd` - Excel 文件读写
- `beautifulsoup4` - HTML 解析
- `requests` - HTTP 请求
- `Pillow` - 图片处理

---

## 目录结构

```
Crawler2.0/
├── Input/              # 输入文件目录
│   ├── rank_page_1.html
│   ├── rank_page_2.html
│   ├── rank_page_3.html
│   └── input.xls
├── Output/             # 输出文件目录
│   ├── output.xlsx
│   ├── output.csv
│   ├── user_ids.txt
│   ├── not_found_users.txt
│   └── avatars/
│       └── <用户ID>/
│           └── photo.png
├── config.json
├── get_user_id.py
├── get_user_avatar.py
├── rename_logos.py
└── README.md
```

**目录说明：**
- `Input/` - 存放所有输入文件（HTML 文件和 Excel 文件）
- `Output/` - 存放所有输出文件（生成的 Excel、CSV、用户ID清单、头像等）

---

## 配置文件

首次运行 `get_user_id.py` 时，如果不存在 `config.json`，会自动创建配置模板。

### `config.json` 示例

```json
{
   "local": {
      "html_files": [
         "rank_page_1.html",
         "rank_page_2.html",
         "rank_page_3.html"
      ],
      "problem_count": 13
   },
   "files": {
      "input_file": "input.xls",
      "output_file": "output.xlsx",
      "user_id_list": "user_ids.txt",
      "not_found_users": "not_found_users.txt",
      "avatar_dir": "avatars"
   }
}
```

> **运行时行为**：如果 `config.json` 不存在，`get_user_id.py` 会自动创建一个配置模板文件并退出（脚本会提示已创建配置文件，请编辑后重新运行）。请在首次运行前检查并修改 `config.json` 中的文件名设置。

### 配置项说明

| 配置项 | 说明 |
|--------|------|
| `html_files` | 排行榜 HTML 文件名列表（保存在 `Input/` 目录中） |
| `problem_count` | 竞赛题目数量 |
| `input_file` | 输入的 Excel 文件名（位于 `Input/` 目录） |
| `output_file` | 输出的 Excel 文件名（保存到 `Output/` 目录） |
| `user_id_list` | 用户ID清单文件名（保存到 `Output/` 目录） |
| `not_found_users` | 未找到用户清单文件名（保存到 `Output/` 目录） |
| `avatar_dir` | 头像保存目录名（相对于 `Output/` 目录） |

> **注意**：配置文件中只需填写文件名，无需包含 `Input/` 或 `Output/` 前缀。程序会自动将输入文件从 `Input/` 目录读取，输出文件保存到 `Output/` 目录。

---

## 使用方法

### 1. 解析用户ID并生成清单

#### 步骤 1：保存排行榜页面

1. 在浏览器中打开牛客竞赛排行榜页面
2. 右键 → "另存为" → 保存为完整网页（HTML）
3. 将 HTML 文件命名为 `rank_page_1.html`、`rank_page_2.html` 等
4. 放置在 `Input/` 目录中

#### 步骤 2：准备输入 Excel

1. 登录牛客（NowCoder）并进入对应比赛的管理页面，导出排名名单（需要比赛管理员权限）。
2. 导出 Excel 文件，保存到本仓库的 `Input/` 目录下，建议命名为 `input.xls` 或类似清晰名称。

注意：本项目目前只能处理特定导出格式的牛客榜单。要求导出的 Excel 必须包含报名时收集的完整用户信息。当前支持的列（按顺序或按列名匹配）至少应包含：

- 排名
- 团队
- 昵称
- 真实名称
- 学历
- 邮箱
- 手机号码
- 学校
- 毕业年份
- 学号
- 专业班级
- 性别
- 备注
- 通过题数
- 罚时
- 题目列（例如：A、A-相似度、B、B-相似度 ...）

也即，导出的表头应类似：

排名	团队	昵称	真实名称	学历	邮箱	手机号码	学校	毕业年份	学号	专业班级	性别	备注	通过题数	罚时	A	A-相似度	B	B-相似度......

这是因为脚本依赖这些字段来在导出的榜单与保存的排行榜 HTML 页面之间做严格匹配并提取用户 id。如果报名时没有收集这些信息，导出的榜单将不符合本项目目前的解析规则，导致匹配失败或丢失 id。

如果你的导出格式与上述不一致，请手动调整 Excel 表头使其匹配，或联系项目维护者以添加对新格式的支持。

将 Excel 文件放置在 `Input/` 目录中。

#### 步骤 3：运行脚本

```powershell
python get_user_id.py
```

#### 输出文件（位于 `Output/` 目录）

- `output.xlsx` - 包含完整用户信息的 Excel 文件
- `output.csv` - CSV 格式（UTF-8 with BOM 编码）
- `user_ids.txt` - 用户ID清单（每行一个ID，去重）
- `not_found_users.txt` - 未找到ID的用户列表

说明与细节：
- 脚本会尝试使用多种 Excel 解析引擎读取文件（以提高兼容性），如果读取失败会抛出相应错误并提示。
- 输出的 `output.xlsx` / `output.csv` 为脚本生成的精简表，包含列：`用户ID`、`昵称`、`真实姓名`、`学校`。
- `user_ids.txt` 为去重后的用户ID列表（按出现顺序去重），适合作为 `get_user_avatar.py` 的输入。
- 未匹配到 ID 的昵称会被写入 `not_found_users.txt`，建议人工核对这些昵称与 HTML 页面或报名信息进行比对后补全。

---

### 2. 下载用户头像

确保已运行 `get_user_id.py` 并在 `Output/` 目录中生成了 `user_ids.txt`。

```powershell
python get_user_avatar.py
```

#### 工作流程

1. 读取 `Output/user_ids.txt` 中的所有用户ID
2. 逐个访问 `https://ac.nowcoder.com/acm/contest/profile/<用户ID>`
3. 解析页面中的头像图片链接
4. 下载并保存为 `Output/avatars/<用户ID>/photo.png`（或 .jpg 等）

#### 注意事项

- 脚本会在每个请求之间等待 0.5 秒，避免请求过于频繁
- 如果某些用户页面需要登录才能访问，可能需要手动添加 Cookie
- 下载失败的用户会在控制台显示错误信息

#### 示例输出

```
[1/50] 处理用户 123456789 ...
  已保存头像: Output\avatars\123456789\photo.png
[2/50] 处理用户 987654321 ...
  未找到头像链接
...
```

---

### 3. 批量重命名图片

`rename_logos.py` 可以批量处理图片，按尺寸重命名为统一格式。

#### 基本用法

```powershell
# 查看将要执行的操作（不实际修改文件）
python rename_logos.py <目标目录> --dry-run

# 处理指定目录中的所有图片
python rename_logos.py <目标目录>

# 递归处理子目录
python rename_logos.py <目标目录> --recursive

# 转换后删除原文件
python rename_logos.py <目标目录> --delete-original

# 显示详细处理信息
python rename_logos.py <目标目录> --verbose
```

#### 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `target` | - | 目标目录（必需） |
| `--recursive` | `-r` | 递归处理子目录 |
| `--ext` | `-e` | 指定文件扩展名（逗号分隔，默认：png,jpg,jpeg,gif,bmp,webp） |
| `--dry-run` | `-n` | 预览模式，仅打印操作不实际修改 |
| `--delete-original` | `-d` | 转换后删除原始文件 |
| `--verbose` | `-v` | 显示详细处理信息 |

#### 示例

```powershell
# 处理 Output/avatars 目录下的所有图片，递归子目录，删除原文件
python rename_logos.py Output/avatars -r -d -v

# 仅处理 Output 目录的 PNG 和 JPG
python rename_logos.py Output -e png,jpg

# 预览将要做的修改
python rename_logos.py Output/avatars --dry-run
```

#### 输出示例

- 原文件：`Output/avatars/123456/photo.jpg` (800×600)
- 新文件：`Output/avatars/123456/logo800x600.png`

如果目标文件名已存在，会自动添加序号：
- `logo800x600.png` → `logo800x600_1.png` → `logo800x600_2.png` ...

---

## 📝 工作流程总览

```
1. 保存排行榜 HTML 页面
   ↓
2. 准备输入 Excel 文件
   ↓
3. 运行 get_user_id.py
   ├─ 输出: output.xlsx / output.csv
   └─ 输出: user_ids.txt
   ↓
4. 运行 get_user_avator.py
   └─ 输出: avatars/<用户ID>/photo.png
   ↓
5. (可选) 运行 rename_logos.py
   └─ 输出: avatars/<用户ID>/logo<宽>x<高>.png
```