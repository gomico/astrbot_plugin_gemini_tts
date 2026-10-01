# 更新日志

## 1.1.0

- 新增语言/方言指导配置，可在 WebUI 中编辑并追加到所有 style preset。
- 默认语言指导覆盖大陆普通话、标准日语和英式 RP；配置为空时不追加语言指导。

## 1.0.1

- 修复：语音发不出去（Gemini 返回 HTTP 400 `invalid_request`）。原因是 `google-genai` SDK 的 annotation 联合类型不识别 `speech_metadata`，会把语气序列化成 `UNKNOWN` 后发出。
- 改为直接向 Interactions 接口发送 HTTP 请求，不再依赖 `google-genai`，插件行为不再受 AstrBot Core 所装 SDK 版本影响。
- 依赖变更：`requirements.txt` 由 `google-genai` 改为 `httpx`（AstrBot Core 自带）。
- 400 与其它 HTTP 错误分别映射，异常信息中附带接口返回的原因；聊天里的提示文案不变。

## 1.0.0

- 首次发布：直接调用 Gemini 3.8 TTS 生成语音，支持预置 Studio voice、Voice Replication / Voice Design 自定义音色和 8 种 style preset。
- 支持 inline vocal tags、`/GEMINITTS <文本>&&<语气>` 手动命令和 `gemini_tts` LLM Tool。
- 支持概率性自动语音回复；未指定语气时由 Jev 或当前会话主模型判断，可通过 `jev.enabled` 切换。
- 采用 AGPL-3.0 许可。
