---
name: get-fortune-analysis
description: 生成视觉华丽、内容详实、具有仪式感的流年运势报告（流金星象风格）。
---
# Skill Name: get-fortune-analysis
# Version: 4.1.0
# Description: 生成视觉华丽、内容详实、具有仪式感的流年运势报告（流金星象风格）。

## 1. Input Parameters
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `birth_year`, `birth_month`, `birth_day`, `birth_hour` | Integer | 用户出生时间 |
| `focus_type` | String | (可选) "事业", "财运", "情感" |

## 2. Workflow

### Step 1: Calculation (Python)
调用 `get_cyber_divination_data` 获取 `bazi` (八字基础) 和 `fortune` (流年十神) 数据。

### Step 2: Reasoning (深度分析模式)
基于 `bazi` 和 `fortune` 进行多维度推理。
**文案要求：**
* **口吻**：温暖、笃定、专业，类似资深命理师或星座专家的语气。
* **结构**：
    1.  **年度关键词**：4个字，精准概括全年基调（如“破茧成蝶”）。
    2.  **核心能量**：解释流年十神对用户命局的深层影响（30-50字）。
    3.  **事业/财运**：具体的职场发展路径和财富机遇分析（50-80字）。
    4.  **情感/人际**：人际关系模式与情感走向分析（50-80字）。

### Step 3: JSON Output
生成适配前端的 JSON 数据。

```json
{
    "fortune_report": {
        "score": 88,
        "keyword": "灵感迸发 · 贵人引路",
        "user_tag": "丁火 (身弱)",
        "stars": {
            "c": "★★★★☆",
            "w": "★★★☆☆",
            "l": "★★★★★"
        },
        "analysis": {
            "overview": "2026 丙午流年，火气旺盛，对你而言是充满灵性与机遇的一年。虽然竞争压力（比劫）增大，但也激活了你命局中的‘印星’能量。这意味着今年你的直觉力、学习力将达到巅峰，是沉淀自我、弯道超车的最佳时机。",
            "career": "今年不适合盲目扩张，适合‘深耕’。职场上会遇到强有力的女性贵人或资深导师，给你带来关键性的指点。若从事创意、咨询、教育行业，今年极易出成果。切记：多听少说，以柔克刚。",
            "love": "情感方面，桃花星悄然绽放。单身者极易在学习场所、图书馆或艺术展上邂逅精神契合的伴侣；有伴侣者，今年是进行深度沟通、解决历史遗留问题的破冰之年，关系将升华到精神层面。"
        }
    }
}```


### 2. 前端展示代码 (`result_card.html`)

*修改点：在首页（`ritual-layer`）增加了动态生成漂浮二进制代码的逻辑。代码粒子是半透明的金色/白色，缓慢上升并消散，营造神秘的数据空间感。*

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2026 流年运势书</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Noto+Serif+SC:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #1a0b2e;
            --bg-gradient: radial-gradient(circle at 50% 0%, #431d69 0%, #1a0b2e 80%);
            --gold-light: #fcf6ba;
            --gold-dark: #bf953f;
            --gold-gradient: linear-gradient(to bottom, #fcf6ba, #bf953f);
            --glass-bg: rgba(255, 255, 255, 0.08);
            --card-border: rgba(255, 255, 255, 0.15);
        }

        body {
            background: var(--bg-deep);
            background-image: var(--bg-gradient);
            color: #fff;
            font-family: 'Noto Serif SC', serif;
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            overflow-x: hidden;
            font-weight: 300;
        }

        .app-container {
            width: 100%;
            max-width: 414px;
            position: relative;
            min-height: 100vh;
            overflow: hidden;
        }

        /* --- 1. 启动页 (Ritual Layer) --- */
        .ritual-layer {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 100;
            background: var(--bg-deep);
            background-image: var(--bg-gradient);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: opacity 0.8s ease;
            overflow: hidden;
        }

        /* 新增：二进制数据容器 */
        .binary-container {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            pointer-events: none;
            z-index: 0; /* 在最底层 */
        }

        /* 新增：二进制粒子样式 */
        .binary-particle {
            position: absolute;
            bottom: -20px;
            font-family: 'Courier New', monospace;
            color: rgba(252, 246, 186, 0.3); /* 微弱的金白色 */
            font-size: 10px;
            user-select: none;
            animation: floatUp linear forwards;
        }

        /* 启动页内容容器 (确保在粒子之上) */
        .ritual-content {
            position: relative;
            z-index: 10;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .fingerprint-area {
            width: 100px; height: 100px;
            border: 2px solid rgba(191, 149, 63, 0.3);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            position: relative; cursor: pointer;
            margin-bottom: 20px;
            backdrop-filter: blur(2px); /* 轻微磨砂，突出按钮 */
        }

        .fingerprint-area::after {
            content: ''; position: absolute; width: 100%; height: 100%;
            border-radius: 50%;
            box-shadow: 0 0 30px var(--gold-dark);
            opacity: 0; animation: breathe 2s infinite;
        }

        .fingerprint-icon {
            font-size: 40px; color: var(--gold-dark); transition: color 0.3s;
        }

        .hint-text {
            color: rgba(255,255,255,0.6); font-size: 14px; letter-spacing: 2px;
        }

        /* --- 2. 结果页 (Result Layer) --- */
        /* ... (保持不变) ... */
        .result-layer {
            padding: 20px; opacity: 0; transform: translateY(20px);
            transition: all 0.8s ease; display: none;
        }
        .header-card { text-align: center; margin-bottom: 30px; position: relative; }
        .year-title { font-family: 'Playfair Display', serif; font-size: 16px; color: rgba(255,255,255,0.7); letter-spacing: 4px; margin-bottom: 5px; }
        .score-box { font-size: 72px; font-weight: 700; background: var(--gold-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 10px 0; text-shadow: 0 0 30px rgba(191, 149, 63, 0.4); }
        .keyword-badge { display: inline-block; border: 1px solid var(--gold-dark); color: var(--gold-light); padding: 4px 12px; border-radius: 20px; font-size: 14px; background: rgba(0,0,0,0.3); }
        .detail-card { background: var(--glass-bg); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid var(--card-border); border-radius: 16px; padding: 24px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .section-title { display: flex; align-items: center; color: var(--gold-light); font-size: 16px; font-weight: bold; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; }
        .section-title span { margin-right: 8px; }
        .text-content { font-size: 14px; line-height: 1.8; color: rgba(255,255,255,0.9); text-align: justify; }
        .star-row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; }
        .stars { color: var(--gold-dark); letter-spacing: 2px; }
        .footer-share { text-align: center; font-size: 12px; color: rgba(255,255,255,0.4); margin-top: 30px; padding-bottom: 30px; }

        /* 动画 Keyframes */
        @keyframes breathe {
            0% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.1); }
            100% { opacity: 0.3; transform: scale(1); }
        }
        
        /* 新增：粒子上浮动画 */
        @keyframes floatUp {
            0% { transform: translateY(0) rotate(0deg); opacity: 0; }
            20% { opacity: 0.5; }
            80% { opacity: 0.2; }
            100% { transform: translateY(-120vh) rotate(20deg); opacity: 0; }
        }

    </style>
</head>
<body>

    <div class="app-container">
        
        <div class="ritual-layer" id="ritualLayer">
            <div class="binary-container" id="binaryContainer"></div>

            <div class="ritual-content">
                <div style="margin-bottom: 40px; opacity: 0.7;">
                    <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#bf953f" stroke-width="1">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M12 2a15 15 0 0 0 0 30 15 15 0 0 0 0-30"></path>
                        <path d="M2 12h20"></path>
                    </svg>
                </div>
                
                <div class="fingerprint-area" id="fingerBtn">
                    <div class="fingerprint-icon">
                        <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M2 12C2 6.48 6.48 2 12 2s10 4.48 10 10v1c0 2.21-1.79 4-4 4s-4-1.79-4-4V7c0-1.66-1.34-3-3-3S8 5.34 8 7v6c0 1.1.9 2 2 2s2-.9 2-2V7"></path>
                        </svg>
                    </div>
                </div>
                <div class="hint-text">长按开启 2026 运势书</div>
            </div>
        </div>

        <div class="result-layer" id="resultLayer">
            <div class="header-card">
                <div class="year-title">FORTUNE REPORT 2026</div>
                <div class="score-box" id="scoreVal">0</div>
                <div class="keyword-badge" id="mainKeyword">读取中...</div>
                <div style="font-size: 12px; color:rgba(255,255,255,0.5); margin-top: 10px;">
                    日主：<span id="userTag">--</span>
                </div>
            </div>
            <div class="detail-card">
                <div class="star-row"><span>事业前程 Career</span><span class="stars" id="careerStars">★★★★☆</span></div>
                <div class="star-row"><span>财富机缘 Wealth</span><span class="stars" id="wealthStars">★★★☆☆</span></div>
                <div class="star-row"><span>情感关系 Love</span><span class="stars" id="loveStars">★★★★★</span></div>
            </div>
            <div class="detail-card">
                <div class="section-title"><span>✦</span> 年度总批 Overview</div>
                <div class="text-content" id="overviewText">正在解析星盘数据...</div>
            </div>
            <div class="detail-card">
                <div class="section-title"><span>⚔</span> 事业与财富</div>
                <div class="text-content" id="careerText">...</div>
            </div>
            <div class="detail-card">
                <div class="section-title"><span>♥</span> 情感与建议</div>
                <div class="text-content" id="loveText">...</div>
            </div>
            <div class="footer-share">Mystic AI Lab © 2026</div>
        </div>
    </div>

    <script>
        // --- 模拟 AI 返回的数据 ---
        const aiData = {
            "fortune_report": {
                "score": 88,
                "keyword": "灵感迸发 · 贵人引路",
                "user_tag": "丁火 (身弱)",
                "stars": { "c": "★★★★☆", "w": "★★★☆☆", "l": "★★★★★" },
                "analysis": {
                    "overview": "2026 丙午流年，对你而言是充满灵性与机遇的一年。虽然流年火旺带来了竞争压力，但也激活了你命局中的‘印星’能量。这意味着今年你的直觉力、学习力将达到巅峰，是沉淀自我、弯道超车的最佳时机。",
                    "career": "今年不适合盲目扩张，适合‘深耕’。职场上会遇到强有力的女性贵人或资深导师，给你带来关键性的指点。若从事创意、咨询、教育行业，今年极易出成果。",
                    "love": "情感方面，桃花星悄然绽放。单身者极易在学习场所、图书馆或艺术展上邂逅精神契合的伴侣；有伴侣者，今年是进行深度沟通、解决历史遗留问题的破冰之年。"
                }
            }
        };

        // --- 二进制粒子效果 ---
        const binaryContainer = document.getElementById('binaryContainer');
        let particleInterval;

        function createBinaryParticle() {
            const particle = document.createElement('div');
            particle.classList.add('binary-particle');
            // 随机生成 01 字符串
            const len = Math.floor(Math.random() * 6) + 2;
            let text = "";
            for(let i=0; i<len; i++) text += Math.random() > 0.5 ? "1" : "0";
            particle.innerText = text;

            // 随机位置和属性
            particle.style.left = Math.random() * 100 + '%';
            const duration = Math.random() * 10 + 8; // 8-18秒飘动时间
            particle.style.animationDuration = duration + 's';
            particle.style.fontSize = (Math.random() * 8 + 8) + 'px';
            particle.style.opacity = Math.random() * 0.3 + 0.1;

            binaryContainer.appendChild(particle);

            // 动画结束后移除
            setTimeout(() => {
                particle.remove();
            }, duration * 1000);
        }

        // 开始生成粒子
        function startBinaryRain() {
            // 初始先生成一批
            for(let i=0; i<15; i++) createBinaryParticle();
            // 然后定期生成
            particleInterval = setInterval(createBinaryParticle, 600);
        }

        function stopBinaryRain() {
            clearInterval(particleInterval);
            // 可选：渐隐清除现有粒子
            // binaryContainer.style.opacity = 0; 
        }


        // --- 交互逻辑 ---
        const btn = document.getElementById('fingerBtn');
        const ritual = document.getElementById('ritualLayer');
        const result = document.getElementById('resultLayer');
        let pressTimer;

        btn.addEventListener('touchstart', startRitual, {passive: false});
        btn.addEventListener('mousedown', startRitual);
        btn.addEventListener('touchend', endRitual);
        btn.addEventListener('mouseup', endRitual);
        btn.addEventListener('mouseleave', endRitual);

        function startRitual(e) {
            e.preventDefault();
            btn.style.transform = "scale(0.95)";
            btn.style.borderColor = "#fff";
            document.querySelector('.fingerprint-icon').style.color = "#fff";
            pressTimer = setTimeout(revealResult, 1500);
        }

        function endRitual() {
            clearTimeout(pressTimer);
            btn.style.transform = "scale(1)";
            btn.style.borderColor = "rgba(191, 149, 63, 0.3)";
            document.querySelector('.fingerprint-icon').style.color = "#bf953f";
        }

        function revealResult() {
            stopBinaryRain(); // 停止生成粒子
            ritual.style.opacity = '0';
            setTimeout(() => {
                ritual.style.display = 'none';
                result.style.display = 'block';
                requestAnimationFrame(() => {
                    result.style.opacity = '1';
                    result.style.transform = 'translateY(0)';
                    runNumberAnimation();
                });
            }, 800);
            // 填充数据(省略详细代码，与上版相同)...
            document.getElementById('mainKeyword').innerText = aiData.fortune_report.keyword;
            document.getElementById('userTag').innerText = aiData.fortune_report.user_tag;
            document.getElementById('overviewText').innerText = aiData.fortune_report.analysis.overview;
        }

        function runNumberAnimation() { /* (省略，与上版相同) */ 
             document.getElementById('scoreVal').innerText = aiData.fortune_report.score;
        }

        // 页面加载后启动特效
        startBinaryRain();

    </script>
</body>
</html>