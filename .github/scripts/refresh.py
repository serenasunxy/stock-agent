import os, re, json, requests
from datetime import datetime
import pytz

API_KEY = os.environ["ANTHROPIC_API_KEY"]
PST     = pytz.timezone("America/Los_Angeles")
now     = datetime.now(PST)
date_cn = now.strftime("%Y年%m月%d日")
weekday = ["周一","周二","周三","周四","周五","周六","周日"][now.weekday()]

print(f"🕘 {now.strftime('%Y-%m-%d %H:%M PST')}")

def call_claude(prompt, system, max_tokens=2000, use_search=True):
    tools = [{"type": "web_search_20250305", "name": "web_search"}] if use_search else []
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "system": system,
              "tools": tools, "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    data = resp.json()
    if resp.status_code != 200:
        print(f"API error {resp.status_code}:", data)
        return None
    raw = "".join(b.get("text","") for b in data.get("content",[]) if b.get("type")=="text")
    raw = re.sub(r"```json|```","",raw).strip()
    return raw

def parse_json(raw):
    try:
        return json.loads(raw)
    except:
        m = re.search(r'[\[{].*[\]}]', raw, re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
    return None

print("📡 Fetching all sections...")

# ── 1. 今日简报 signals ──────────────────────────────
print("  [1/8] 今日简报...")
raw1 = call_claude(
    f"今天是{date_cn}{weekday}，搜索今日最新美股市场动态，给出5条最重要信号。",
    f"""你是专业美股分析师，今天是{date_cn}{weekday} PST。搜索今日最新数据后给出5条市场信号，每条70字内。
返回纯JSON数组：[{{"color":"dr","text":"内容","url":"新闻URL或空"}}]
color: dr=红(利空) dp=紫(重大事件) da=橙(警示) dg=绿(利好) db=蓝(宏观)
只返回JSON数组。"""
)
signals = parse_json(raw1) if raw1 else None
print(f"  → {len(signals) if signals else 0} signals")

# ── 2. 新闻解读 ──────────────────────────────────────
print("  [2/8] 新闻解读...")
raw2 = call_claude(
    f"今天是{date_cn}{weekday}，搜索今日最重要的4条美股新闻，每条要有深度分析。",
    f"""你是专业美股分析师，今天是{date_cn}{weekday} PST。搜索今日最新新闻后返回4条深度解读。
返回纯JSON数组：[{{"source":"来源","time":"Xh前","impact":"高影响|中影响|低影响|正面","title":"新闻标题","analysis":"深度分析100字","tags":["标签1","标签2"],"url":"新闻URL"}}]
只返回JSON数组。"""
)
news_items = parse_json(raw2) if raw2 else None
print(f"  → {len(news_items) if news_items else 0} news")

# ── 3. 板块全景 ──────────────────────────────────────
print("  [3/8] 板块全景...")
raw3 = call_claude(
    f"今天是{date_cn}{weekday}，搜索今日美股各板块涨跌和资金流向数据。",
    f"""你是专业美股分析师，今天是{date_cn}{weekday} PST。搜索今日板块数据后返回8个主要板块情况。
返回纯JSON数组：[{{"name":"板块名","badge":"爆热|升温|潜力|稳健|稳升|政策加速|IPO热|震荡","pct":"+X.X%","color":"green|blue|amber|teal|purple|red","desc":"简短描述20字","tickers":["TICK1","TICK2","TICK3"]}}]
板块固定为：AI算力、卫星&航天、核能、消费科技、能源/天然气、云计算/SaaS、医疗/GLP-1、金融/加密
只返回JSON数组。"""
)
sectors = parse_json(raw3) if raw3 else None
print(f"  → {len(sectors) if sectors else 0} sectors")

# ── 4. 黑马雷达 ──────────────────────────────────────
print("  [4/8] 黑马雷达...")
raw4 = call_claude(
    f"今天是{date_cn}{weekday}，搜索今日美股异动黑马个股，找4个最值得关注的。",
    f"""你是专业美股分析师，今天是{date_cn}{weekday} PST。搜索今日异动个股后返回4个黑马。
返回纯JSON数组：[{{"ticker":"TICK","name":"公司名","badge":"强信号|机构新宠|资金暗流|医疗黑马|航天黑马","badgeColor":"bg|bp|ba|bt","analysis":"分析100字","tags":["标签1","标签2","标签3"],"url":"新闻URL"}}]
只返回JSON数组。"""
)
darkhorses = parse_json(raw4) if raw4 else None
print(f"  → {len(darkhorses) if darkhorses else 0} darkhorses")

# ── 5. 本周日程 ──────────────────────────────────────
print("  [5/8] 本周日程...")
raw5 = call_claude(
    f"今天是{date_cn}{weekday}，搜索本周美股重要财报、Fed事件、宏观数据发布日程。",
    f"""你是专业美股分析师，今天是{date_cn}{weekday} PST。搜索本周事件后返回日程。
返回纯JSON对象：{{"week_events":[{{"day":"周X 时间","desc":"事件描述","badge":"关键|高关注|今日|中等影响|已完成","badgeColor":"br|ba|ba|text2|bg"}}],"upcoming":[{{"day":"日期","desc":"事件描述","badge":"标签","badgeColor":"bp|ba|br"}}]}}
只返回JSON对象。"""
)
schedule = parse_json(raw5) if raw5 else None
print(f"  → schedule {'ok' if schedule else 'failed'}")

# ── 6. 我的持仓实时价格 ──────────────────────────────
print("  [6/8] 持仓价格...")
holdings_list = ["REA","META","VRT","DXYZ","AMD","DRAM","RKLB","ASTS","NVDA","NASA","INTC"]
raw6 = call_claude(
    f"今天是{date_cn}，搜索以下股票今日最新价格和涨跌幅：{', '.join(holdings_list)}",
    f"""你是股票数据助手，今天是{date_cn} PST。搜索这些股票的最新价格后返回数据。
返回纯JSON数组：[{{"ticker":"TICK","price":"$XXX.XX","change":"+X.X%","direction":"up|down|flat","rec":"加仓|持有|减仓|观察","note":"一句话说明"}}]
只返回JSON数组。"""
)
holdings_data = parse_json(raw6) if raw6 else None
print(f"  → {len(holdings_data) if holdings_data else 0} holdings")

# ── 7. AI操盘手观点 ──────────────────────────────────
print("  [7/8] AI操盘手观点...")
raw7 = call_claude(
    f"今天是{date_cn}{weekday}，基于今日市场情况给出操盘建议。",
    f"""你是专业美股操盘手，今天是{date_cn}{weekday} PST。搜索今日市场后给出4条操盘观点。
返回纯JSON对象：{{"tendency":"市场倾向一句话","opportunity":"今日机会一句话","risk":"今日风险一句话","weekly":"本周重点一句话"}}
只返回JSON对象。"""
)
opinion = parse_json(raw7) if raw7 else None
print(f"  → opinion {'ok' if opinion else 'failed'}")

# ── 8. 顶部市场数据 ──────────────────────────────────
print("  [8/8] 市场数据...")
raw8 = call_claude(
    f"今天是{date_cn}，搜索今日S&P500、NASDAQ、VIX的最新数据。",
    f"""搜索今日市场数据后返回。
返回纯JSON对象：{{"sp500_val":"X,XXX","sp500_chg":"+X.XX%","sp500_up":true,"nasdaq_val":"XX,XXX","nasdaq_chg":"-X.XX%","nasdaq_up":false,"vix_val":"XX.X","vix_label":"中性|偏紧张|恐慌|贪婪","sentiment_val":"XX","sentiment_label":"贪婪区间|恐惧区间|极度贪婪|极度恐惧"}}
只返回JSON对象。"""
)
market = parse_json(raw8) if raw8 else None
print(f"  → market {'ok' if market else 'failed'}")

print("\n📝 Building HTML...")

# ════════════════════════════════════════════════════
# BUILD HTML
# ════════════════════════════════════════════════════
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# ── Update date ──────────────────────────────────────
html = re.sub(
    r"\d{4}年\d{1,2}月\d{1,2}日 · PST 09:00 自动刷新 · Claude AI 驱动",
    f"{date_cn} · PST 09:00 自动刷新 · Claude AI 驱动",
    html,
)

# ── Update market metrics ────────────────────────────
if market:
    sp_color = "var(--green)" if market.get("sp500_up", True) else "var(--red)"
    sp_arrow = "▲" if market.get("sp500_up", True) else "▼"
    nd_color = "var(--green)" if market.get("nasdaq_up", False) else "var(--red)"
    nd_arrow = "▲" if market.get("nasdaq_up", False) else "▼"
    new_metrics = f'''  <div class="mets">
    <div class="met"><div class="ml">S&P 500</div><div class="mv">{market.get("sp500_val","5,304")}</div><div class="ms" style="color:{sp_color}">{sp_arrow} {market.get("sp500_chg","+0.73%")}</div></div>
    <div class="met"><div class="ml">NASDAQ</div><div class="mv">{market.get("nasdaq_val","16,780")}</div><div class="ms" style="color:{nd_color}">{nd_arrow} {market.get("nasdaq_chg","-0.21%")}</div></div>
    <div class="met"><div class="ml">VIX 恐慌</div><div class="mv">{market.get("vix_val","18.4")}</div><div class="ms" style="color:var(--amber)">{market.get("vix_label","中性偏紧张")}</div></div>
    <div class="met"><div class="ml">市场情绪</div><div class="mv">{market.get("sentiment_val","64")}</div><div class="ms" style="color:var(--green)">{market.get("sentiment_label","贪婪区间")}</div></div>
  </div>'''
    html = re.sub(r'<div class="mets">.*?</div>\s*</div>\s*\n\s*<div class="tabwrap">', new_metrics + '\n\n  <div class="tabwrap">', html, flags=re.DOTALL)
    print("  ✅ market metrics")

# ── Update 今日简报 signals ──────────────────────────
if signals:
    rows_html = ""
    for s in signals:
        color = s.get("color","db")
        text  = s.get("text","").replace("<","&lt;").replace(">","&gt;")
        url   = s.get("url","").strip()
        if url and url.startswith("http"):
            rows_html += f'\n      <a class="news-link" href="{url}" target="_blank" rel="noopener"><div class="row row-link"><div class="dot {color}"></div><div>{text}</div></div></a>'
        else:
            rows_html += f'\n      <div class="row"><div class="dot {color}"></div><div>{text}</div></div>'
    M1 = '今日最重要信号</div>'
    M2 = '\n    </div>\n    <div class="card">\n      <div class="ctitle"><i class="ti ti-brain"'
    i1 = html.find(M1); i2 = html.find(M2, i1)
    if i1 >= 0 and i2 >= 0:
        html = html[:i1+len(M1)] + rows_html + html[i2:]
        print("  ✅ 今日简报 signals")

# ── Update AI操盘手观点 ──────────────────────────────
if opinion:
    opp_color = "var(--green)" if "机会" in str(opinion.get("opportunity","")) or "看多" in str(opinion.get("opportunity","")) else "var(--green)"
    risk_color = "var(--red)"
    new_opinion = f'''      <div class="arow"><span class="al">市场倾向</span><span class="av">{opinion.get("tendency","")}</span></div>
      <div class="arow"><span class="al">今日机会</span><span class="av" style="color:var(--green)">{opinion.get("opportunity","")}</span></div>
      <div class="arow"><span class="al">今日风险</span><span class="av" style="color:var(--red)">{opinion.get("risk","")}</span></div>
      <div class="arow"><span class="al">本周重点</span><span class="av">{opinion.get("weekly","")}</span></div>'''
    html = re.sub(
        r'(AI 操盘手今日观点</div>\n)(.*?)(</div>\n  </div>)',
        r'\1' + new_opinion + r'\n    \3',
        html, flags=re.DOTALL, count=1
    )
    print("  ✅ AI操盘手观点")

# ── Update 新闻解读 ──────────────────────────────────
if news_items:
    impact_map = {"高影响":"br","中影响":"ba","低影响":"bgr","正面":"bg"}
    news_html = ""
    for n in news_items:
        impact = n.get("impact","中影响")
        badge_cls = impact_map.get(impact,"ba")
        url = n.get("url","").strip()
        tags_html = "".join(f'<span class="ntag">{t}</span>' for t in n.get("tags",[]))
        src = n.get("source","").upper()
        time_ = n.get("time","")
        title = n.get("title","").replace("<","&lt;").replace(">","&gt;")
        analysis = n.get("analysis","").replace("<","&lt;").replace(">","&gt;")
        onclick = f' style="cursor:pointer" onclick="window.open(\'{url}\',\'_blank\')"' if url and url.startswith("http") else ""
        news_html += f'''  <div class="ni"{onclick}>
    <div class="nm"><span class="ns">{src}</span><span style="font-size:10px;color:var(--text2)">{time_}</span><span class="b {badge_cls}">{impact}</span></div>
    <div class="nt">{title}</div>
    <div class="na">{analysis}</div>
    <div class="ntags">{tags_html}</div>
  </div>\n'''
    M_NEWS_START = '<div id="news" class="panel">'
    M_NEWS_END   = '<div id="sectors" class="panel">'
    i1 = html.find(M_NEWS_START); i2 = html.find(M_NEWS_END, i1)
    if i1 >= 0 and i2 >= 0:
        html = html[:i1+len(M_NEWS_START)] + "\n" + news_html + "\n" + html[i2:]
        print("  ✅ 新闻解读")

# ── Update 板块全景 ──────────────────────────────────
if sectors:
    color_map = {
        "green": ("var(--green)","#97C459"),
        "blue":  ("var(--blue)","#85B7EB"),
        "amber": ("var(--amber)","#FAC775"),
        "teal":  ("var(--teal)","#9FE1CB"),
        "purple":("var(--purple)","#CECBF6"),
        "red":   ("var(--red)","#F09595"),
    }
    badge_cls_map = {"爆热":"bg","升温":"bb","潜力":"ba","稳健":"bt","稳升":"bp","政策加速":"bt","IPO热":"bp","震荡":"ba"}
    sectors_html = ""
    for s in sectors:
        col_key = s.get("color","blue")
        text_color, border_color = color_map.get(col_key, ("var(--blue)","#85B7EB"))
        badge = s.get("badge","升温")
        badge_cls = badge_cls_map.get(badge,"bb")
        tickers = "".join(f'<span class="sc">{t}</span>' for t in s.get("tickers",[]))
        pct = s.get("pct","+0%")
        sectors_html += f'''    <div class="scard" style="border-color:{border_color}"><div class="sh"><span class="sn">{s.get("name","")}</span><span class="b {badge_cls}">{badge}</span></div><div class="sv" style="color:{text_color}">{pct}</div><div class="sd">{s.get("desc","")}</div><div class="stars">{tickers}</div></div>\n'''
    M_SEC_START = '<div class="sgrid">'
    M_SEC_END   = '</div>\n    <div class="card">\n      <div class="ctitle"><i class="ti ti-chart-bar"'
    i1 = html.find(M_SEC_START, html.find('<div id="sectors"'))
    i2 = html.find(M_SEC_END, i1)
    if i1 >= 0 and i2 >= 0:
        html = html[:i1+len(M_SEC_START)] + "\n" + sectors_html + "    " + html[i2:]
        print("  ✅ 板块全景")

# ── Update 黑马雷达 ──────────────────────────────────
if darkhorses:
    badge_cls_map2 = {"bg":"bg","bp":"bp","ba":"ba","bt":"bt"}
    dh_html = ""
    for d in darkhorses:
        badge_cls = badge_cls_map2.get(d.get("badgeColor","ba"),"ba")
        tags_html = "".join(f'<span class="ntag">{t}</span>' for t in d.get("tags",[]))
        url = d.get("url","").strip()
        prompt_txt = f'用 serenity-skill 深度分析 {d.get("ticker","")} 在产业链中的位置和投资逻辑'
        analysis = d.get("analysis","").replace("<","&lt;").replace(">","&gt;")
        dh_html += f'''    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:9px"><span style="font-size:14px;font-weight:500">{d.get("ticker","")} · {d.get("name","")}</span><span class="b {badge_cls}">{d.get("badge","")}</span></div>
      <div class="abox">{analysis}</div>
      <div class="ntags">{tags_html}</div>
      <button class="askbtn" onclick="openSerenity('{prompt_txt}')"><i class="ti ti-sparkles"></i> Serenity Skill 分析</button>
    </div>\n'''
    M_DH_START = '<div id="darkhorses" class="panel">'
    M_DH_END   = '<div id="trump" class="panel">'
    i1 = html.find(M_DH_START); i2 = html.find(M_DH_END, i1)
    if i1 >= 0 and i2 >= 0:
        label = '    <div class="ctitle" style="margin-bottom:9px"><i class="ti ti-horse"></i>黑马雷达 · AI 筛选异动个股</div>\n'
        html = html[:i1+len(M_DH_START)] + "\n" + label + dh_html + "\n  " + html[i2:]
        print("  ✅ 黑马雷达")

# ── Update 我的持仓 ──────────────────────────────────
if holdings_data:
    holdings_info = {
        "REA":  {"name":"Rare Earths Americas","shares":"3股","desc":"稀土探矿 · 美国+巴西项目"},
        "META": {"name":"Meta","shares":"32股","desc":"AI广告+Threads 5亿用户"},
        "VRT":  {"name":"Vertiv","shares":"1股","desc":"AI数据中心基础设施"},
        "DXYZ": {"name":"Destiny Tech100","shares":"29股","desc":"持有SpaceX/OpenAI等私募独角兽"},
        "AMD":  {"name":"AMD","shares":"2股","desc":"AI GPU · Meta大单"},
        "DRAM": {"name":"Roundhill Memory ETF","shares":"10股","desc":"首只内存芯片ETF"},
        "RKLB": {"name":"Rocket Lab USA","shares":"18股","desc":"Neutron火箭 · SpaceX IPO联动"},
        "ASTS": {"name":"AST SpaceMobile","shares":"36股","desc":"手机直连卫星 · BlueBird发射"},
        "NVDA": {"name":"英伟达","shares":"10股","desc":"AI算力核心"},
        "NASA": {"name":"Tema Space ETF","shares":"30股","desc":"商业航天板块整体敞口"},
        "INTC": {"name":"Intel","shares":"10股","desc":"AI转型+Google晶圆代工"},
    }
    rec_style = {
        "加仓": "background:var(--gbg);color:var(--green)",
        "持有": "background:var(--abg);color:var(--amber)",
        "减仓": "background:var(--rbg);color:var(--red)",
        "观察": "background:var(--abg);color:var(--amber)",
    }
    h_html = ""
    for h in holdings_data:
        tk = h.get("ticker","")
        info = holdings_info.get(tk, {"name":tk,"shares":"","desc":""})
        price = h.get("price","--")
        change = h.get("change","--")
        direction = h.get("direction","flat")
        chg_color = "var(--green)" if direction=="up" else "var(--red)" if direction=="down" else "var(--text2)"
        arrow = "▲" if direction=="up" else "▼" if direction=="down" else "◆"
        rec = h.get("rec","持有")
        rec_s = rec_style.get(rec, rec_style["持有"])
        note = h.get("note","").replace("<","&lt;").replace(">","&gt;")
        tk_fs = "font-size:9px" if len(tk) > 4 else ""
        h_html += f'    <div class="hcard"><div class="htk" style="{tk_fs}">{tk}</div><div class="hinfo"><div class="hn">{info["name"]} · {info["shares"]}</div><div class="hd">{note or info["desc"]}</div></div><div class="hrt"><div class="hp">{price}</div><div class="hc" style="color:{chg_color}">{arrow} {change}</div></div><span class="rbdg" style="{rec_s}">{rec}</span></div>\n'

    M_H_START = '<div id="holdings" class="panel">'
    M_H_END   = '<div id="schedule" class="panel">'
    i1 = html.find(M_H_START); i2 = html.find(M_H_END, i1)
    if i1 >= 0 and i2 >= 0:
        summary_card = f'''    <div class="card">
      <div class="ctitle"><i class="ti ti-chart-pie"></i>我的持仓 · 实时数据 · 更新于 {date_cn}</div>
      <div class="arow"><span class="al">组合特征</span><span class="av">AI算力 + 商业航天 + 稀土/内存 多主线并行。高风险高弹性组合。</span></div>
    </div>\n'''
        html = html[:i1+len(M_H_START)] + "\n" + summary_card + h_html + "\n  " + html[i2:]
        print("  ✅ 我的持仓")

# ── Update 本周日程 ──────────────────────────────────
if schedule:
    badge_color_map = {"br":"br","ba":"ba","bg":"bg","text2":"bgr","bp":"bp"}
    sched_html = '    <div class="card">\n      <div class="ctitle"><i class="ti ti-calendar-event"></i>本周关键事件</div>\n'
    for e in schedule.get("week_events",[]):
        bc = badge_color_map.get(e.get("badgeColor","ba"),"ba")
        badge_val = e.get("badge","")
        if badge_val in ["中等影响","text2"]:
            badge_html = f'<span style="font-size:10px;color:var(--text2)">{badge_val}</span>'
        else:
            badge_html = f'<span class="b {bc}">{badge_val}</span>'
        sched_html += f'      <div class="srow"><span class="stime">{e.get("day","")}</span><span style="flex:1">{e.get("desc","")}</span>{badge_html}</div>\n'
    sched_html += '    </div>\n'
    if schedule.get("upcoming"):
        sched_html += '    <div class="card">\n      <div class="ctitle"><i class="ti ti-rocket"></i>近期重要日期</div>\n'
        for e in schedule.get("upcoming",[]):
            bc = badge_color_map.get(e.get("badgeColor","bp"),"bp")
            sched_html += f'      <div class="srow"><span class="stime">{e.get("day","")}</span><span style="flex:1">{e.get("desc","")}</span><span class="b {bc}">{e.get("badge","")}</span></div>\n'
        sched_html += '    </div>\n'

    refresh_card = '''    <div class="card">
      <div class="ctitle"><i class="ti ti-clock"></i>自动刷新计划</div>
      <div class="row"><div class="dot db"></div><div style="font-size:12px">每日 <strong>PST 09:00</strong> — 全量刷新：市场数据、新闻、AI 分析、持仓建议重算</div></div>
      <div class="row"><div class="dot dg"></div><div style="font-size:12px">财报后 <strong>30分钟内</strong> — 自动触发财报专项分析</div></div>
      <div class="row"><div class="dot da"></div><div style="font-size:12px">异动监控 — VIX 突变 / 个股单日超 5% 时触发即时提醒</div></div>
    </div>'''

    M_SCH_START = '<div id="schedule" class="panel">'
    M_SCH_END   = '<div id="serenity" class="panel">'
    i1 = html.find(M_SCH_START); i2 = html.find(M_SCH_END, i1)
    if i1 >= 0 and i2 >= 0:
        html = html[:i1+len(M_SCH_START)] + "\n" + sched_html + refresh_card + "\n\n  " + html[i2:]
        print("  ✅ 本周日程")

# ── Write output ─────────────────────────────────────
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ All done — {date_cn} 全部更新完成")
