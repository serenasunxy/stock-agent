import os, re, json, requests
from datetime import datetime
import pytz

API_KEY = os.environ["ANTHROPIC_API_KEY"]
PST = pytz.timezone("America/Los_Angeles")
now = datetime.now(PST)
date_cn = now.strftime("%Y年%m月%d日")
weekday = ["周一","周二","周三","周四","周五","周六","周日"][now.weekday()]
print(f"🕘 {now.strftime('%Y-%m-%d %H:%M PST')}")

# ── 一次调用，搜索后生成所有数据 ─────────────────────
SYSTEM = f"""你是专业美股分析师，今天是{date_cn}{weekday} PST上午9点。
用网络搜索工具获取今日最新市场数据，然后返回一个包含所有模块的JSON对象。

返回格式（严格按此结构，只返回JSON，不要任何其他文字）：
{{
  "market": {{
    "sp500_val": "X,XXX.XX",
    "sp500_chg": "+X.XX%",
    "sp500_up": true,
    "nasdaq_val": "XX,XXX.XX",
    "nasdaq_chg": "-X.XX%",
    "nasdaq_up": false,
    "vix_val": "XX.X",
    "vix_label": "偏紧张",
    "sentiment_val": "XX",
    "sentiment_label": "恐惧区间"
  }},
  "signals": [
    {{"color": "dr", "text": "信号内容70字内", "url": "真实新闻URL或空字符串"}}
  ],
  "opinion": {{
    "tendency": "市场倾向一句话",
    "opportunity": "今日机会一句话",
    "risk": "今日风险一句话",
    "weekly": "本周重点一句话"
  }},
  "news": [
    {{"source": "Bloomberg", "time": "2h前", "impact": "高影响", "title": "新闻标题", "analysis": "深度分析100字", "tags": ["标签1","标签2"], "url": "URL"}}
  ],
  "sectors": [
    {{"name": "AI算力", "badge": "爆热", "pct": "+X.X%", "color": "green", "desc": "描述20字内", "tickers": ["NVDA","AMD","SMH"]}}
  ],
  "darkhorses": [
    {{"ticker": "TICK", "name": "公司名", "badge": "强信号", "badgeColor": "bg", "analysis": "分析100字", "tags": ["标签1","标签2"], "url": "URL"}}
  ],
  "holdings": [
    {{"ticker": "NVDA", "price": "$XXX.XX", "change": "+X.X%", "direction": "up", "rec": "持有", "note": "简短说明"}}
  ],
  "schedule": {{
    "week_events": [{{"day": "周X 时间", "desc": "事件描述", "badge": "关键", "badgeColor": "br"}}],
    "upcoming": [{{"day": "X月X日", "desc": "事件描述", "badge": "标签", "badgeColor": "bp"}}]
  }}
}}

规则：
- signals: 5条，color用 dr/dp/da/dg/db
- news: 4条，impact用 高影响/中影响/正面
- sectors: 固定8个板块：AI算力、卫星&航天、核能、消费科技、能源/天然气、云计算/SaaS、医疗/GLP-1、金融/加密
  badge用 爆热/升温/潜力/稳健/稳升/政策加速/IPO热/震荡，color用 green/blue/amber/teal/purple/red
- darkhorses: 4条，badgeColor用 bg/bp/ba/bt
- holdings: 必须包含这11个ticker：REA META VRT DXYZ AMD DRAM RKLB ASTS NVDA NASA INTC
  direction用 up/down/flat，rec用 加仓/持有/减仓/观察
- schedule: week_events 5条本周事件，upcoming 3-4条近期重要日期
  badgeColor用 br/ba/bg/bp"""

resp = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    json={
        "model": "claude-sonnet-4-6",
        "max_tokens": 8000,
        "system": SYSTEM,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        "messages": [{"role": "user", "content": f"今天是{date_cn}{weekday}，请搜索今日最新美股数据，然后生成完整的JSON数据对象。"}],
    },
    timeout=180,
)

print(f"API status: {resp.status_code}")
if resp.status_code != 200:
    print("Error:", resp.json())
    exit(1)

raw = "".join(b.get("text","") for b in resp.json().get("content",[]) if b.get("type")=="text")
raw = re.sub(r"```json|```", "", raw).strip()
print("Raw preview:", raw[:200])

try:
    d = json.loads(raw)
except:
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if m:
        try: d = json.loads(m.group())
        except: print("❌ JSON parse failed"); exit(1)
    else:
        print("❌ No JSON found"); exit(1)

print(f"✅ Parsed: {list(d.keys())}")

# ════════════════════════════════════════════════
# UPDATE HTML
# ════════════════════════════════════════════════
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

def esc(s): return str(s).replace("<","&lt;").replace(">","&gt;")

# ── date ─────────────────────────────────────────────
html = re.sub(
    r"\d{4}年\d{1,2}月\d{1,2}日 · PST 09:00 自动刷新 · Claude AI 驱动",
    f"{date_cn} · PST 09:00 自动刷新 · Claude AI 驱动", html
)

# ── market metrics ────────────────────────────────────
m = d.get("market", {})
if m:
    u1 = m.get("sp500_up", True); u2 = m.get("nasdaq_up", False)
    gc = lambda u: "var(--green)" if u else "var(--red)"
    ar = lambda u: "▲" if u else "▼"
    new_mets = f'''  <div class="mets">
    <div class="met"><div class="ml">S&P 500</div><div class="mv">{m.get("sp500_val","--")}</div><div class="ms" style="color:{gc(u1)}">{ar(u1)} {m.get("sp500_chg","")}</div></div>
    <div class="met"><div class="ml">NASDAQ</div><div class="mv">{m.get("nasdaq_val","--")}</div><div class="ms" style="color:{gc(u2)}">{ar(u2)} {m.get("nasdaq_chg","")}</div></div>
    <div class="met"><div class="ml">VIX 恐慌</div><div class="mv">{m.get("vix_val","--")}</div><div class="ms" style="color:var(--amber)">{m.get("vix_label","")}</div></div>
    <div class="met"><div class="ml">市场情绪</div><div class="mv">{m.get("sentiment_val","--")}</div><div class="ms" style="color:var(--green)">{m.get("sentiment_label","")}</div></div>
  </div>'''
    html = re.sub(r'<div class="mets">.*?</div>\s*</div>\s*\n\s*<div class="tabwrap">',
                  new_mets + '\n\n  <div class="tabwrap">', html, flags=re.DOTALL)
    print("  ✅ market")

# ── 今日简报 signals ──────────────────────────────────
signals = d.get("signals", [])
if signals:
    rows = ""
    for s in signals:
        t = esc(s.get("text","")); u = s.get("url","").strip(); c = s.get("color","db")
        if u and u.startswith("http"):
            rows += f'\n      <a class="news-link" href="{u}" target="_blank" rel="noopener"><div class="row row-link"><div class="dot {c}"></div><div>{t}</div></div></a>'
        else:
            rows += f'\n      <div class="row"><div class="dot {c}"></div><div>{t}</div></div>'
    M1='今日最重要信号</div>'; M2='\n    </div>\n    <div class="card">\n      <div class="ctitle"><i class="ti ti-brain"'
    i1=html.find(M1); i2=html.find(M2,i1)
    if i1>=0 and i2>=0:
        html=html[:i1+len(M1)]+rows+html[i2:]
        print("  ✅ 今日简报")

# ── AI操盘观点 ────────────────────────────────────────
op = d.get("opinion", {})
if op:
    new_op = f'''      <div class="arow"><span class="al">市场倾向</span><span class="av">{esc(op.get("tendency",""))}</span></div>
      <div class="arow"><span class="al">今日机会</span><span class="av" style="color:var(--green)">{esc(op.get("opportunity",""))}</span></div>
      <div class="arow"><span class="al">今日风险</span><span class="av" style="color:var(--red)">{esc(op.get("risk",""))}</span></div>
      <div class="arow"><span class="al">本周重点</span><span class="av">{esc(op.get("weekly",""))}</span></div>'''
    html = re.sub(r'(AI 操盘手今日观点</div>\n)(.*?)(</div>\n  </div>)',
                  r'\1'+new_op+r'\n    \3', html, flags=re.DOTALL, count=1)
    print("  ✅ AI观点")

# ── 新闻解读 ──────────────────────────────────────────
news = d.get("news", [])
if news:
    imap={"高影响":"br","中影响":"ba","低影响":"bgr","正面":"bg"}
    nh=""
    for n in news:
        bc=imap.get(n.get("impact","中影响"),"ba"); u=n.get("url","").strip()
        tags="".join(f'<span class="ntag">{esc(t)}</span>' for t in n.get("tags",[]))
        oc=f' style="cursor:pointer" onclick="window.open(\'{u}\',\'_blank\')"' if u and u.startswith("http") else ""
        nh+=f'  <div class="ni"{oc}>\n    <div class="nm"><span class="ns">{esc(n.get("source","")).upper()}</span><span style="font-size:10px;color:var(--text2)">{esc(n.get("time",""))}</span><span class="b {bc}">{esc(n.get("impact",""))}</span></div>\n    <div class="nt">{esc(n.get("title",""))}</div>\n    <div class="na">{esc(n.get("analysis",""))}</div>\n    <div class="ntags">{tags}</div>\n  </div>\n'
    i1=html.find('<div id="news" class="panel">'); i2=html.find('<div id="sectors" class="panel">',i1)
    if i1>=0 and i2>=0:
        html=html[:i1+len('<div id="news" class="panel">')] + "\n" + nh + "\n" + html[i2:]
        print("  ✅ 新闻解读")

# ── 板块全景 ──────────────────────────────────────────
sectors = d.get("sectors", [])
if sectors:
    cmap={"green":("var(--green)","#97C459"),"blue":("var(--blue)","#85B7EB"),"amber":("var(--amber)","#FAC775"),
          "teal":("var(--teal)","#9FE1CB"),"purple":("var(--purple)","#CECBF6"),"red":("var(--red)","#F09595")}
    bmap={"爆热":"bg","升温":"bb","潜力":"ba","稳健":"bt","稳升":"bp","政策加速":"bt","IPO热":"bp","震荡":"ba"}
    sh=""
    for s in sectors:
        tc,bc=cmap.get(s.get("color","blue"),("var(--blue)","#85B7EB"))
        bdg=s.get("badge","升温"); bcls=bmap.get(bdg,"bb")
        tks="".join(f'<span class="sc">{esc(t)}</span>' for t in s.get("tickers",[]))
        sh+=f'    <div class="scard" style="border-color:{bc}"><div class="sh"><span class="sn">{esc(s.get("name",""))}</span><span class="b {bcls}">{bdg}</span></div><div class="sv" style="color:{tc}">{esc(s.get("pct",""))}</div><div class="sd">{esc(s.get("desc",""))}</div><div class="stars">{tks}</div></div>\n'
    sp=html.find('<div id="sectors" class="panel">')
    i1=html.find('<div class="sgrid">',sp); i2=html.find('</div>\n    <div class="card">\n      <div class="ctitle"><i class="ti ti-chart-bar"',i1)
    if i1>=0 and i2>=0:
        html=html[:i1+len('<div class="sgrid">')] + "\n" + sh + "    " + html[i2:]
        print("  ✅ 板块全景")

# ── 黑马雷达 ──────────────────────────────────────────
darkhorses = d.get("darkhorses", [])
if darkhorses:
    bcmap={"bg":"bg","bp":"bp","ba":"ba","bt":"bt"}
    dh=""
    for h in darkhorses:
        bc=bcmap.get(h.get("badgeColor","ba"),"ba"); tk=esc(h.get("ticker",""))
        tags="".join(f'<span class="ntag">{esc(t)}</span>' for t in h.get("tags",[]))
        pt=f'用 serenity-skill 深度分析 {tk} 在产业链中的位置和投资逻辑'
        dh+=f'    <div class="card">\n      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:9px"><span style="font-size:14px;font-weight:500">{tk} · {esc(h.get("name",""))}</span><span class="b {bc}">{esc(h.get("badge",""))}</span></div>\n      <div class="abox">{esc(h.get("analysis",""))}</div>\n      <div class="ntags">{tags}</div>\n      <button class="askbtn" onclick="openSerenity(\'{pt}\')"><i class="ti ti-sparkles"></i> Serenity Skill 分析</button>\n    </div>\n'
    i1=html.find('<div id="darkhorses" class="panel">'); i2=html.find('<div id="trump" class="panel">',i1)
    if i1>=0 and i2>=0:
        lbl='    <div class="ctitle" style="margin-bottom:9px"><i class="ti ti-horse"></i>黑马雷达 · AI 筛选异动个股</div>\n'
        html=html[:i1+len('<div id="darkhorses" class="panel">')] + "\n" + lbl + dh + "\n  " + html[i2:]
        print("  ✅ 黑马雷达")

# ── 我的持仓 ──────────────────────────────────────────
holdings = d.get("holdings", [])
if holdings:
    info={
        "REA":{"name":"Rare Earths Americas","shares":"3股"},
        "META":{"name":"Meta","shares":"32股"},
        "VRT":{"name":"Vertiv","shares":"1股"},
        "DXYZ":{"name":"Destiny Tech100","shares":"29股"},
        "AMD":{"name":"AMD","shares":"2股"},
        "DRAM":{"name":"Roundhill Memory ETF","shares":"10股"},
        "RKLB":{"name":"Rocket Lab USA","shares":"18股"},
        "ASTS":{"name":"AST SpaceMobile","shares":"36股"},
        "NVDA":{"name":"英伟达","shares":"10股"},
        "NASA":{"name":"Tema Space ETF","shares":"30股"},
        "INTC":{"name":"Intel","shares":"10股"},
    }
    rstyle={"加仓":"background:var(--gbg);color:var(--green)","持有":"background:var(--abg);color:var(--amber)",
            "减仓":"background:var(--rbg);color:var(--red)","观察":"background:var(--abg);color:var(--amber)"}
    hh=""
    for h in holdings:
        tk=h.get("ticker",""); inf=info.get(tk,{"name":tk,"shares":""})
        dr=h.get("direction","flat")
        cc="var(--green)" if dr=="up" else "var(--red)" if dr=="down" else "var(--text2)"
        ar="▲" if dr=="up" else "▼" if dr=="down" else "◆"
        rec=h.get("rec","持有"); rs=rstyle.get(rec,rstyle["持有"])
        fs="font-size:9px" if len(tk)>4 else ""
        hh+=f'    <div class="hcard"><div class="htk" style="{fs}">{tk}</div><div class="hinfo"><div class="hn">{inf["name"]} · {inf["shares"]}</div><div class="hd">{esc(h.get("note",""))}</div></div><div class="hrt"><div class="hp">{esc(h.get("price","--"))}</div><div class="hc" style="color:{cc}">{ar} {esc(h.get("change","--"))}</div></div><span class="rbdg" style="{rs}">{rec}</span></div>\n'
    sc=f'    <div class="card">\n      <div class="ctitle"><i class="ti ti-chart-pie"></i>我的持仓 · 实时数据 · {date_cn}</div>\n      <div class="arow"><span class="al">组合特征</span><span class="av">AI算力 + 商业航天 + 稀土/内存 多主线并行，高风险高弹性组合。</span></div>\n    </div>\n'
    i1=html.find('<div id="holdings" class="panel">'); i2=html.find('<div id="schedule" class="panel">',i1)
    if i1>=0 and i2>=0:
        html=html[:i1+len('<div id="holdings" class="panel">')] + "\n" + sc + hh + "\n  " + html[i2:]
        print("  ✅ 我的持仓")

# ── 本周日程 ──────────────────────────────────────────
sched = d.get("schedule", {})
if sched:
    bcmap2={"br":"br","ba":"ba","bg":"bg","bp":"bp"}
    sc='    <div class="card">\n      <div class="ctitle"><i class="ti ti-calendar-event"></i>本周关键事件</div>\n'
    for e in sched.get("week_events",[]):
        bc=bcmap2.get(e.get("badgeColor","ba"),"ba"); bdg=esc(e.get("badge",""))
        bh=f'<span style="font-size:10px;color:var(--text2)">{bdg}</span>' if bdg=="中等影响" else f'<span class="b {bc}">{bdg}</span>'
        sc+=f'      <div class="srow"><span class="stime">{esc(e.get("day",""))}</span><span style="flex:1">{esc(e.get("desc",""))}</span>{bh}</div>\n'
    sc+='    </div>\n'
    if sched.get("upcoming"):
        sc+='    <div class="card">\n      <div class="ctitle"><i class="ti ti-rocket"></i>近期重要日期</div>\n'
        for e in sched.get("upcoming",[]):
            bc=bcmap2.get(e.get("badgeColor","bp"),"bp")
            sc+=f'      <div class="srow"><span class="stime">{esc(e.get("day",""))}</span><span style="flex:1">{esc(e.get("desc",""))}</span><span class="b {bc}">{esc(e.get("badge",""))}</span></div>\n'
        sc+='    </div>\n'
    sc+='    <div class="card">\n      <div class="ctitle"><i class="ti ti-clock"></i>自动刷新计划</div>\n      <div class="row"><div class="dot db"></div><div style="font-size:12px">每日 <strong>PST 09:00</strong> — 全量刷新所有模块</div></div>\n      <div class="row"><div class="dot dg"></div><div style="font-size:12px">财报后 <strong>30分钟内</strong> — 自动触发专项分析</div></div>\n      <div class="row"><div class="dot da"></div><div style="font-size:12px">异动监控 — VIX突变 / 个股超5% 触发提醒</div></div>\n    </div>'
    i1=html.find('<div id="schedule" class="panel">'); i2=html.find('<div id="serenity" class="panel">',i1)
    if i1>=0 and i2>=0:
        html=html[:i1+len('<div id="schedule" class="panel">')] + "\n" + sc + "\n\n  " + html[i2:]
        print("  ✅ 本周日程")

with open("index.html","w",encoding="utf-8") as f:
    f.write(html)
print(f"\n✅ 全部完成 — {date_cn}")
