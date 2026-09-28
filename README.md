# 3分鐘快速了解ISO27001

講師：Allan Lo (http://www.123hi.org)

依據《ISO 27001 標準簡介》上課簡報（講師：羅宇倫 Allan Lo）製作的 3 分鐘課程重點導覽動畫。

**Q 版（主要版本）**：活潑漫畫風格，由 Q 版虛擬講師 Allan 用對話框講解。
- 🌐 線上播放（GitHub Pages）：https://allanloplus.github.io/ISO27001_course/
- 🎬 影片：[`video/ISO27001_course_intro.mp4`](video/ISO27001_course_intro.mp4)（1920×1080、30fps、180 秒、輕快背景音樂＋對話音效）
- 原始檔：[`animation/index.html`](animation/index.html)（空白鍵暫停、點擊進度條跳轉）

**有聲版**：同 Q 版動畫，對話框出現時 Allan 老師會開口說話（台灣年輕男聲「雲哲」zh-TW-YunJheNeural），背景音樂自動壓低。
- 🌐 https://allanloplus.github.io/ISO27001_course/animation/voice.html（按「開始播放」後開始，任何瀏覽器聲音都一樣）
- 🎬 影片：[`video/ISO27001_course_intro_voice.mp4`](video/ISO27001_course_intro_voice.mp4)
- 語音檔：[`animation/voice/`](animation/voice/)（每句一個 mp3，`voice.json` 記錄時間與長度）

**經典版**：深色科技風、無角色。
- 🌐 https://allanloplus.github.io/ISO27001_course/animation/classic.html
- 🎬 [`video/ISO27001_course_intro_classic.mp4`](video/ISO27001_course_intro_classic.mp4)

## 修改 Q 版講師台詞

台詞都在 `animation/index.html` 的 `LINES` 陣列：`[開始秒數, 結束秒數, "文字（\n 換行，<b>強調</b>）", 動作, "（選填）有聲版朗讀用文字"]`，
動作可用 `wave`（揮手）、`point`（指向內容）、`cheer`（雙手舉高）、`thumb`（比讚）、`idle`。

## 動畫段落（兩版相同架構）

| 時間 | 段落 | 內容重點 |
|---|---|---|
| 0:00 | 開場 | ISO/IEC 27001:2022 標準簡介、講師介紹 |
| 0:09 | 課程大綱 | 標準沿革 / 架構與內容 / 附錄 A 控制措施 |
| 0:18 | ISMS 演進歷史 | 1995 BS 7799 → 2005 ISO 27001 → 2022 改版 |
| 0:36 | 27001 vs 27002 | 要求事項（可驗證，shall）vs 控制措施指引（參考，should）；以風險為基礎 |
| 0:50 | 系列標準家族 | 共通性、產業別、特定主題標準（27005、27017、27701…） |
| 1:02 | 標準架構 | 第 1~3 章前言、第 4~10 章要求（不得排除）、附錄 A |
| 1:18 | PSDCA 模式 | 規劃 P、支援 S、執行 D、檢查 C、行動 A |
| 1:30 | 條文 4~10 | 組織全景、領導、規劃（風險評鑑 → 風險處理 → SoA）、支援、運作、績效評估、改善 |
| 2:16 | 附錄 A | 4 主題 93 項：A.5 組織 37、A.6 人員 8、A.7 實體 14、A.8 技術 34 |
| 2:30 | 15 項運作能力 | 治理、人資安全、資訊保護 … 遵循性 |
| 2:43 | 控制屬性 | 控制類型、資安特性、網宇安全概念、運作能力、安全領域 |
| 2:51 | 重點回顧 | 延伸學習：sites.google.com/123hi.org/iso27001 |

## 重新產生影片

動畫以 HTML/JS 撰寫，每一影格由時間 `t` 決定（可重現），再用 Playwright 逐格擷取並以 ffmpeg 編碼。

```bash
npm i playwright && pip install numpy imageio-ffmpeg
node scripts/render.js video.mp4 30          # 逐格擷取 → 無聲 MP4（經典版前面加 PAGE=classic.html）
node scripts/render.js --events events.json   # 取出對話框時間點
python3 scripts/make_audio.py bgm.wav --pop events.json   # Q 版音樂＋音效（經典版省略 --pop 參數）
ffmpeg -i video.mp4 -i bgm.wav -c:v copy -c:a aac -b:a 160k -shortest video/ISO27001_course_intro.mp4
```

有聲版：

```bash
pip install edge-tts
node scripts/render.js --events events.json
python3 scripts/make_voice.py events.json animation/voice            # 產生每句台詞的語音（雲哲）
QUERY='&voice' node scripts/render.js video_voice.mp4 30             # 嘴型跟語音長度同步
python3 scripts/make_audio.py bgm_voice.wav --pop events.json --voice animation/voice
ffmpeg -i video_voice.mp4 -i bgm_voice.wav -c:v copy -c:a aac -b:a 160k -shortest video/ISO27001_course_intro_voice.mp4
```

改了台詞後，重新執行 `make_voice.py` 即可更新語音。

修改內容：編輯 `animation/index.html` 中各 `<section class="scene" data-start data-end>` 的文字與時間即可。
