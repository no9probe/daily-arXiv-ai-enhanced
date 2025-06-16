# 论文 URL 解析与 AI 增强工具

这个工具可以从arXiv论文URL中获取论文信息，并使用AI模型进行翻译和分析。

## 功能

1. 从arXiv URL解析论文信息（标题、作者、摘要等）
2. 使用AI模型进行内容分析和翻译
3. 生成中文标题和摘要
4. 生成Markdown格式的论文总结

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python test_translation.py https://arxiv.org/abs/XXXX.XXXXX
```

其中 `XXXX.XXXXX` 是arXiv论文ID，例如 `2304.03442`。

## 环境变量

可以通过环境变量配置以下参数：

- `MODEL_NAME`: 使用的语言模型名称，默认为 'deepseek-chat'
- `LANGUAGE`: 输出语言，默认为 '中文'

设置环境变量的方法：

```bash
export MODEL_NAME=gpt-4
export LANGUAGE=Chinese
python test_translation.py https://arxiv.org/abs/XXXX.XXXXX
```

也可以创建 `.env` 文件：

```
MODEL_NAME=gpt-4
LANGUAGE=Chinese
```

## 输出文件

程序会生成以下文件：

1. `paper_{论文ID}.jsonl`: 原始论文数据
2. `paper_{论文ID}_AI_enhanced.jsonl`: AI增强后的论文数据
3. `paper_{论文ID}_output.md`: Markdown格式的论文总结 