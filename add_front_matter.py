import os
import re
import subprocess
import sys
from pathlib import Path

# --- 配置 ---
# Hugo 内容目录下的 posts 文件夹
POSTS_DIR = "content/posts"
# ----------------

def has_front_matter(file_path: Path) -> bool:
    """检查文件是否已经包含 Front Matter (以 '---' 或 '+++' 开头)。"""
    try:
        with file_path.open('r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            return first_line in ('---', '+++')
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"    [警告] 无法读取文件 {file_path}: {e}")
        return True

def clean_title_in_front_matter(front_matter_content: str) -> str:
    """在 front matter 内容中查找 title 字段并移除末尾的 ' Tmp'。"""
    cleaned_lines = []
    # 正则表达式匹配 title = "Some Title Tmp" 或 title = 'Some Title Tmp'
    # 它会捕获 'title = "' 部分, 'Some Title' 部分, 以及结尾的引号
    # (title\s*=\s*['"])   => 捕获组1: title = ' or title = "
    # (.*?)                => 捕获组2: 标题文字
    # \s+[Tt]mp            => 匹配一个或多个空格，后跟 Tmp 或 tmp
    # (['"])               => 捕获组3: 结尾的引号
    title_pattern = re.compile(r"(title\s*=\s*['\"])(.*?)\s+[Tt]mp(['\"])")

    for line in front_matter_content.splitlines():
        # 使用 sub 进行替换，如果匹配成功，则用捕获组1,2,3重组字符串
        cleaned_line, num_replacements = title_pattern.subn(r'\1\2\3', line)
        if num_replacements > 0:
            print(f"    [清理] 已修正标题: {cleaned_line.strip()}")
        cleaned_lines.append(cleaned_line)
    
    return "\n".join(cleaned_lines)

def process_file(md_file: Path, posts_dir_path: Path):
    """处理单个 markdown 文件：为其添加 front matter。"""
    print(f"-> 正在处理: {md_file}")

    if has_front_matter(md_file):
        print("    [跳过] 文件已存在 Front Matter。")
        return

    relative_path = md_file.relative_to(posts_dir_path)
    tmp_relative_path = relative_path.with_stem(f"{relative_path.stem}-tmp")
    hugo_new_path = f"posts/{tmp_relative_path.as_posix()}"
    tmp_file_path = posts_dir_path / tmp_relative_path
    
    if tmp_file_path.exists():
        tmp_file_path.unlink()

    try:
        print(f"    [执行] hugo new {hugo_new_path}")
        command = ['hugo', 'new', hugo_new_path]
        subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
    except FileNotFoundError:
        print("\n[错误] 'hugo' 命令未找到。", file=sys.stderr)
        print("请确保 Hugo 已安装并在系统的 PATH 环境变量中。", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"    [错误] Hugo 命令执行失败，文件: {md_file}", file=sys.stderr)
        print(f"    [错误详情] {e.stderr.strip()}", file=sys.stderr)
        return
    except Exception as e:
        print(f"    [未知错误] 在执行 Hugo 命令时发生错误: {e}", file=sys.stderr)
        return

    try:
        if not tmp_file_path.exists():
             print(f"    [错误] Hugo 没有成功创建临时文件: {tmp_file_path}", file=sys.stderr)
             return
             
        tmp_content = tmp_file_path.read_text(encoding='utf-8')
        
        # 自动检测分隔符
        first_line = tmp_content.splitlines()[0].strip()
        if first_line not in ('---', '+++'):
            print(f"    [错误] 临时文件 {tmp_file_path} 未包含有效的 Front Matter 分隔符。", file=sys.stderr)
            return
        delimiter = first_line

        # 提取 front matter 内容（在两个分隔符之间的部分）
        parts = tmp_content.split(delimiter, 2)
        if len(parts) < 3:
            print(f"    [错误] 无法从 {tmp_file_path} 提取 Front Matter。", file=sys.stderr)
            return
        
        raw_front_matter = parts[1]

        # 清理标题
        cleaned_front_matter_content = clean_title_in_front_matter(raw_front_matter)

        # 重新构建完整的 front matter
        final_front_matter = f"{delimiter}{cleaned_front_matter_content.strip()}\n{delimiter}\n\n"
        
        # 读取原始文件内容并合并
        original_content = md_file.read_text(encoding='utf-8')
        new_content = final_front_matter + original_content
        md_file.write_text(new_content, encoding='utf-8')
        print(f"    [成功] 已为 {md_file} 添加修正后的 Front Matter。")

    except IOError as e:
        print(f"    [错误] 文件读写失败: {e}", file=sys.stderr)
    except Exception as e:
        print(f"    [错误] 处理文件时发生未知错误: {e}", file=sys.stderr)
    finally:
        if tmp_file_path.exists():
            try:
                tmp_file_path.unlink()
                print(f"    [清理] 已删除临时文件: {tmp_file_path}")
            except OSError as e:
                print(f"    [错误] 无法删除临时文件: {e}", file=sys.stderr)


def main():
    """主函数，执行脚本逻辑。"""
    posts_dir_path = Path(POSTS_DIR)

    if not posts_dir_path.is_dir():
        print(f"[错误] 目录不存在: '{POSTS_DIR}'", file=sys.stderr)
        print("请确保你在 Hugo 站点的根目录下运行此脚本。", file=sys.stderr)
        sys.exit(1)
    
    print(f"[*] 开始递归扫描目录: {posts_dir_path}")
    
    md_files = list(posts_dir_path.rglob("*.md"))
    
    if not md_files:
        print("[*] 没有找到任何 Markdown 文件。")
        return

    print(f"[*] 共找到 {len(md_files)} 个 Markdown 文件。开始处理...")
    print("-" * 40)

    for md_file in md_files:
        if md_file.stem.endswith('-tmp'):
            continue
        process_file(md_file, posts_dir_path)
        print("-" * 40)

    print("[*] 所有文件处理完毕。")


if __name__ == "__main__":
    main()