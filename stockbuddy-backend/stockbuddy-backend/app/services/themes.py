"""
產業題材標籤系統
- 只用於顯示，不影響評分
- 未來可結合新聞、國際動態
"""

# 產業分類對照表
INDUSTRY_MAP = {
    # === 半導體 ===
    "2330": {"industry": "半導體", "tags": ["AI", "先進製程"]},
    "2454": {"industry": "IC設計", "tags": ["AI", "手機晶片"]},
    "3711": {"industry": "封測", "tags": ["先進封裝"]},
    "2379": {"industry": "伺服器", "tags": ["AI伺服器"]},
    "2408": {"industry": "記憶體", "tags": ["DRAM"]},
    "3008": {"industry": "IC設計", "tags": ["驅動IC"]},
    "2344": {"industry": "記憶體", "tags": ["HBM", "DDR5"]},
    "3443": {"industry": "IC設計", "tags": ["AI"]},
    "2449": {"industry": "IC設計", "tags": ["矽智財"]},
    "3661": {"industry": "IC設計", "tags": ["驅動IC"]},
    "2337": {"industry": "記憶體", "tags": ["模組"]},
    "3006": {"industry": "記憶體", "tags": ["NAND"]},
    "6415": {"industry": "矽智財", "tags": ["AI", "Arm"]},
    
    # === 電子代工 ===
    "2317": {"industry": "EMS", "tags": ["AI伺服器", "蘋果"]},
    "2382": {"industry": "代工", "tags": ["AI伺服器", "GB200"]},
    "2357": {"industry": "EMS", "tags": ["網通"]},
    "3034": {"industry": "IC設計", "tags": ["網通", "WiFi"]},
    "2376": {"industry": "主機板", "tags": ["AI伺服器"]},
    "2377": {"industry": "主機板", "tags": ["電競"]},
    
    # === 電子零組件 ===
    "2308": {"industry": "電源", "tags": ["電動車", "充電樁"]},
    "2301": {"industry": "光電", "tags": ["面板"]},
    "2303": {"industry": "晶圓代工", "tags": ["成熟製程"]},
    "2324": {"industry": "PCB", "tags": ["ABF載板"]},
    "3231": {"industry": "PCB", "tags": ["車用"]},
    "2353": {"industry": "電源", "tags": ["伺服器電源"]},
    "3044": {"industry": "機殼", "tags": ["伺服器"]},
    "2395": {"industry": "面板", "tags": ["車用"]},
    "2345": {"industry": "IC設計", "tags": ["聯陽"]},
    "2409": {"industry": "PCB", "tags": ["友達"]},
    "3017": {"industry": "散熱", "tags": ["AI散熱"]},
    "2474": {"industry": "PCB", "tags": ["HDI"]},
    "3702": {"industry": "光學", "tags": ["鏡頭"]},
    "2383": {"industry": "記憶體", "tags": ["NOR Flash"]},
    
    # === 金融 ===
    "2881": {"industry": "金控", "tags": ["壽險"]},
    "2882": {"industry": "金控", "tags": ["壽險"]},
    "2886": {"industry": "金控", "tags": ["銀行"]},
    "2891": {"industry": "金控", "tags": ["銀行"]},
    "2884": {"industry": "金控", "tags": ["壽險"]},
    "2892": {"industry": "金控", "tags": ["銀行"]},
    "2883": {"industry": "金控", "tags": ["銀行"]},
    "2887": {"industry": "金控", "tags": ["壽險"]},
    "2880": {"industry": "金控", "tags": ["高股息"]},
    "5880": {"industry": "金控", "tags": ["高股息"]},
    "2801": {"industry": "金融", "tags": ["銀行"]},
    "5876": {"industry": "金融", "tags": ["租賃"]},
    "2834": {"industry": "金融", "tags": ["銀行"]},
    "2838": {"industry": "金融", "tags": ["銀行"]},
    "2845": {"industry": "金融", "tags": ["票券"]},
    
    # === 傳產 ===
    "1301": {"industry": "塑膠", "tags": ["石化"]},
    "1303": {"industry": "塑膠", "tags": ["電子材料"]},
    "1326": {"industry": "塑化", "tags": ["石化"]},
    "2002": {"industry": "鋼鐵", "tags": ["基建"]},
    "1101": {"industry": "水泥", "tags": ["碳權"]},
    "1102": {"industry": "水泥", "tags": ["碳權"]},
    "1216": {"industry": "食品", "tags": ["民生消費"]},
    "2912": {"industry": "零售", "tags": ["超商"]},
    "2603": {"industry": "航運", "tags": ["散裝"]},
    "2609": {"industry": "航運", "tags": ["貨櫃"]},
    "1402": {"industry": "紡織", "tags": ["成衣"]},
    "2105": {"industry": "食品", "tags": ["飼料"]},
    "2207": {"industry": "汽車", "tags": ["和泰"]},
    "1504": {"industry": "電機", "tags": ["馬達"]},
    "1605": {"industry": "塑膠", "tags": ["華新"]},
    
    # === 其他 ===
    "2412": {"industry": "電信", "tags": ["5G", "高股息"]},
    "2615": {"industry": "航運", "tags": ["散裝"]},
    "2618": {"industry": "航空", "tags": ["旅遊"]},
    "2610": {"industry": "航運", "tags": ["華航"]},
    "9910": {"industry": "營建", "tags": ["房地產"]},
    "1227": {"industry": "食品", "tags": ["烘焙"]},
    "2915": {"industry": "零售", "tags": ["超市"]},
    
    # === 新增：更多金融 ===
    "2890": {"industry": "金控", "tags": ["永豐金"]},
    "2888": {"industry": "金控", "tags": ["新光金"]},
    
    # === 新增：更多半導體 ===
    "8046": {"industry": "IC設計", "tags": ["南電"]},
    "2436": {"industry": "封測", "tags": ["偉詮電"]},
    "3545": {"industry": "IC設計", "tags": ["敦泰"]},
    "6770": {"industry": "IC設計", "tags": ["力積電"]},
    "3707": {"industry": "IC設計", "tags": ["漢磊"]},
    
    # === 新增：AI/伺服器 ===
    "3533": {"industry": "散熱", "tags": ["AI散熱"]},
    "6669": {"industry": "散熱", "tags": ["緯穎"]},
    
    # === 新增：航運/觀光 ===
    "2634": {"industry": "航空", "tags": ["漢翔"]},
    "2606": {"industry": "航運", "tags": ["裕民"]},
    "5871": {"industry": "金融", "tags": ["中租"]},
    "2633": {"industry": "航空", "tags": ["台灣高鐵"]},
    "2637": {"industry": "航運", "tags": ["慧洋"]},
    
    # === 新增：生技 ===
    "6446": {"industry": "生技", "tags": ["藥華藥"]},
    "4743": {"industry": "生技", "tags": ["合一"]},
    "6472": {"industry": "醫材", "tags": ["保瑞"]},
    "1707": {"industry": "製藥", "tags": ["葡萄王"]},
    "4137": {"industry": "醫材", "tags": ["麗豐"]},
    "6547": {"industry": "生技", "tags": ["高端"]},
    
    # === 新增：ETF ===
    "0050": {"industry": "ETF", "tags": ["台灣50", "大盤"]},
    "0056": {"industry": "ETF", "tags": ["高股息"]},
    "00878": {"industry": "ETF", "tags": ["ESG高股息"]},
    "00919": {"industry": "ETF", "tags": ["群益台灣精選高息"]},
    "00929": {"industry": "ETF", "tags": ["復華台灣科技優息"]},
    "006208": {"industry": "ETF", "tags": ["富邦台50"]},
    
    # === 新增：其他電子 ===
    "2327": {"industry": "被動元件", "tags": ["國巨", "MLCC"]},
    "2385": {"industry": "電源", "tags": ["群光"]},
    "2360": {"industry": "光電", "tags": ["致茂"]},
    
    # === 新增：更多金融 ===
    "2885": {"industry": "金控", "tags": ["元大金"]},
    "2889": {"industry": "金控", "tags": ["國泰金"]},
    "2897": {"industry": "保險", "tags": ["王道銀"]},
    "2823": {"industry": "保險", "tags": ["中壽"]},
    
    # === 新增：更多AI/網通 ===
    "3596": {"industry": "網通", "tags": ["智易", "交換器"]},
    "2368": {"industry": "光通訊", "tags": ["金像電"]},
    "4938": {"industry": "網通", "tags": ["和碩"]},
    "2059": {"industry": "電源", "tags": ["川湖"]},
    "6285": {"industry": "散熱", "tags": ["啟碁"]},
    "3682": {"industry": "機殼", "tags": ["亞太電信"]},
    "5269": {"industry": "光通訊", "tags": ["祥碩"]},
    "6514": {"industry": "光通訊", "tags": ["芮特"]},
    "3705": {"industry": "網通", "tags": ["永信"]},
    "2356": {"industry": "工業電腦", "tags": ["英業達"]},
    "2312": {"industry": "PCB", "tags": ["金寶"]},
    "5274": {"industry": "IC設計", "tags": ["信驊"]},
    "6533": {"industry": "IC設計", "tags": ["晶心科"]},
    "2049": {"industry": "散熱", "tags": ["上銀"]},
    "3037": {"industry": "LED", "tags": ["欣興"]},
    
    # === 新增：傳產補充 ===
    "1904": {"industry": "紡織", "tags": ["正隆"]},
    "1434": {"industry": "紡織", "tags": ["福懋"]},
    "1476": {"industry": "紡織", "tags": ["儒鴻"]},
    "2605": {"industry": "航運", "tags": ["新興"]},
    
    # === 新增：生技補充 ===
    "1733": {"industry": "製藥", "tags": ["五鼎"]},
    "4142": {"industry": "醫材", "tags": ["國光生"]},
}


def get_stock_info(stock_id: str) -> dict:
    """
    取得股票的產業標籤資訊
    回傳: {"industry": "半導體", "tags": ["AI", "先進製程"]}
    """
    return INDUSTRY_MAP.get(stock_id, {"industry": "", "tags": []})


def get_industry(stock_id: str) -> str:
    """取得產業分類"""
    info = INDUSTRY_MAP.get(stock_id, {})
    return info.get("industry", "")


def get_tags(stock_id: str) -> list:
    """取得題材標籤"""
    info = INDUSTRY_MAP.get(stock_id, {})
    return info.get("tags", [])
