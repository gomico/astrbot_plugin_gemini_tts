# AGENTS.md

## 项目概览

这是一个 AstrBot 插件，直接调用 Gemini TTS 生成语音。自动 TTS 或 LLM Tool 未指定 `style` 时，使用配置选择的 style selector：

- `jev.enabled=true`：使用 `JevStyleSelector`。
- `jev.enabled=false`：使用当前会话主模型的 `MainModelStyleSelector`。

## 关键文件

- `main.py`：插件入口、配置读取、自动 TTS 和 LLM Tool。
- `_conf_schema.json`：AstrBot WebUI 配置 schema，必须保持合法 JSON。
- `style_selectors/jev.py`：Jev 请求、候选 style 和置信度回退逻辑。
- `style_selectors/main_model.py`：主模型 style 判断。
- `utils/style.py`：style preset 和模板处理。
- `tests/`：单元测试。

## 配置约定

- Gemini API key、模型和 voice 配置放在 `gemini` 分组。
- Jev 配置放在 `jev` 分组；默认 base URL 为 `https://api.typesafe.ai`，默认模型为 `jev-latest`，默认置信度阈值为 `0.7`。
- `style_templates` 保持为顶层配置，不要嵌入 `gemini`。
- `whispering` 和 `sarcastic` 默认不参与 Jev 判断，因为仅凭文字较难判断。
- 不要在日志中输出 API Key 或完整 API 响应。

## 开发与验证

在仓库根目录运行：

```bash
pytest -q
python -m compileall -q main.py style_selectors
git diff --check
```

修改配置项时同步更新 `_conf_schema.json` 和 `README.md`。`requirements.txt` 中的 `google-genai` 版本需与 AstrBot Core 的依赖约束兼容。
