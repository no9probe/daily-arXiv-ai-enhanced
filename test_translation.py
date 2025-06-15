import json
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import (
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
  HumanMessagePromptTemplate,
)
import sys

# 添加ai目录到系统路径
sys.path.append('ai')
from structure import Structure

# 创建测试数据
test_data = {
    "id": "test001",
    "title": "A Novel Method for Natural Language Processing",
    "authors": ["Test Author1", "Test Author2"],
    "summary": "This paper introduces a novel method for natural language processing that improves performance on benchmark tasks by 15%. We propose a new architecture that combines transformer models with memory networks and demonstrate its effectiveness on several datasets.",
    "abs": "https://arxiv.org/abs/test001",
    "categories": ["cs.CL"]
}

# 保存测试数据
with open('test_paper.jsonl', 'w') as f:
    json.dump(test_data, f)
    f.write('\n')

# 读取提示模板
template = open("ai/template.txt", "r").read()
system = open("ai/system.txt", "r").read()

# 设置语言模型
model_name = os.environ.get("MODEL_NAME", 'deepseek-chat')
language = os.environ.get("LANGUAGE", 'Chinese')

print(f"使用模型: {model_name}")
print(f"使用语言: {language}")

# 初始化LLM
llm = ChatOpenAI(model=model_name).with_structured_output(Structure, method="function_calling")

# 创建提示模板
prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system),
    HumanMessagePromptTemplate.from_template(template=template)
])

# 创建链
chain = prompt_template | llm

# 处理测试数据
try:
    print("开始处理测试数据...")
    response = chain.invoke({
        "language": language,
        "content": test_data['summary'],
        "title": test_data['title']
    })
    test_data['AI'] = response.model_dump()
    print("\n✅ AI处理成功！")
    
    # 打印翻译结果
    print("\n==== 翻译结果 ====")
    print(f"原始标题: {test_data['title']}")
    print(f"中文标题: {test_data['AI']['paper_title_zh']}")
    print("\n原始摘要: \n{0}".format(test_data['summary']))
    print("\n中文摘要: \n{0}".format(test_data['AI']['abstract_zh']))
    
    # 保存增强后的结果
    with open('test_paper_AI_enhanced.jsonl', 'w') as f:
        json.dump(test_data, f, ensure_ascii=False)
    
    print("\n已将结果保存到 test_paper_AI_enhanced.jsonl")
    
    # 创建测试markdown输出
    from itertools import count
    
    # 读取markdown模板
    with open('to_md/paper_template.md', 'r') as f:
        template = f.read()
    
    idx = count(1)
    markdown = template.format(
        title=test_data["title"],
        authors=",".join(test_data["authors"]),
        url=test_data['abs'],
        tldr=test_data['AI']['tldr'],
        motivation=test_data['AI']['motivation'],
        method=test_data['AI']['method'],
        result=test_data['AI']['result'],
        conclusion=test_data['AI']['conclusion'],
        paper_title_zh=test_data['AI'].get('paper_title_zh', '翻译失败'),
        abstract_zh=test_data['AI'].get('abstract_zh', '翻译失败'),
        cate=test_data['categories'][0],
        idx=next(idx)
    )
    
    # 保存markdown结果
    with open('test_paper_output.md', 'w') as f:
        f.write(markdown)
    
    print("已将Markdown输出保存到 test_paper_output.md")
    
except Exception as e:
    print(f"❌ 处理过程中出现错误: {e}") 