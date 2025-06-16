import json
import os
import sys
import re
import argparse
import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.prompts import (
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
  HumanMessagePromptTemplate,
)
import dotenv

# 添加ai目录到系统路径
sys.path.append('ai')
from structure import Structure

# 加载.env文件
if os.path.exists('.env'):
    dotenv.load_dotenv()

def parse_arxiv_url(url):
    """解析arXiv URL，获取论文ID"""
    # 从URL中提取论文ID
    pattern = r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        raise ValueError("无效的arXiv URL格式")

def get_paper_info(paper_id):
    """从arXiv获取论文信息"""
    print(f"正在从arXiv获取论文ID为 {paper_id} 的信息...")
    
    # 构建arXiv API URL
    api_url = f"https://export.arxiv.org/api/query?id_list={paper_id}"
    
    # 发送请求
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"获取论文信息失败，状态码: {response.status_code}")
    
    # 使用BeautifulSoup解析XML响应
    soup = BeautifulSoup(response.text, 'xml')
    
    # 提取信息
    title = soup.find('title').text.strip()
    summary = soup.find('summary').text.strip()
    
    # 提取作者
    authors = []
    author_tags = soup.find_all('author')
    for author_tag in author_tags:
        name_tag = author_tag.find('name')
        if name_tag:
            authors.append(name_tag.text.strip())
    
    # 提取分类
    categories = []
    category_tags = soup.find('arxiv:primary_category')
    if category_tags:
        main_category = category_tags.get('term')
        categories.append(main_category)
    
    # 创建paper信息
    paper_info = {
        "id": paper_id,
        "title": title,
        "authors": authors,
        "summary": summary,
        "abs": f"https://arxiv.org/abs/{paper_id}",
        "categories": categories
    }
    
    return paper_info

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="从arXiv URL获取论文并用AI增强")
    parser.add_argument("url", type=str, help="arXiv论文URL (格式: https://arxiv.org/abs/XXXX.XXXXX)")
    parser.add_argument("--api_key", "-k", type=str, help="API密钥 (OpenAI 或 DeepSeek)")
    parser.add_argument("--model", "-m", type=str, default="gpt-3.5-turbo", 
                        help="使用的模型名称 (默认: gpt-3.5-turbo)")
    parser.add_argument("--base_url", "-b", type=str, 
                        help="API基础URL (OpenAI: https://api.openai.com 或 DeepSeek: https://api.deepseek.com)")
    parser.add_argument("--api_type", "-t", type=str, choices=["openai", "deepseek"], default="openai",
                        help="API类型 (默认: openai)")
    return parser.parse_args()

def main():
    # 解析命令行参数
    args = parse_args()
    
    # 根据API类型设置环境变量和API参数
    if args.api_type == "openai" or (not args.api_type and not args.base_url):
        # 使用OpenAI API
        api_key_env = "OPENAI_API_KEY"
        base_url = args.base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    elif args.api_type == "deepseek" or (args.base_url and "deepseek" in args.base_url):
        # 使用DeepSeek API
        api_key_env = "DEEPSEEK_API_KEY"
        base_url = args.base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    else:
        api_key_env = "OPENAI_API_KEY"
        base_url = args.base_url or "https://api.openai.com/v1"
    
    # 如果提供了API密钥参数，则设置环境变量
    if args.api_key:
        os.environ[api_key_env] = args.api_key
    
    # 检查API密钥是否已设置
    api_key = os.environ.get(api_key_env)
    if not api_key:
        print(f"❌ 错误: 未设置{api_key_env}，请通过以下方式之一设置:")
        print(f"1. 使用--api_key参数: python test_translation.py --api_key=YOUR_API_KEY --api_type={args.api_type} URL")
        print(f"2. 设置环境变量: export {api_key_env}=YOUR_API_KEY")
        print(f"3. 在.env文件中添加: {api_key_env}=YOUR_API_KEY")
        return
    
    try:
        # 解析URL获取论文ID
        paper_id = parse_arxiv_url(args.url)
        
        # 获取论文信息
        paper_data = get_paper_info(paper_id)
        
        # 保存原始数据
        with open(f'paper_{paper_id}.jsonl', 'w') as f:
            json.dump(paper_data, f)
            f.write('\n')
        
        print(f"已保存原始论文数据到 paper_{paper_id}.jsonl")
        
        # 读取提示模板
        template = open("ai/template.txt", "r").read()
        system = open("ai/system.txt", "r").read()
        
        # 设置语言模型
        model_name = args.model or os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
        if args.api_type == "deepseek" and not "deepseek" in model_name:
            model_name = "deepseek-chat"  # 默认DeepSeek模型
            
        language = os.environ.get("LANGUAGE", 'Chinese')
        
        print(f"使用模型: {model_name}")
        print(f"使用API端点: {base_url}")
        print(f"使用语言: {language}")
        
        # 初始化LLM
        llm = ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            base_url=base_url
        ).with_structured_output(Structure, method="function_calling")
        
        # 创建提示模板
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system),
            HumanMessagePromptTemplate.from_template(template=template)
        ])
        
        # 创建链
        chain = prompt_template | llm
        
        # 处理论文数据
        try:
            print("开始处理论文数据...")
            response = chain.invoke({
                "language": language,
                "content": paper_data['summary'],
                "title": paper_data['title']
            })
            paper_data['AI'] = response.model_dump()
            print("\n✅ AI处理成功！")
            
            # 打印翻译结果
            print("\n==== 翻译结果 ====")
            print(f"原始标题: {paper_data['title']}")
            print(f"中文标题: {paper_data['AI']['paper_title_zh']}")
            print("\n原始摘要: \n{0}".format(paper_data['summary']))
            print("\n中文摘要: \n{0}".format(paper_data['AI']['abstract_zh']))
            
            # 保存增强后的结果
            with open(f'paper_{paper_id}_AI_enhanced.jsonl', 'w') as f:
                json.dump(paper_data, f, ensure_ascii=False)
            
            print(f"\n已将结果保存到 paper_{paper_id}_AI_enhanced.jsonl")
            
            # 创建markdown输出
            from itertools import count
            
            # 读取markdown模板
            with open('to_md/paper_template.md', 'r') as f:
                template = f.read()
            
            idx = count(1)
            markdown = template.format(
                title=paper_data["title"],
                authors=",".join(paper_data["authors"]),
                url=paper_data['abs'],
                tldr=paper_data['AI']['tldr'],
                motivation=paper_data['AI']['motivation'],
                method=paper_data['AI']['method'],
                result=paper_data['AI']['result'],
                conclusion=paper_data['AI']['conclusion'],
                paper_title_zh=paper_data['AI'].get('paper_title_zh', '翻译失败'),
                abstract_zh=paper_data['AI'].get('abstract_zh', '翻译失败'),
                cate=paper_data['categories'][0] if paper_data['categories'] else 'N/A',
                idx=next(idx)
            )
            
            # 保存markdown结果
            output_file = f'paper_{paper_id}_output.md'
            with open(output_file, 'w') as f:
                f.write(markdown)
            
            print(f"已将Markdown输出保存到 {output_file}")
            
        except Exception as e:
            print(f"❌ 处理过程中出现错误: {e}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main() 