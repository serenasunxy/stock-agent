import os, re, json, requests
from datetime import datetime
import pytz

# ── Config ───────────────────────────────────────────
API_KEY = os.environ["ANTHROPIC_API_KEY"]
PST     = pytz.timezone("America/Los_Angeles")
now     = datetime.now(PST)
date_cn = now.strftime("%Y年%m月%d日")
weekday = ["周一","周二","周三","周四","周五","周六","周日"][now.weekday()]

print(f"🕘 Running at {now.strftime('%Y-%m-%d %H:%M PST')}")

# ── Call Claude API ───────────────────────────────────
system_prompt = f"""你是专业美股分析师，今天是{date_cn}{weekday} PST。
给出今日最重要的5条市场信号，每条70字内，覆盖：财报/业绩、Fed/宏观、重大事件、板块机会、风险提示。
返回纯JSON数组，格式：
[{{"color":"dr","text":"内容","url":"真实新闻URL或空字符串"}}]
color选项：dr=红(利空/风险) dp=紫(重大事件) da=橙(警示) dg=绿(利好) db=蓝(宏观数据)
只返回JSON数组，不要任何其他文字、代码块标记。"""

resp = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    json={
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": f"今天是{date_cn}，请给出今日5条最新最重要的美股市场信号。"}],
    },
    timeout=60,
)

data = resp.json()
print("API status:", resp.status_code)
raw = "".join(c.get("text", "") for c in data.get("content", []))
raw = re.sub(r"```json|```", "", raw).strip()
print("Raw response:", raw[:300])

signals = json.loads(raw)
print(f"✅ Got {len(signals)} signals")

# ── Build HTML rows ───────────────────────────────────
rows_html = ""
for s in signals:
    color = s.get("color", "db")
    text  = s.get("text", "").replace("<", "&lt;").replace(">", "&gt;")
    url   = s.get("url", "").strip()
    if url and url.startswith("http"):
        rows_html += f'\n    <a class="news-link" href="{url}" target="_blank" rel="noopener"><div class="row row-link"><div class="dot {color}"></div><div>{text}</div></div></a>'
    else:
        rows_html += f'\n    <div class="row"><div class="dot {color}"></div><div>{text}</div></div>'

# ── Update index.html ─────────────────────────────────
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Update date string
html = re.sub(
    r"\d{4}年\d{1,2}月\d{1,2}日 · PST 09:00 自动刷新 · Claude AI 驱动",
    f"{date_cn} · PST 09:00 自动刷新 · Claude AI 驱动",
    html,
)

# 2. Replace signal rows (between ctitle div and the AI观点 card)
MARKER_START = "今日最重要信号</div>"
MARKER_END   = '<div class="card">\n    <div class="ctitle"><i class="ti ti-brain"'

start_idx = html.find(MARKER_START)
end_idx   = html.find(MARKER_END, start_idx)

if start_idx >= 0 and end_idx >= 0:
    html = html[:start_idx + len(MARKER_START)] + rows_html + "\n  </div>\n\n  " + html[end_idx:]
    print("✅ Signals injected into HTML")
else:
    print("⚠️  Could not find signal markers, skipping injection")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Done — {date_cn} 简报已更新")
