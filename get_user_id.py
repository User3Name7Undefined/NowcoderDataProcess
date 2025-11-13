import pandas as pd
import json
import os
import re
from bs4 import BeautifulSoup

class NowCoderLocalParser:
    def __init__(self, config_file='config.json'):
        # 读取JSON配置
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.create_config_template()
            print(f"已创建配置文件模板: {config_file}")
            print("请编辑该文件并重新运行程序")
            exit(1)
        
        # 从配置读取设置
        local_config = self.config.get('local', {})
        files_config = self.config.get('files', {})
        
        # HTML文件路径（添加Input/前缀）
        html_files_raw = local_config.get('html_files', [])
        self.html_files = [f'Input/{f}' if not f.startswith('Input/') else f 
                  for f in html_files_raw]
        
        # 输入文件（添加Input/前缀）
        input_file_raw = files_config.get('input_file')
        self.input_file = f'Input/{input_file_raw}' if input_file_raw and not input_file_raw.startswith('Input/') else input_file_raw
        
        # 输出文件（添加Output/前缀）
        output_file_raw = files_config.get('output_file')
        self.output_file = f'Output/{output_file_raw}' if output_file_raw and not output_file_raw.startswith('Output/') else output_file_raw
        
        # 用户ID清单文件（添加Output/前缀）
        user_id_list_raw = files_config.get('user_id_list')
        self.user_id_list_file = f'Output/{user_id_list_raw}' if user_id_list_raw and not user_id_list_raw.startswith('Output/') else user_id_list_raw
        
        # 未找到用户的清单文件（添加Output/前缀）
        not_found_raw = files_config.get('not_found_users')
        self.not_found_file = f'Output/{not_found_raw}' if not_found_raw and not not_found_raw.startswith('Output/') else not_found_raw
        
        # 头像目录（添加Output/前缀）
        avatar_dir_raw = files_config.get('avatar_dir')
        self.avatar_dir = f'Output/{avatar_dir_raw}' if avatar_dir_raw and not avatar_dir_raw.startswith('Output/') else avatar_dir_raw
        
        # 确保输出目录存在
        if not os.path.exists('Output'):
            os.makedirs('Output', exist_ok=True)
        
        # 存储用户昵称到ID的映射
        self.user_mapping = {}
        
    def parse_html_files(self):
        """解析HTML文件，提取用户昵称和ID的映射"""
        print("开始解析HTML文件...")
        
        if not self.html_files:
            print("错误: 未配置HTML文件路径")
            return False
            
        for html_file in self.html_files:
            if not os.path.exists(html_file):
                print(f"警告: HTML文件不存在: {html_file}")
                continue
                
            try:
                print(f"\n正在解析文件: {html_file}")
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 解析用户链接
                user_mappings_from_file = self.parse_user_links(soup, html_file)
                
                # 更新全局映射表
                self.user_mapping.update(user_mappings_from_file)
                
                print(f"从文件 {html_file} 中解析出 {len(user_mappings_from_file)} 个用户ID")
                
            except Exception as e:
                print(f"解析HTML文件 {html_file} 时出错: {e}")
        
        print(f"\n总共解析出 {len(self.user_mapping)} 个用户ID")
        
        return True
    
    def parse_user_links(self, soup, filename):
        """在整个文档中搜索用户链接"""
        user_mappings = {}
        
        # 查找所有用户链接
        user_links = soup.find_all('a', href=re.compile(r'/acm/contest/profile/\d+'))
        print(f"在文件 {filename} 中找到 {len(user_links)} 个用户链接")
        
        for link in user_links:
            # 尝试多种方式提取用户昵称
            nickname = self.extract_nickname(link)
            
            # 从链接中提取用户ID
            user_id_match = re.search(r'/acm/contest/profile/(\d+)', link.get('href', ''))
            
            if user_id_match and nickname:
                user_id = user_id_match.group(1)
                user_mappings[nickname] = user_id
                print(f"  找到用户 {nickname} -> ID: {user_id}")
        
        return user_mappings
    
    def extract_nickname(self, link):
        """从链接元素中提取用户昵称"""
        # 方法1: 从链接文本中提取
        nickname = link.get_text(strip=True)
        if nickname:
            return nickname
        
        # 方法2: 从title属性中提取
        nickname = link.get('title', '')
        if nickname:
            return nickname
        
        # 方法3: 从子元素中提取
        for child in link.children:
            if hasattr(child, 'get_text'):
                nickname = child.get_text(strip=True)
                if nickname:
                    return nickname
        
        return ''
    
    def process_excel(self):
        """处理Excel文件"""
        print(f"\n开始处理Excel文件: {self.input_file}")
        try:
            # 读取原文件（尽量兼容不同引擎）
            try:
                df_old = pd.read_excel(self.input_file)
            except Exception:
                try:
                    df_old = pd.read_excel(self.input_file, engine='xlrd')
                except Exception:
                    df_old = pd.read_excel(self.input_file, engine='openpyxl')

            print(f"成功读取Excel文件，共 {len(df_old)} 行数据")

            # 查找列名（宽松匹配）
            cols = list(df_old.columns)

            def find_col(keywords):
                for col in cols:
                    name = str(col)
                    for kw in keywords:
                        if kw in name:
                            return col
                return None

            nickname_col = find_col(['昵称', '昵称名称']) or find_col(['nick', 'Nick'])
            realname_col = find_col(['真实姓名', '真实名称', '姓名'])
            school_col = find_col(['学校', '院校', '单位'])

            if not nickname_col:
                print('错误：未能在表头中找到包含“昵称”的列，请检查输入文件。')
                return

            # 构建新的精简表格： 用户ID, 昵称, 真实姓名, 学校
            nick_series = df_old[nickname_col].astype(str).fillna('').tolist()
            user_ids = []
            not_found = []

            for nick in nick_series:
                nick_key = nick.strip()
                uid = self.user_mapping.get(nick_key, '')
                # 尝试去掉空白或不可见字符后再匹配
                if not uid:
                    uid = self.user_mapping.get(re.sub(r"\s+", '', nick_key), '')
                user_ids.append(uid)
                if not uid:
                    not_found.append(nick_key)

            print(f"成功匹配 {len([u for u in user_ids if u])}/{len(user_ids)} 个用户ID")

            # 真实姓名和学校列（如果未找到则填空）
            real_series = df_old[realname_col].astype(str).fillna('') if realname_col in df_old.columns else [''] * len(df_old)
            school_series = df_old[school_col].astype(str).fillna('') if school_col in df_old.columns else [''] * len(df_old)

            df_new = pd.DataFrame({
                '用户ID': user_ids,
                '昵称': nick_series,
                '真实姓名': list(real_series) if hasattr(real_series, '__iter__') else [''] * len(user_ids),
                '学校': list(school_series) if hasattr(school_series, '__iter__') else [''] * len(user_ids)
            })

            # 确保输出目录存在
            out_dir = os.path.dirname(self.output_file) if self.output_file else ''
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)

            # 仅保存为 CSV（UTF-8 带 BOM）
            # 如果配置的 output_file 不是以 .csv 结尾，则替换扩展名为 .csv
            if self.output_file and self.output_file.lower().endswith('.csv'):
                csv_file = self.output_file
            else:
                # 若未配置或配置为其他扩展名，则将其扩展名替换为 .csv 或添加 .csv
                if self.output_file:
                    base = os.path.splitext(self.output_file)[0]
                    csv_file = f"{base}.csv"
                else:
                    csv_file = 'Output/output.csv'

            try:
                df_new.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"CSV文件已保存为: {csv_file}")
            except Exception as e:
                print(f"保存CSV失败: {e}")

            # 打印预览
            print('\n前几行数据预览:')
            print(df_new.head().to_string())

            # 保存未找到的用户列表
            if not_found:
                print(f"\n未找到以下用户的ID: {', '.join(not_found[:10])}{'...' if len(not_found) > 10 else ''}")
                if self.not_found_file:
                    try:
                        nd_dir = os.path.dirname(self.not_found_file)
                        if nd_dir:
                            os.makedirs(nd_dir, exist_ok=True)
                        with open(self.not_found_file, 'w', encoding='utf-8') as f:
                            for user in not_found:
                                f.write(f"{user}\n")
                        print(f"未找到的用户列表已保存到 {self.not_found_file} (共{len(not_found)}个)")
                    except Exception as e:
                        print(f"保存未找到用户列表失败: {e}")

            # 保存用户ID清单（去重）
            try:
                unique_ids = [uid for uid in dict.fromkeys([u for u in user_ids if u])]
                if unique_ids and self.user_id_list_file:
                    uid_dir = os.path.dirname(self.user_id_list_file)
                    if uid_dir:
                        os.makedirs(uid_dir, exist_ok=True)
                    with open(self.user_id_list_file, 'w', encoding='utf-8') as f:
                        for uid in unique_ids:
                            f.write(f"{uid}\n")
                    print(f"用户ID清单已保存为: {self.user_id_list_file} (共{len(unique_ids)}个)")
                else:
                    print("未找到任何用户ID或未配置清单文件，不创建清单文件。")
            except Exception as e:
                print(f"保存用户ID清单时出错: {e}")

        except Exception as e:
            import traceback
            print(f"处理Excel文件时出错: {e}")
            print("详细错误信息:")
            traceback.print_exc()
    
    def create_config_template(self):
        """创建配置文件模板"""
        config_template = {
            "local": {
                "html_files": [
                    "rank_page_1.html",
                    "rank_page_2.html",
                    "rank_page_3.html"
                ]
            },
            "files": {
                "input_file": "input.xls",
                "output_file": "output.csv",
                "user_id_list": "user_ids.txt",
                "not_found_users": "not_found_users.txt",
                "avatar_dir": "avatars"
            }
        }
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config_template, f, indent=4, ensure_ascii=False)
    
    def run(self):
        """运行本地解析器"""
        print(f"检查输入文件: {self.input_file}")
        print(f"文件是否存在: {os.path.exists(self.input_file)}")
        
        if not os.path.exists(self.input_file):
            print(f"输入文件不存在: {self.input_file}")
            return
        
        # 解析HTML文件
        if not self.parse_html_files():
            print("HTML文件解析失败")
            return
            
        print("HTML文件解析成功，开始处理Excel...")
        # 处理Excel文件
        self.process_excel()

def main():
    parser = NowCoderLocalParser()
    parser.run()

if __name__ == '__main__':
    main()