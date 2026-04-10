# 网站部署

日报生成后，可自动部署到网站。

## 快速开始

```bash
cp -r references/website-template <workspace>/website
cd <workspace>/website
python3 build.py
```

## 目录结构

```
<workspace>/
├── output/              # 日报 Markdown 输出
└── website/
    ├── build.py         # 构建脚本（终端风格，零依赖纯 Python）
    ├── dist/            # 生成的静态网站
    └── README.md        # 部署指南
```

## 首次创建

```bash
cp -r references/website-template <workspace>/website
cd <workspace>/website && python3 build.py
git init && git add -A && git commit -m "Initial commit"
gh repo create daily-news-web --public --source=. --push
```

Cloudflare Pages 配置：Build command `python3 build.py`，Output `dist`。

## 日报生成后更新

检查 `<workspace>/website` 是否存在，询问用户：

- **存在**：立即构建推送 / 仅构建 / 跳过
- **不存在**：是否创建网站

立即构建推送：
```bash
cd <workspace>/website
python3 build.py
git add -A && git commit -m "Add daily report for $(date +%Y-%m-%d)"
git push origin main
```

详细配置见 `<workspace>/website/README.md`。
