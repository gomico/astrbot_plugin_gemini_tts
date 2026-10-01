---
name: gemini-tts
description: 需要发送语音时使用：用户要求发语音、朗读文本、用语音回复或指定语气朗读时，以及你自己想用语音代替文字回复时，都调用 gemini_tts 工具发送 Gemini 3.8 TTS 语音。工具使用当前插件配置的 voice，不需要也不能自行传 voice 参数。
---

# Gemini TTS 工具调用规则

## 何时调用

两种情形都要先按本规则决定参数，不要凭印象直接拼调用。

**一、用户要求发语音时**，例如：

- 发一条语音、说两句、念出来、朗读这段文字
- 用语音回复、用声音回答
- 指定开心、温柔、轻声、悲伤、兴奋、耳语、讽刺或生气的语气说话

**二、你自己决定用语音回复时**：

- 这句话用声音说出来比打字更合适——例如道晚安、撒娇、念一小段诗、模仿某种语气、情绪比文字更明显的时候。
- 用户试探你的声音，例如“你能发语音吗”“想听听你的声音”，也是发语音的时机。
- 主动发语音时，`text` 是你自己想说的话，不是复述用户的原话，也不是把上一段文字回复重念一遍。

主动发语音是加分项，不是常态：同一轮最多一条语音，不要连续两轮都发，也不要拿语音回避正常的文字交流。拿不准时用文字。

用户要求时不要先用文字回复“可以”，也不要要求用户再次确认。调用成功后只需简短确认，不要重复整段 transcript。

## 工具签名

```text
gemini_tts(
  text: string,
  style: string = ""
) -> string
```

### `text`

- 必填，必须是实际要朗读的正文。
- 尽量保持用户原文，不要改写、翻译、总结、删掉标点或添加舞台指令。
- 可以包含 Gemini inline vocal tags，例如 `<laugh>`、`<sigh>`、`<cough>`、`<breath>`、`<short pause>`、`<long pause>`。
- 也可以使用带局部风格的 expression 标签，例如：

  ```text
  <expression style="soft, slightly embarrassed, warm and gentle">要朗读的内容</expression>
  ```

- expression 标签中的 `style` 只影响标签包裹的局部内容；标签外的正文保持原样。
- 正文是中文时，inline tag 仍使用英文标签。
- 不要把持续语气写进正文，例如不要把 `Say cheerfully: 你好` 作为 text 传入。

### `style`

用于整段 turn 的持续语气、情绪、节奏或音量。

可直接使用以下 preset：

```text
natural
cheerful
soft
sad
excited
whispering
sarcastic
angry
```

也可以传任意自然语言 style，例如：

```text
softly, slightly nervous, speaking a little faster than usual
```

- 调用时必须一并给出 `style`：在生成朗读文本的同时决定这段文本该用什么语气，不要留空交给插件判断。
- 不要把持续风格转换成 `<whispering>` 等 inline tag；inline tag 只表示某个时间点发生的 vocal event。

## 调用示例

用户说“用开心的语气说：今天终于放假了”时：

```json
{
  "text": "今天终于放假了",
  "style": "cheerful"
}
```

用户说“把这句话发成语音：嗯……我想想”时（用户没指定语气，你需要判断）：

```json
{
  "text": "嗯……我想想",
  "style": "soft"
}
```

用户要求带停顿或叹气时：

```json
{
  "text": "嗯……<short pause>我想想。<sigh>可能还是这样比较好。",
  "style": "soft"
}
```

你自己决定发一条语音时（例如道晚安，没人要求你发）：

```json
{
  "text": "那我先睡啦，你也别熬太晚。<breath>晚安。",
  "style": "soft"
}
```

## 失败处理

如果工具返回错误，用简短文字说明语音发送失败并正常继续，不要反复重试同一个调用，也不要向用户暴露 API Key、完整错误堆栈或内部路径。
