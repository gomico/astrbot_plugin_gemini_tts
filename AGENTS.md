# AGENTS.md

## 项目概览

这是一个 AstrBot 插件，直接调用 Gemini TTS 生成语音。style 判断器（selector）用在两处：

- 自动 TTS：每次都要判断。
- LLM Tool：只在 `style` 未指定时判断。`skills/gemini-tts/SKILL.md` 要求模型每次调用都自行给出 `style`，所以这条路径正常不会触发。

`style` 判断器的选择：

- `jev.enabled=true`：使用 `JevStyleSelector`。
- `jev.enabled=false`：使用当前会话主模型的 `MainModelStyleSelector`。

## 关键文件

- `main.py`：插件入口、配置读取、自动 TTS 和 LLM Tool。
- `_conf_schema.json`：AstrBot WebUI 配置 schema，必须保持合法 JSON。
- `style_selectors/jev.py`：Jev 请求、候选 style 和置信度回退逻辑。
- `style_selectors/main_model.py`：主模型 style 判断。
- `skills/gemini-tts/SKILL.md`：喂给 LLM 的 `gemini_tts` 调用规则（何时调用、style 取值、失败处理），是 style 行为的对外出口之一。AstrBot 的插件技能用 `skills/<子目录>/` 的目录名作技能名，frontmatter 里的 `name` 会被忽略。
- `services/gemini_tts.py`：Gemini 请求与音频落盘。
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
uv run --with pytest --with httpx pytest -q
python -m compileall -q main.py services style_selectors
git diff --check
```

修改配置项时同步更新 `_conf_schema.json` 和 `README.md`。改 `style` 相关行为时必须同步三处口径：`main.py` 里 `gemini_tts` 的 docstring、`skills/gemini-tts/SKILL.md`、`README.md`。`requirements.txt` 只声明 `httpx`（AstrBot Core 自带，`httpx[socks]>=0.28.1`）；不要重新引入 `google-genai`——AstrBot Core 按 `uv.lock` 装的是 2.10.0，那个版本的 annotation 联合类型不认 `speech_metadata`，会让请求 400。
