# Cookie 刷新工具

通过 Docker 容器使用 Playwright + Chromium 自动访问网页刷新 Cookie。

## 功能特性

-   支持 Netscape Cookie 格式（兼容 curl、wget 等工具）
-   使用真实浏览器环境（Chromium）访问页面
-   自动刷新页面以更新 Cookie
-   自定义 HTTP Headers 支持
-   反爬虫检测对抗（隐藏 webdriver 特征）
-   完整日志记录
-   输出渲染后的 HTML 内容

## 技术栈

-   **基础镜像:** mcr.microsoft.com/playwright/python:v1.40.0-jammy
-   **Python 版本:** 3.11+
-   **核心依赖:** Playwright

## 快速开始

### 方式一：使用预构建镜像（推荐）

从 GitHub Container Registry 拉取最新镜像：

```bash
docker pull ghcr.io/lc4t/refresh_cookie:latest
```

### 方式二：本地构建

```bash
# 克隆仓库
git clone https://github.com/lc4t/refresh_cookie.git
cd refresh_cookie

# 构建镜像
docker build -t cookie-refresher .
```

### 准备 Cookie 文件

创建 Netscape 格式的 Cookie 文件（参见 `examples/cookie_example.txt`）:

```
# Netscape HTTP Cookie File
.example.com    TRUE    /    FALSE    1735689600    session_id    abc123
.example.com    TRUE    /    TRUE    1767225600    secure_token    xyz789
```

### 运行容器

```bash
# 使用预构建镜像（推荐）
IMAGE=ghcr.io/lc4t/refresh_cookie:latest

# 或使用本地构建的镜像
# IMAGE=cookie-refresher

# 方式一：直接更新原 Cookie 文件（推荐 - 挂载目录）
docker run --rm \
  -e URL="https://example.com" \
  -e COOKIE_FILE="/data/cookie.txt" \
  -e OUTPUT_COOKIE="/data/cookie.txt" \
  -e OUTPUT_HTML="/data/page.html" \
  -v $(pwd):/data \
  $IMAGE

# 方式二：输出到新文件
docker run --rm \
  -e URL="https://example.com" \
  -e COOKIE_FILE="/input/cookie.txt" \
  -e OUTPUT_COOKIE="/output/new_cookie.txt" \
  -e OUTPUT_HTML="/output/page.html" \
  -v $(pwd)/cookie.txt:/input/cookie.txt:ro \
  -v $(pwd)/output:/output \
  $IMAGE
```

## 环境变量参数

### 必需参数

| 参数名          | 说明                                          | 示例                     |
| --------------- | --------------------------------------------- | ------------------------ |
| `URL`           | 目标网址                                      | `https://example.com`    |
| `COOKIE_FILE`   | 输入 Cookie 文件路径                          | `/input/cookie.txt`      |
| `OUTPUT_COOKIE` | 输出 Cookie 文件路径（可与 COOKIE_FILE 相同） | `/output/new_cookie.txt` |
| `OUTPUT_HTML`   | 输出 HTML 文件路径                            | `/output/page.html`      |

### 可选参数

| 参数名           | 默认值 | 说明                             |
| ---------------- | ------ | -------------------------------- |
| `WAIT_TIME`      | 5      | 首次加载等待时间（秒）           |
| `REFRESH_DELAY`  | 5      | 刷新后等待时间（秒）             |
| `CUSTOM_HEADERS` | `{}`   | 自定义 HTTP Headers（JSON 格式） |
| `LOG_FILE`       | stdout | 日志输出路径                     |

## 使用示例

### 基础使用（输出到新文件）

```bash
docker run --rm \
  -e URL="https://example.com" \
  -e COOKIE_FILE="/input/cookie.txt" \
  -e OUTPUT_COOKIE="/output/new_cookie.txt" \
  -e OUTPUT_HTML="/output/page.html" \
  -v $(pwd)/cookie.txt:/input/cookie.txt:ro \
  -v $(pwd)/output:/output \
  cookie-refresher
```

### 直接更新原 Cookie 文件（推荐）

将刷新后的 Cookie 直接写回原文件，无需创建新文件。**推荐挂载整个目录**：

```bash
# 推荐：挂载目录（Cookie 和 HTML 都能正确保存）
docker run --rm \
  -e URL="https://example.com" \
  -e COOKIE_FILE="/data/cookie.txt" \
  -e OUTPUT_COOKIE="/data/cookie.txt" \
  -e OUTPUT_HTML="/data/page.html" \
  -v $(pwd):/data \
  cookie-refresher

# 或者：挂载单个文件（仅更新 Cookie，HTML 需要单独处理）
docker run --rm \
  -e URL="https://example.com" \
  -e COOKIE_FILE="/data/cookie.txt" \
  -e OUTPUT_COOKIE="/data/cookie.txt" \
  -e OUTPUT_HTML="/output/page.html" \
  -v $(pwd)/cookie.txt:/data/cookie.txt \
  -v $(pwd)/output:/output \
  cookie-refresher
```

**注意事项：**

-   `COOKIE_FILE` 和 `OUTPUT_COOKIE` 可以是同一个文件
-   挂载时**不要**使用 `:ro`（只读）标志
-   工具会先读取完整内容再写入，保证数据安全
-   **推荐挂载目录而非单个文件**，这样 Cookie 和 HTML 都能保存在同一位置

### 使用自定义 Headers

```bash
docker run --rm \
  -e URL="https://example.com" \
  -e COOKIE_FILE="/data/cookie.txt" \
  -e OUTPUT_COOKIE="/data/cookie.txt" \
  -e OUTPUT_HTML="/data/page.html" \
  -e CUSTOM_HEADERS='{"User-Agent":"Mozilla/5.0 Custom","Referer":"https://google.com"}' \
  -v $(pwd)/cookie.txt:/data/cookie.txt \
  cookie-refresher
```

### 使用日志文件

```bash
docker run --rm \
  -e URL="https://example.com" \
  -e COOKIE_FILE="/data/cookie.txt" \
  -e OUTPUT_COOKIE="/data/cookie.txt" \
  -e OUTPUT_HTML="/data/page.html" \
  -e LOG_FILE="/logs/refresh.log" \
  -v $(pwd)/cookie.txt:/data/cookie.txt \
  -v $(pwd)/logs:/logs \
  cookie-refresher
```

### 调整等待时间

```bash
docker run --rm \
  -e URL="https://example.com" \
  -e COOKIE_FILE="/data/cookie.txt" \
  -e OUTPUT_COOKIE="/data/cookie.txt" \
  -e OUTPUT_HTML="/data/page.html" \
  -e WAIT_TIME=10 \
  -e REFRESH_DELAY=8 \
  -v $(pwd)/cookie.txt:/data/cookie.txt \
  cookie-refresher
```

## Netscape Cookie 格式说明

### 格式规范

每行包含 7 个字段，用 TAB 分隔：

```
domain    flag    path    secure    expiration    name    value
```

**字段说明：**

-   `domain`: Cookie 所属域名（如 `.example.com`）
-   `flag`: 是否对所有子域有效（`TRUE` 或 `FALSE`）
-   `path`: Cookie 路径（通常为 `/`）
-   `secure`: 是否仅 HTTPS 传输（`TRUE` 或 `FALSE`）
-   `expiration`: 过期时间（Unix 时间戳，0 表示会话 Cookie）
-   `name`: Cookie 名称
-   `value`: Cookie 值

### 示例文件

```
# Netscape HTTP Cookie File
# https://curl.se/docs/http-cookies.html
.example.com    TRUE    /    FALSE    1735689600    session_id    abc123def456
.example.com    TRUE    /    TRUE     1767225600    auth_token    xyz789token
example.com     FALSE   /    FALSE    0             temp_data     test123
```

### 从浏览器导出 Cookie

**Chrome 扩展：**

-   [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/)

**Firefox 扩展：**

-   [cookies.txt](https://addons.mozilla.org/firefox/addon/cookies-txt/)

## 工作流程

1. 读取 Netscape 格式 Cookie 文件
2. 启动 Chromium 浏览器（headless 模式）
3. 将 Cookie 加载到浏览器上下文
4. 应用自定义 Headers（如果提供）
5. 访问目标 URL
6. 等待页面完全加载（`WAIT_TIME` 秒）
7. 刷新页面
8. 再次等待（`REFRESH_DELAY` 秒）
9. 获取更新后的 Cookie
10. 获取渲染后的完整 HTML
11. 保存 Cookie 和 HTML 到输出文件

## 反爬虫对抗

工具内置以下反检测措施：

-   禁用自动化控制特征：`--disable-blink-features=AutomationControlled`
-   隐藏 `navigator.webdriver` 属性
-   使用真实浏览器 User-Agent
-   支持自定义 Referer 和其他 Headers

## 常见问题

### 1. Cookie 数量变化警告

**现象：** 日志显示 `Cookie count changed: 5 -> 7`

**原因：** 网站在访问或刷新后设置了新的 Cookie，这是正常行为。

**处理：** 无需担心，工具会保存所有更新后的 Cookie。

### 2. 页面加载超时

**现象：** `Navigation failed: Timeout 30000ms exceeded`

**原因：** 网络慢或页面加载资源过多。

**解决：** 增加 `WAIT_TIME` 或检查网络连接。

### 3. Cookie 文件格式错误

**现象：** `Invalid format, expected 7 fields`

**原因：** Cookie 文件不是标准 Netscape 格式。

**解决：** 确保使用 TAB 分隔符，不是空格；参考 `examples/cookie_example.txt`。

### 4. 验证自定义 Headers 是否生效

访问测试网站：

```bash
docker run --rm \
  -e URL="https://httpbin.org/headers" \
  -e COOKIE_FILE="/data/cookie.txt" \
  -e OUTPUT_COOKIE="/data/cookie.txt" \
  -e OUTPUT_HTML="/data/headers.html" \
  -e CUSTOM_HEADERS='{"X-Custom-Header":"test123"}' \
  -v $(pwd)/cookie.txt:/data/cookie.txt \
  cookie-refresher

# 查看输出的 HTML 文件确认 Headers
cat cookie.txt  # 查看更新后的 Cookie
```

## 文件结构

```
refresh_cookie/
├── Dockerfile                  # Docker 镜像构建文件
├── requirements.txt            # Python 依赖
├── src/
│   ├── cookie_utils.py         # Cookie 格式转换工具
│   └── refresh_cookie.py       # 主程序入口
├── README.md                   # 使用文档
├── .gitignore                  # Git 忽略配置
└── examples/
    ├── cookie_example.txt      # Cookie 格式示例
    └── test.sh                 # 快速测试脚本
```

## Docker 镜像

### 可用镜像标签

项目通过 GitHub Actions 自动构建并发布 Docker 镜像到 GitHub Container Registry (ghcr.io)。

| 标签     | 说明                  | 示例                                 |
| -------- | --------------------- | ------------------------------------ |
| `latest` | 最新的主分支构建      | `ghcr.io/lc4t/refresh_cookie:latest` |
| `main`   | 主分支最新版本        | `ghcr.io/lc4t/refresh_cookie:main`   |
| `dev`    | 开发分支最新版本      | `ghcr.io/lc4t/refresh_cookie:dev`    |
| `v*`     | 发布版本（如 v1.0.0） | `ghcr.io/lc4t/refresh_cookie:v1.0.0` |

### 拉取镜像

```bash
# 最新版本
docker pull ghcr.io/lc4t/refresh_cookie:latest

# 特定版本
docker pull ghcr.io/lc4t/refresh_cookie:v1.0.0

# 开发版本
docker pull ghcr.io/lc4t/refresh_cookie:dev
```

### 平台支持

镜像支持以下平台：

-   `linux/amd64` - x86_64 架构（Intel/AMD）
-   `linux/arm64` - ARM64 架构（Apple Silicon, ARM 服务器）

## CI/CD

项目使用 GitHub Actions 自动化构建流程：

-   **自动触发：** 推送到 main/dev 分支，或创建版本标签时自动构建
-   **多平台构建：** 同时构建 amd64 和 arm64 架构
-   **自动发布：** 构建成功后自动推送到 GitHub Container Registry
-   **缓存优化：** 使用 GitHub Actions Cache 加速构建

查看构建状态：[Actions](https://github.com/lc4t/refresh_cookie/actions)

## 许可证

Apache License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

-   [Playwright](https://playwright.dev/) - 强大的浏览器自动化工具
-   [Microsoft Playwright Docker Images](https://mcr.microsoft.com/en-us/product/playwright/python/about)
