# MiniCode

轻量 AI 编程 Agent。

## 安装

```bash
pip install -e .
```

## 配置

通过环境变量或项目目录下的 `.env` 文件配置。命令行参数优先级高于环境变量。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MINICODE_API_KEY` | API 密钥（必填） | — |
| `MINICODE_MODEL` | 模型名 | `deepseek-v4-flash` |
| `MINICODE_BASE_URL` | API 地址 | `https://api.deepseek.com` |
| `MINICODE_MAX_TOKENS` | 单次最大生成 token | `8192` |
| `MINICODE_TEMPERATURE` | 温度 | `1.0` |
| `MINICODE_MAX_CONTEXT` | 上下文压缩阈值（token） | `1048576` |

## 启动

```bash
uv run minicoder                    # 交互模式
uv run minicoder -r <id>            # 恢复已保存的会话
uv run minicoder -m gpt-4o          # 指定模型
uv run minicoder --base-url <url>   # 指定 API 地址
uv run minicoder --api-key <key>    # 指定 API 密钥
uv run minicoder --version          # 查看版本
```

当前 CLI 参数：

| 参数 | 说明 |
|------|------|
| `-h, --help` | 显示帮助信息 |
| `-m, --model <name>` | 覆盖 `MINICODE_MODEL` |
| `--base-url <url>` | 覆盖 `MINICODE_BASE_URL` |
| `--api-key <key>` | 覆盖 `MINICODE_API_KEY` |
| `-r, --resume <id>` | 恢复保存的会话 |
| `-v, --version` | 显示版本号 |

## 内置命令

在交互模式下输入：

| 命令 | 说明 |
|------|------|
| `/help` | 帮助 |
| `/reset` | 清空对话历史 |
| `/model` | 展示当前模型 |
| `/model <name>` | 切换模型 |
| `/tokens` | 查看本次 token 用量 |
| `/compact` | 手动压缩上下文 |
| `/diff` | 查看本次会话修改的文件 |
| `/save` | 保存当前会话 |
| `/sessions` | 列出已保存的会话 |
| `quit` | 退出 |

`Enter` 发送，`Esc+Enter` 换行。

## 工具

Agent 可调用以下工具：

- **bash** — 执行 shell 命令
- **read_file** — 读取文件
- **write_file** — 写入文件
- **edit_file** — 精确替换文件内容
- **glob** — 按模式匹配文件路径
- **grep** — 在文件中搜索文本
- **agent** — 启动子 Agent 处理子任务
- **ask_user** — 向用户提问并把回答返回给 Agent
