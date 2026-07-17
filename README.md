# ysjc-scyx-zbgwxxmp

苏州市吴江区公共资源交易平台 — 招标挂网信息摸排 WorkBuddy Skill。

## 功能

从[苏州市公共资源交易平台](https://ggzy.suzhou.gov.cn/wjqfzx/035006/wjCity_jyxx.html)自动抓取吴江区建设工程数据，三线处理：

| 线路 | 目标 Sheet | 过滤条件 | 规模单位 |
|------|-----------|---------|---------|
| 施工类 | 招标挂网项目信息 | 合同额 ≥ 2亿，排除监理/设计/勘察/公示 | 亿元（÷10000） |
| 设计/勘察类 | 设计或勘察挂网信息 | 设计费/勘察费 ≥ 200万，仅含设计/勘察 | 万元（原值） |
| 招标预计划 | 招标预计划挂网信息 | 投资估算 ≥ 2亿，排除监理/设计/勘察/公示 | 亿元（÷10000） |

## 目录结构

```
├── README.md
├── SKILL.md                    # WorkBuddy Skill 定义文件
├── scripts/
│   ├── fetch_list.py           # 列表API抓取脚本
│   └── fetch_details.py        # 施工线详情页抓取与解析脚本
└── references/
    └── api_and_layout.md       # API参数、正则模式、双sheet列布局参考
```

## 快速开始

```bash
# 1. 抓取招标公告列表
python3 scripts/fetch_list.py --start 2026-05-30 --end 2026-07-17 > list.json

# 2. 施工线：过滤并抓取详情页（含业主、合同估算价）
cat list.json | python3 scripts/fetch_details.py > details.json

# 3. 设计/勘察线：用 Phase 3B 的 segment 策略提取设计费/勘察费
```

## 关键陷阱速查表

| 类别 | 陷阱 | 解决方案 |
|------|------|---------|
| API参数 | `diqu` 传数字"035"返回0条 | 必须传中文"吴江区" |
| 详情页 | `/jump.html` 是JS重定向页 | 先调 `getDetailPath` 拿真实路径 |
| HTML实体 | `&nbsp;` 未解码 | 正则前必须 `html.unescape()` |
| 设计费提取 | 全量文本 `.+` 正则导致 SIGKILL | 先 `text.find()` 截取600字符segment |
| 表格写入 | `set_range_value` 对已有数据行不生效 | 先 `insert_dimension` 插入空行 |
| 行插入 | `index` 为 string "9" 报错 | 必须传 JSON number |
| 单位混淆 | 施工亿元 vs 设计万元 vs 预计划亿元 | 施工/预计划 sheet col 6 除以10000，设计 sheet col 6 原值 |
| 预计划字段 | 字段名不同（招标人名称、投资估算） | 不能用"项目业主"和"合同估算价"正则 |

## 安装到 WorkBuddy

将整个目录放置到 `~/.workbuddy/skills/ysjc-scyx-zbgwxxmp/` 即可。
