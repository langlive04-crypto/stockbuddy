"""
新聞服務模組 V10.41
- 整合多個新聞來源
- 提供股票相關新聞
- 進行情緒分析

V10.41: 整合 FinBERT 深度學習情緒分析
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import xml.etree.ElementTree as ET

# 股票名稱對照（用於新聞搜尋）
STOCK_NAMES = {
    "2330": "台積電",
    "2454": "聯發科",
    "2317": "鴻海",
    "2308": "台達電",
    "2303": "聯電",
    "2412": "中華電",
    "3711": "日月光",
    "2382": "廣達",
    "2357": "華碩",
    "3034": "聯詠",
    "2881": "富邦金",
    "2882": "國泰金",
    "2886": "兆豐金",
    "2891": "中信金",
    "2884": "玉山金",
    "2379": "瑞昱",
    "2408": "南亞科",
    "2344": "華邦電",
    "1301": "台塑",
    "1303": "南亞",
    "2002": "中鋼",
    "2603": "長榮",
    "2609": "陽明",
    "2615": "萬海",
}

# 產業關鍵字對照
INDUSTRY_KEYWORDS = {
    "半導體": ["半導體", "晶片", "晶圓", "IC", "封測", "先進製程", "CoWoS"],
    "AI": ["AI", "人工智慧", "輝達", "NVIDIA", "GPU", "大語言模型", "ChatGPT"],
    "記憶體": ["記憶體", "DRAM", "HBM", "DDR5", "NAND", "Flash"],
    "電動車": ["電動車", "特斯拉", "Tesla", "EV", "充電樁", "電池"],
    "金融": ["升息", "降息", "央行", "利率", "金控", "壽險"],
    "航運": ["航運", "貨櫃", "散裝", "運價", "海運"],
    "面板": ["面板", "LCD", "OLED", "顯示器"],
}

# 情緒關鍵字
POSITIVE_KEYWORDS = [
    "大漲", "飆漲", "創新高", "突破", "利多", "看好", "成長", "獲利",
    "訂單", "擴產", "調升", "買超", "加碼", "樂觀", "強勁", "亮眼",
    "超預期", "上修", "需求增", "供不應求", "滿載", "爆單"
]

NEGATIVE_KEYWORDS = [
    "大跌", "重挫", "崩跌", "利空", "看壞", "衰退", "虧損", "下修",
    "賣超", "減碼", "悲觀", "疲軟", "砍單", "庫存", "下滑", "警訊",
    "低於預期", "需求減", "產能過剩", "裁員", "關廠"
]


class NewsService:
    """新聞服務"""

    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_duration = 300  # 5分鐘快取
        self._finbert_available = None  # V10.41: FinBERT 可用性快取
        self._finbert_analyzer = None   # V10.41: FinBERT 分析器實例
    
    async def get_stock_news(self, stock_id: str, limit: int = 5) -> List[Dict]:
        """取得個股相關新聞"""
        stock_name = STOCK_NAMES.get(stock_id, stock_id)
        
        # 檢查快取
        cache_key = f"stock_{stock_id}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key][:limit]
        
        news_list = []
        
        # 從多個來源取得新聞
        tasks = [
            self._fetch_google_news(stock_name),
            self._fetch_yahoo_news(stock_id),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                news_list.extend(result)
        
        # 去重和排序
        seen_titles = set()
        unique_news = []
        for news in news_list:
            if news["title"] not in seen_titles:
                seen_titles.add(news["title"])
                unique_news.append(news)
        
        # 按時間排序
        unique_news.sort(key=lambda x: x.get("time", ""), reverse=True)
        
        # 加入情緒分析
        for news in unique_news:
            news["sentiment"] = self._analyze_sentiment(news["title"])
        
        # 更新快取
        self.cache[cache_key] = unique_news
        self.cache_time[cache_key] = datetime.now()
        
        return unique_news[:limit]
    
    async def get_market_news(self, limit: int = 10) -> List[Dict]:
        """取得大盤/市場新聞"""
        cache_key = "market"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key][:limit]
        
        news_list = []
        
        # 搜尋多個關鍵字
        keywords = ["台股", "加權指數", "台灣股市"]
        
        for keyword in keywords:
            try:
                result = await self._fetch_google_news(keyword)
                if result:
                    news_list.extend(result)
            except:
                pass
        
        # 去重
        seen_titles = set()
        unique_news = []
        for news in news_list:
            if news["title"] not in seen_titles:
                seen_titles.add(news["title"])
                news["sentiment"] = self._analyze_sentiment(news["title"])
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x.get("time", ""), reverse=True)
        
        self.cache[cache_key] = unique_news
        self.cache_time[cache_key] = datetime.now()
        
        return unique_news[:limit]
    
    async def get_industry_news(self, industry: str, limit: int = 5) -> List[Dict]:
        """取得產業新聞"""
        keywords = INDUSTRY_KEYWORDS.get(industry, [industry])
        
        cache_key = f"industry_{industry}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key][:limit]
        
        news_list = []
        
        for keyword in keywords[:3]:  # 限制搜尋數量
            try:
                result = await self._fetch_google_news(keyword)
                if result:
                    news_list.extend(result)
            except:
                pass
        
        # 去重和情緒分析
        seen_titles = set()
        unique_news = []
        for news in news_list:
            if news["title"] not in seen_titles:
                seen_titles.add(news["title"])
                news["sentiment"] = self._analyze_sentiment(news["title"])
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x.get("time", ""), reverse=True)
        
        self.cache[cache_key] = unique_news
        self.cache_time[cache_key] = datetime.now()
        
        return unique_news[:limit]
    
    async def _fetch_google_news(self, query: str) -> List[Dict]:
        """從 Google News RSS 取得新聞"""
        try:
            url = f"https://news.google.com/rss/search?q={query}+台股&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return []
                
                # 解析 RSS XML
                root = ET.fromstring(response.content)
                news_list = []
                
                for item in root.findall(".//item")[:10]:
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    source = item.find("source")
                    
                    if title is not None:
                        news_list.append({
                            "title": title.text,
                            "link": link.text if link is not None else "",
                            "time": self._parse_date(pub_date.text) if pub_date is not None else "",
                            "source": source.text if source is not None else "Google News",
                        })
                
                return news_list
        except Exception as e:
            print(f"Google News 錯誤: {e}")
            return []
    
    async def _fetch_yahoo_news(self, stock_id: str) -> List[Dict]:
        """從 Yahoo Finance 取得新聞"""
        try:
            # Yahoo Finance 台股代號格式
            symbol = f"{stock_id}.TW"
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            
            # Yahoo 的新聞 API 較複雜，這裡簡化處理
            # 實際上可能需要另外的 endpoint
            return []
        except Exception as e:
            print(f"Yahoo News 錯誤: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """
        分析文字情緒

        V10.41: 優先使用 FinBERT 深度學習模型，
        若 FinBERT 不可用則回退到關鍵字匹配
        """
        # V10.41: 嘗試使用 FinBERT
        finbert_result = self._analyze_with_finbert(text)
        if finbert_result:
            return finbert_result

        # 回退: 關鍵字匹配分析
        return self._analyze_with_keywords(text)

    def _analyze_with_finbert(self, text: str) -> Optional[Dict]:
        """
        V10.41: 使用 FinBERT 進行情緒分析
        """
        # 檢查 FinBERT 是否可用
        if self._finbert_available is False:
            return None

        try:
            # 延遲導入 FinBERT
            if self._finbert_analyzer is None:
                from app.services.finbert_sentiment import FinBERTSentiment
                self._finbert_analyzer = FinBERTSentiment(language="zh")
                self._finbert_available = True

            # 分析情緒
            result = self._finbert_analyzer.analyze(text)

            # 轉換為內部格式
            label_map = {
                "positive": "利多",
                "negative": "利空",
                "neutral": "中性"
            }

            return {
                "type": result.label,
                "score": int(result.probabilities.get("positive", 0.5) * 100),
                "label": label_map.get(result.label, "中性"),
                "confidence": result.score,
                "model": "finbert",  # V10.41: 標記使用的模型
            }

        except ImportError:
            # FinBERT 未安裝
            self._finbert_available = False
            return None
        except Exception as e:
            # FinBERT 分析失敗，回退到關鍵字
            print(f"[NewsService] FinBERT 分析失敗: {e}")
            return None

    def _analyze_with_keywords(self, text: str) -> Dict:
        """
        使用關鍵字匹配進行情緒分析 (回退方案)
        """
        positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
        negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

        if positive_count > negative_count:
            sentiment = "positive"
            score = min(100, 50 + positive_count * 15)
            label = "利多"
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(0, 50 - negative_count * 15)
            label = "利空"
        else:
            sentiment = "neutral"
            score = 50
            label = "中性"

        return {
            "type": sentiment,
            "score": score,
            "label": label,
            "model": "keywords",  # V10.41: 標記使用的模型
        }
    
    def _parse_date(self, date_str: str) -> str:
        """解析日期字串"""
        try:
            # Google News RSS 日期格式: "Sat, 14 Dec 2024 10:30:00 GMT"
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return date_str
    
    def _is_cache_valid(self, key: str) -> bool:
        """檢查快取是否有效"""
        if key not in self.cache or key not in self.cache_time:
            return False
        
        elapsed = (datetime.now() - self.cache_time[key]).total_seconds()
        return elapsed < self.cache_duration
    
    def get_news_summary(self, news_list: List[Dict]) -> Dict:
        """取得新聞摘要（用於提示詞生成）"""
        if not news_list:
            return {"trend": "neutral", "summary": "暫無相關新聞"}
        
        positive = sum(1 for n in news_list if n.get("sentiment", {}).get("type") == "positive")
        negative = sum(1 for n in news_list if n.get("sentiment", {}).get("type") == "negative")
        
        if positive > negative * 2:
            trend = "very_positive"
            summary = "近期新聞偏多，市場情緒樂觀"
        elif positive > negative:
            trend = "positive"
            summary = "新聞面偏正向"
        elif negative > positive * 2:
            trend = "very_negative"
            summary = "近期利空消息較多，需留意風險"
        elif negative > positive:
            trend = "negative"
            summary = "新聞面偏負向"
        else:
            trend = "neutral"
            summary = "新聞面中性"
        
        return {
            "trend": trend,
            "summary": summary,
            "positive_count": positive,
            "negative_count": negative,
            "total": len(news_list),
        }


# 單例模式
_news_service = None

def get_news_service() -> NewsService:
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
