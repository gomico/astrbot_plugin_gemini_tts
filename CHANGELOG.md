# 更新日志

## 1.0.0

- 首次发布：直接调用 Gemini 3.8 TTS 生成语音，支持预置 Studio voice、Voice Replication / Voice Design 自定义音色和 8 种 style preset。
- 支持 inline vocal tags、`/GEMINITTS <文本>&&<语气>` 手动命令和 `gemini_tts` LLM Tool。
- 支持概率性自动语音回复；未指定语气时由 Jev 或当前会话主模型判断，可通过 `jev.enabled` 切换。
- 采用 AGPL-3.0 许可。
