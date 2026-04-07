# Paul Graham Essays

Paul Graham 的博客文章，按主题分类整理为 Markdown 文件。

## 目录结构

```
topics/
├── startups/       # 创业与企业家精神
├── programming/    # 编程与技术
├── writing/        # 写作与表达
├── thinking/       # 思考与哲学
├── wealth/         # 财富与经济
├── education/      # 教育
├── yc/             # Y Combinator
└── life/           # 生活与文化
backlogs/           # 已爬取但未分类的文章
images/             # 文章中的图片
```

## 使用

需要 [uv](https://docs.astral.sh/uv/) 管理依赖。

```bash
# 安装依赖
uv sync

# 运行爬虫（增量更新，已有文章会跳过）
uv run python -m src.scraper
```

## 自动更新

通过 GitHub Actions 每周一自动运行爬虫，检查新文章并更新仓库。也可在 Actions 页面手动触发。

## 统计

- 共 231 篇文章
- 8 个主题分类
