# astrbot_plugin_gemini_tts

直接调用 Gemini 3.8 TTS 的 AstrBot 插件，不使用 AstrBot 原生 TTS Provider。

## 安装

将本目录放入 AstrBot 的插件目录，安装 `requirements.txt`，然后在 WebUI 加载插件。

## 配置

- `api_key` (Gemini API Key)：WebUI 中按 secret 字段填写。
- `model` (Gemini TTS 模型)：`gemini-3.8-flash-tts` 或 `gemini-3.8-flash-lite-tts`。
- `prebuilt_voice` (预置 Studio voice)：30 个官方预置 voice 之一。
- `voice_id_override` (Voice Replication / Voice Design voice ID)：已创建的 `voice_...` 或 `voicekey_...`。
- `custom_voice_aliases` (自定义音色别名映射) 与 `custom_voice_alias` (当前自定义音色别名)：自定义别名映射和当前别名。
- `style_templates` (Style preset 模板)：8 个 preset 的可编辑英文模板。
- `auto_tts_enabled` (启用概率性自动语音回复) / `auto_tts_probability` (自动语音概率)：概率性自动把 Bot 文本回复转换为语音。

voice 优先级为：

```text
voice_id_override > custom_voice_aliases[custom_voice_alias] > prebuilt_voice
```

修改配置后，需要在 AstrBot WebUI 中手动重启本插件才能生效；本插件不实现配置热更新。

## Tool 与命令

LLM Tool 名称为 `gemini_tts`。Tool 的 `style` 缺失、为空或只有空白时使用配置中的 `natural` 模板。

手动命令：

```text
/GEMINITTS <text>&&<style>
/GEMINITTS <text>
```

命令省略 style 时不发送 `style`；显式写 `&&natural` 才使用 natural 模板。正文按逐字 transcript 传递，连续空格、换行和 inline tags 不会被插件改写。

## Inline vocal tags 与 style

例如：

```text
/GEMINITTS 嗯……<short pause>我想想。<sigh>可能还是这样比较好。&&soft
```

`<laugh>`、`<sigh>`、`<cough>`、`<breath>`、`<short pause>` 等是时间点 vocal event。即使正文是中文，Google 也建议使用英文 inline tags；持续的 whispering 等风格应放进 `style`，不要改写成 `<whispering>`。

Google 当前没有把 `style` 限定为英语，但官方示例和推荐短语主要使用英语，因此本插件默认模板使用英文。
