# 旧版邮件摘要服务（已弃用）

**Author:** Damon Li

本目录保留迁移前的原始实现（`requests` 直连 LLM + 正则脱敏），仅供对照与历史部署参考。
新服务请使用上级目录的 `agenticx_service/`。

## 文件说明

| 文件 | 说明 |
|------|------|
| `api_server.py` | 旧 Sanic 入口 |
| `preprocessor.py` | 正则 / jionlp 脱敏 |
| `prompts.py` / `prompts.yaml` | 提示词模板 |
| `config.py` / `config.json` | 服务配置 |
| `ops.sh` | 生产环境启停脚本（默认路径 `/opt/liziran/email_abstraction`） |
| `test_client.py` / `test_llm_service.py` | 联调脚本 |

## 本地运行（需在 `legacy/` 目录下执行）

```shell
cd legacy
pip install -r ../requirements.txt
python api_server.py --config config.json
```

## 生产启停

```shell
cd legacy
sh ops.sh start    # start | stop | restart | status
```

Made-with: Damon Li
