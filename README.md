# 路径
* 代码在42.137路径： **/opt/liziran/email_abstraction/**
* 代码在创建软链和同步写入代码前，需要对该目录进行赋权：**sudo chmod -R 777 /opt/liziran/email_abstraction/**

# AgenticX 版长文本摘要服务

基于 AgenticX 框架的新实现位于 `agenticx_service/`。旧版 `api_server.py` 已弃用（deprecated），仅作历史参考，请使用 `agenticx_service.app`。

## 安装

```shell
# 在 AgenticX 仓库根目录安装框架
pip install -e ../../

cd examples/AgenticX-LongTextSummarizer
pip install -r requirements.txt
```

## 配置

编辑 `config_agenticx.yaml`，或通过环境变量覆盖密钥：

```shell
export AGX_LLM_API_KEY="your-api-key"
```

## 启动

```shell
python -m agenticx_service.app --config config_agenticx.yaml
```

接口保持兼容：`POST /aibox/richMail/v1.0/intelliAbstract?sid=...`

## 测试

```shell
PYTHONPATH=".:../../" pytest agenticx_service/tests -q
```

## 评测

Phase 4 提供基于 `LLMJudge` / `CompositeJudge` 的自动化质量评估，覆盖 4 个固定用例：

| 用例 | 文件 | 验证点 |
|------|------|--------|
| 短邮件 | `evaluation/datasets/email_short.json` | PII 脱敏（`must_not` 硬断言）+ action 覆盖 |
| 长邮件链 | `evaluation/datasets/email_long_chain.json` | 8000+ 字 lost-in-middle 锚点召回 |
| 深度新闻 | `evaluation/datasets/news_deep.json` | 5W1H 事实覆盖 |
| 溢出边界 | `evaluation/datasets/news_overflow.json` | 超长输入不崩溃（硬断言） |

**运行（默认 Mock 裁判，适合 CI）：**

```shell
cd examples/AgenticX-LongTextSummarizer
PYTHONPATH=".:../../" python -m agenticx_service.evaluation.run_eval
```

**使用真实裁判模型**（与业务模型分离，见 `config_agenticx.yaml` 的 `judge_llm` 段）：

```shell
export AGX_JUDGE_API_KEY="your-judge-api-key"
export AGX_EVAL_USE_MOCK_JUDGE=0
PYTHONPATH=".:../../" python -m agenticx_service.evaluation.run_eval
```

**报告解读：**

- 输出路径：`agenticx_service/evaluation/report_<timestamp>.json` 与同名的 `.md`
- 每条用例含 `dimension_scores`：`faithfulness`、`conciseness`，以及场景维度（email → `action_item_coverage`，news → `fact_5w1h_coverage`）
- `hard_failures` 非空（如 PII 泄漏、overflow 崩溃）直接判 FAIL，不受 LLM 主观分影响
- `passed=true` 需同时满足：无硬失败 + 各维度评委通过 + `CompositeJudge` 聚合通过

## 实施计划

分阶段 plan 见 `plans/` 目录（`2026-06-17-longtext-summarizer-*.plan.md`）。

# 环境安装（旧版）
```shell
conda create -n liziran python=3.10.12

conda activate liziran

pip install -r requirements.txt
```

# 执行顺序
```shell
sh ops.sh start
```
