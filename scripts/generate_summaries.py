import os
import frontmatter
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import shutil

# --- 配置 ---

# 博客文章所在的根目录
POSTS_DIRECTORY = "./content/posts"

# 用于生成摘要的 LLM 模型
LLM_MODEL = "qwen-plus-latest"

# 给 LLM 的指令 (Prompt)
PROMPT_TEMPLATE = """
你是一个专业的SEO内容优化师。请为以下博客文章生成更适合搜索引擎排名的摘要。

文章内容：
---
{content}
---

请根据以下要求优化：

**摘要要求：**
1. 长度控制在60-80个汉字
2. 包含文章的核心关键词
3. 准确概括文章价值和亮点
4. 使用第三人称描述
5. 适合作为搜索结果的描述片段
6. 结构清晰，易于理解

请直接生成摘要，不要包含任何额外的解释或前缀。
"""

# --- 脚本主体 ---


def generate_summary_with_llm(content: str) -> str:
    """
    使用 ALYUN BAILIAN 为给定内容生成摘要。

    Args:
        content: 博客文章的正文内容。

    Returns:
        由 LLM 生成的摘要文本。
    """
    try:
        client = OpenAI(
            # 替换为 ALYUN BAILIAN 的 API 基础 URL
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.environ.get("QWEN_API_KEY"))

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的SEO内容优化师。请严格按照要求返回结果。"},
                {"role": "user", "content": PROMPT_TEMPLATE.format(
                    content=content)},
            ],
            temperature=0.7,
            max_tokens=16384,  # 限制最大 token 数，以控制成本和长度
        )
        content_value = response.choices[0].message.content or ""
        summary = content_value.strip()
        return summary
    except Exception as e:
        print(f"    ❌ 调用 API 时出错: {e}")
        return ""


def process_markdown_file(filepath: Path):
    """
    处理单个 Markdown 文件：读取、检查摘要、生成摘要并写回。

    Args:
        filepath: 指向 Markdown 文件的 Path 对象。
    """
    print(f"📄 正在处理: {filepath}")

    backup_path = filepath.with_suffix(filepath.suffix + ".bak")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # 检查是否已有摘要
        summary_val = post.get('summary')
        if summary_val and str(summary_val).strip():
            print("    ✅ 摘要已存在，跳过。")
            return

        # 如果没有内容，也跳过
        if not post.content.strip():
            print("    ⚠️ 文章内容为空，跳过。")
            return

        print("    ✨ 摘要不存在，准备生成...")

        # 调用 LLM 生成摘要
        new_summary = generate_summary_with_llm(post.content)

        if new_summary:
            # 将新摘要添加到 frontmatter 中
            post['summary'] = new_summary
            # 写入前先备份原文件
            shutil.copy2(filepath, backup_path)
            try:
                # 用 frontmatter.dumps 生成字符串再写入，防止 bytes 问题
                new_content = frontmatter.dumps(post)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"    ✅ 成功生成并写入摘要！")
                # 写入成功后删除备份
                if backup_path.exists():
                    backup_path.unlink()
            except Exception as write_err:
                print(f"    ❌ 写入文件时发生错误: {write_err}，正在恢复原文件...")
                # 写入失败恢复备份
                if backup_path.exists():
                    shutil.copy2(backup_path, filepath)
                print("    ⚠️ 已恢复原文件内容。")
        else:
            print("    ❌ 未能生成摘要，文件未被修改。")

    except Exception as e:
        print(f"    ❌ 处理文件时发生错误: {e}")


def main():
    """
    主函数，递归遍历目录并处理所有 Markdown 文件。
    """
    # 加载 .env 文件中的环境变量
    load_dotenv()

    if not os.environ.get("QWEN_API_KEY"):
        print("错误：QWEN_API_KEY 环境变量未设置。")
        print("请在项目根目录创建一个 .env 文件并添加您的 QWEN API 密钥。")
        return

    content_path = Path(POSTS_DIRECTORY)
    if not content_path.is_dir():
        print(f"错误：目录 '{POSTS_DIRECTORY}' 不存在。")
        return

    print(f"🚀 开始扫描目录 '{content_path}' 下的 Markdown 文件...")

    # 递归查找所有 .md 文件
    markdown_files = list(content_path.rglob("*.md"))

    if not markdown_files:
        print("未找到任何 Markdown 文件。")
        return

    for filepath in markdown_files:
        process_markdown_file(filepath)
        print("-" * 20)

    print("🎉 所有文件处理完毕！")


if __name__ == "__main__":
    main()
