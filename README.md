# astrbot_plugin_gemini_tts

直接调用 Gemini 3.8 TTS 生成语音，不使用 AstrBot 原生 TTS Provider。

支持 30 个官方预置 Studio voice、Voice Replication / Voice Design 自定义音色、8 种 style preset、inline vocal tags，以及概率性自动语音回复；可通过 LLM Tool 或手动命令触发。

## 安装

- 从 AstrBot 插件市场安装，或在 WebUI 的插件管理里填入仓库地址 `https://github.com/gomico/astrbot_plugin_gemini_tts`。
- 手动安装：将本目录放入 AstrBot 的插件目录，安装 `requirements.txt`，然后在 WebUI 加载插件。

依赖由 AstrBot 按 `requirements.txt` 安装（`google-genai==2.10.0`）。

## 配置

- `enabled` (启用插件)：关闭后插件整体不生效，手动命令会提示未启用，LLM Tool 也不可用。
- `tool_enabled` (启用 gemini_tts LLM Tool)：关闭后 LLM 无法调用本插件；手动命令和自动语音不受影响。
- `gemini.api_key` (Gemini API Key)：填写 AI Studio 创建的 API Key。
- `gemini.model` (Gemini TTS 模型)：`gemini-3.8-flash-tts` 或 `gemini-3.8-flash-lite-tts`。
- `gemini.prebuilt_voice` (预置 Studio voice)：30 个官方预置 voice 之一。
- `gemini.voice_id_override` (Voice Replication / Voice Design voice ID)：已创建的 `voice_...` 或 `voicekey_...`。
- `gemini.custom_voice_aliases` (自定义音色别名映射) 与 `gemini.custom_voice_alias` (当前自定义音色别名)：自定义别名映射和当前别名。
- `style_templates` (Style preset 模板)：8 个 preset 的可编辑英文模板，key 为 `natural`、`cheerful`、`soft`、`sad`、`excited`、`whispering`、`sarcastic`、`angry`。
- `jev.enabled`：开启后，自动语音使用 Jev 判断 style；关闭时使用当前会话主模型。
- `jev.base_url` / `jev.model` / `jev.api_key` / `jev.confidence_threshold`：Jev 接口配置，默认分别为 `https://api.typesafe.ai`、`jev-latest`、空、`0.7`。
- `jev.styles`：参与 Jev 判断的 style key 列表，取值同 `style_templates` 的 8 个 key。留空时使用默认候选 `natural`、`cheerful`、`soft`、`sad`、`excited`、`angry`；`natural` 始终保留作低置信度回退。`whispering` 和 `sarcastic` 靠文字较难判断，默认不参与判断。
- `auto_tts_enabled` (启用概率性自动语音回复) / `auto_tts_probability` (自动语音概率)：概率性自动把 Bot 文本回复转换为语音。

voice 优先级为：

```text
voice_id_override > custom_voice_aliases[custom_voice_alias] > prebuilt_voice
```

修改配置后，需要在 AstrBot WebUI 中手动重启本插件才能生效。

## Tool 与命令

LLM Tool 名称为 `gemini_tts`。Tool 的 `style` 缺失、为空或只有空白时，会进行一次 style 判断：

- `jev.enabled=true`：使用 Jev 判断。
- `jev.enabled=false`：使用当前会话的主模型判断。

Tool 明确填写 `style` 时不进行判断，直接使用指定的 style。

调用时机与参数写法由插件自带的 `skills/gemini-tts/SKILL.md` 约束：用户要求发语音、朗读或指定语气时调用，Bot 主动想用语音代替文字回复时同样调用；该 skill 需要在人格的技能列表里启用后才会进入系统提示词。

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

## Style 判断日志

自动 TTS 和 Tool 未填写 `style` 时，会在 AstrBot 日志中记录判断器和结果，例如：

```text
Gemini TTS style selected: selector=JevStyleSelector style=excited
Gemini TTS style selected: selector=MainModelStyleSelector style=natural
```

日志只记录判断器类型和 style，不记录 API Key。

## 许可

本项目采用 [AGPL-3.0](LICENSE) 许可。
