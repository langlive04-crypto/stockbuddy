"""
🤖 AI 智能選股引擎 - StockBuddy V10.7.1

整合多維度分析：
1. 技術面 - MA, RSI, MACD, KD, 布林通道, 成交量
2. 籌碼面 - 三大法人, 融資融券, 外資持股
3. 基本面 - PER, PBR, 營收成長, ROE, 殖利率
4. 消息面 - 新聞情緒分析

輸出：
- AI 精選 Top 10（最佳買點）
- 每檔股票的完整分析報告
- 風險評估與建議操作

V10.7 更新：使用 TWSE OpenAPI 取得全市場資料
V10.7.1 更新：整合智能快取（盤中/盤後動態 TTL）
"""

import asyncio
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from app.services.finmind_service import FinMindService, FinMindExtended
from app.services.twse_openapi import TWSEOpenAPI
from app.services.cache_service import SmartTTL, is_trading_hours  # 🆕 V10.7.1: 智能快取


@dataclass
class StockAnalysis:
    """股票分析結果"""
    stock_id: str
    name: str
    price: float
    change_percent: float
    
    # AI 評分
    ai_score: int  # 0-100
    signal: str  # 強力買進/買進/持有/觀望/減碼
    
    # 各維度分數
    technical_score: int
    chip_score: int
    fundamental_score: int
    sentiment_score: int
    
    # 詳細分析
    technical_detail: Dict
    chip_detail: Dict
    fundamental_detail: Dict
    
    # 建議
    reasons: List[str]  # 推薦理由
    risks: List[str]    # 風險提示
    stop_loss: float    # 止損價
    target: float       # 目標價
    
    # 標籤
    industry: str
    tags: List[str]


class AIStockPicker:
    """AI 智能選股引擎（支援智能快取）"""

    # 快取（使用智能 TTL）
    _cache = {}
    _cache_time = {}
    # 🆕 V10.7.1: 改用智能 TTL，盤後自動延長快取時間
    
    # ============================================================
    # 主要入口
    # ============================================================
    
    @classmethod
    async def get_top_picks(cls, top_n: int = 10) -> Dict:
        """
        取得 AI 精選股票
        
        Returns:
            {
                "updated_at": "2025-12-15T18:30:00",
                "market_summary": {...},
                "top_picks": [StockAnalysis, ...],
                "analysis_count": 100
            }
        """
        cache_key = f"top_picks_{top_n}"
        cached = cls._get_cache(cache_key)
        if cached:
            return cached
        
        print("🤖 AI 選股引擎啟動...")
        
        # Step 1: 取得全市場資料
        print("📊 掃描全市場...")
        all_stocks = await cls._get_market_data()
        
        if not all_stocks:
            print("❌ 無法取得市場資料")
            return {"error": "無法取得市場資料", "top_picks": []}
        
        print(f"✅ 取得 {len(all_stocks)} 檔股票")
        
        # Step 2: 初步篩選（排除不適合的股票）
        candidates = cls._pre_filter(all_stocks)
        print(f"📋 初篩後剩 {len(candidates)} 檔")
        
        # Step 3: 深度分析 Top 候選
        # 取漲幅/成交量前 50 名做深度分析
        top_candidates = sorted(
            candidates,
            key=lambda x: (x.get("change_percent", 0) * 0.4 + 
                          min(x.get("volume_ratio", 1), 5) * 0.6),
            reverse=True
        )[:50]
        
        print(f"🔍 深度分析前 {len(top_candidates)} 檔...")
        
        # Step 4: 多維度分析
        analyzed = []
        for i, stock in enumerate(top_candidates):
            try:
                analysis = await cls._deep_analyze(stock)
                if analysis:
                    analyzed.append(analysis)
                if (i + 1) % 10 == 0:
                    print(f"  分析進度: {i+1}/{len(top_candidates)}")
            except Exception as e:
                print(f"  ⚠️ {stock.get('stock_id')} 分析失敗: {e}")
        
        # Step 5: 排序並選出 Top N
        analyzed.sort(key=lambda x: x["ai_score"], reverse=True)
        top_picks = analyzed[:top_n]
        
        # Step 6: 產生報告
        result = {
            "updated_at": datetime.now().isoformat(),
            "market_summary": await cls._get_market_summary(),
            "top_picks": top_picks,
            "analysis_count": len(analyzed),
            "scanned_count": len(all_stocks),
        }
        
        cls._set_cache(cache_key, result)
        print(f"🎯 AI 精選完成！Top {len(top_picks)} 出爐")
        
        return result
    
    # ============================================================
    # 資料取得
    # ============================================================
    
    @classmethod
    async def _get_market_data(cls) -> List[Dict]:
        """
        取得市場資料
        
        V10.7 更新：優先使用 TWSE OpenAPI（全市場掃描）
        
        策略：
        1. TWSE OpenAPI 每日成交 + 本益比（全市場 1000+ 檔）
        2. 備用：核心股票清單 + yfinance
        """
        result = []
        
        # ============================================================
        # 方案 1: TWSE OpenAPI 全市場掃描（推薦）
        # ============================================================
        print("📊 嘗試 TWSE OpenAPI（全市場掃描）...")
        
        try:
            # 取得全市場每日成交 + 本益比
            all_summary = await TWSEOpenAPI.get_all_stocks_summary()
            
            if all_summary and len(all_summary) > 100:
                print(f"✅ TWSE OpenAPI 成功: {len(all_summary)} 檔")
                
                for stock_id, data in all_summary.items():
                    # 只取有價格的股票
                    if data.get("price") and len(stock_id) == 4:
                        result.append({
                            "stock_id": stock_id,
                            "name": data.get("name", stock_id),
                            "close": data.get("price", 0),
                            "change_percent": data.get("change_percent", 0),
                            "volume": data.get("volume", 0),
                            "pe_ratio": data.get("pe_ratio"),
                            "pb_ratio": data.get("pb_ratio"),
                            "dividend_yield": data.get("dividend_yield"),
                        })
                
                if result:
                    print(f"✅ 有效股票: {len(result)} 檔")
                    return result
            else:
                print("⚠️ TWSE OpenAPI 資料不足")
                
        except Exception as e:
            print(f"⚠️ TWSE OpenAPI 失敗: {e}")
        
        # ============================================================
        # 方案 2: 備用方案（核心股票清單）
        # ============================================================
        print("📋 使用備用方案：核心股票清單...")
        
        # 2025/12 更新：已驗證可用的股票清單
        CORE_STOCKS = [
            # 半導體 (15)
            "2330", "2454", "2303", "3711", "2379", "3034", "6415", "3443",
            "3661", "2408", "3035", "6239", "4961", "2344", "8046",
            # 電子代工 (10)
            "2317", "2382", "2353", "2357", "3231", "2356", "2324", "4938",
            "2301", "2376",
            # AI / 伺服器 (8)
            "2345", "3017", "6669", "2395", "3036", "6285", "3533", "8454",
            # 金融 (15)
            "2881", "2882", "2891", "2886", "2884", "2885", "2887", "2880",
            "2883", "2890", "5880", "2892", "2801", "5876", "2834",
            # 傳產龍頭 (12)
            "1301", "1303", "1326", "6505", "2002", "1402", "2912", "1216",
            "1101", "1102", "9910", "2105",
            # 航運 (5)
            "2603", "2609", "2615", "2618", "2610",
            # 電信 (3)
            "2412", "3045", "4904",
            # ETF (6)
            "0050", "0056", "00878", "00713", "00919", "00929",
            # 其他熱門 (10)
            "2227", "5871", "6770", "2542", "2474", "6409",
            "1590", "3008", "2377", "2409",
        ]
        
        return await cls._fallback_market_data(CORE_STOCKS)
    
    @classmethod
    async def _fallback_market_data(cls, stock_list: List[str] = None) -> List[Dict]:
        """
        備用方案：使用 yfinance 批量查詢
        """
        import yfinance as yf
        
        if not stock_list:
            # 預設核心清單
            stock_list = [
                "2330", "2317", "2454", "2303", "2881", "2882", "2891", "1301",
                "2886", "2884", "2885", "2887", "1216", "2357", "3008", "2382",
                "5880", "2892", "6505", "1326", "2377", "3045", "2395", "4904",
                "1101", "2912", "9910", "2105", "5871", "2883", "6669", "3034",
                "2603", "2207", "1102", "3231", "2880", "6415", "2379", "5876",
                "2409", "2474", "3443", "6446", "2345", "3533", "2301", "1590",
                "3017", "2376", "4938", "2353", "3661", "6472", "3706", "8046",
                "2344", "3035", "6239", "1476", "4961", "6285", "3044", "2408",
            ]
        
        print(f"📋 yfinance 查詢 {len(stock_list)} 檔股票...")
        
        result = []
        batch_size = 20
        
        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i+batch_size]
            
            # 轉換為 yfinance 格式
            symbols = [f"{sid}.TW" for sid in batch]
            
            try:
                # 批量下載
                data = yf.download(
                    symbols,
                    period="5d",
                    progress=False,
                    threads=True,
                )
                
                if data.empty:
                    continue
                
                for sid in batch:
                    symbol = f"{sid}.TW"
                    try:
                        if len(batch) > 1:
                            close_series = data['Close'][symbol]
                            volume_series = data['Volume'][symbol]
                        else:
                            close_series = data['Close']
                            volume_series = data['Volume']
                        
                        if close_series.empty:
                            continue
                        
                        # 取最後一筆有效資料
                        close = float(close_series.dropna().iloc[-1])
                        volume = int(volume_series.dropna().iloc[-1]) if not volume_series.empty else 0
                        
                        # 計算漲跌幅
                        if len(close_series.dropna()) >= 2:
                            prev_close = float(close_series.dropna().iloc[-2])
                            change_pct = round((close - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0
                        else:
                            change_pct = 0
                        
                        result.append({
                            "stock_id": sid,
                            "close": close,
                            "change_percent": change_pct,
                            "volume": volume,
                        })
                    except:
                        pass
                        
            except Exception as e:
                print(f"⚠️ yfinance 批次 {i//batch_size + 1} 失敗: {e}")
            
            # 進度
            if (i + batch_size) % 40 == 0:
                print(f"  進度: {min(i + batch_size, len(stock_list))}/{len(stock_list)}")
        
        print(f"✅ yfinance 取得: {len(result)} 檔")
        return result
    
    # ============================================================
    # 篩選
    # ============================================================
    
    @classmethod
    def _pre_filter(cls, stocks: List[Dict]) -> List[Dict]:
        """初步篩選"""
        filtered = []
        for stock in stocks:
            price = stock.get("close", 0)
            volume = stock.get("volume", 0)
            change_pct = stock.get("change_percent", 0)
            
            # 排除條件
            if price < 10:  # 低價股
                continue
            if price > 2000:  # 超高價股（資金門檻高）
                continue
            if volume < 100000:  # 成交量太低
                continue
            if change_pct <= -9.5:  # 跌停
                continue
            
            filtered.append(stock)
        
        return filtered
    
    # ============================================================
    # 深度分析
    # ============================================================
    
    @classmethod
    async def _deep_analyze(cls, stock: Dict) -> Optional[Dict]:
        """深度多維度分析"""
        stock_id = stock.get("stock_id")
        
        try:
            # 並行取得各維度資料
            tasks = [
                cls._analyze_technical(stock_id, stock),
                cls._analyze_chip(stock_id),
                cls._analyze_fundamental(stock_id),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            technical = results[0] if not isinstance(results[0], Exception) else {}
            chip = results[1] if not isinstance(results[1], Exception) else {}
            fundamental = results[2] if not isinstance(results[2], Exception) else {}
            
            # 計算 AI 綜合評分
            tech_score = technical.get("score", 50)
            chip_score = chip.get("score", 50)
            fund_score = fundamental.get("score", 50)
            
            # 權重：技術面 40%, 籌碼面 35%, 基本面 25%
            ai_score = int(
                tech_score * 0.40 +
                chip_score * 0.35 +
                fund_score * 0.25
            )
            
            # V10.37: 修正追高邏輯 - 過熱時減分，超跌時加分
            # 原 V10.35.5 方案 B 仍有追高風險，完全反轉邏輯
            # 參考審查報告建議：漲幅越高風險越大，應減分
            change_pct = stock.get("change_percent", 0)
            if change_pct > 5:
                ai_score -= 5  # 可能過熱，減分（原 +3）
            elif change_pct > 3:
                ai_score += 0  # 中性，不加不減（原 +2）
            elif 0 < change_pct <= 3:
                ai_score += 3  # 適度上漲，最佳買點（原 +1）
            elif -3 <= change_pct < 0:
                ai_score += 1  # 小幅回調，可觀察
            elif change_pct < -3:
                ai_score += 5  # 超跌可能反彈，加分

            # V10.35.5 方案 A: 連續性加分
            # 取得技術分析中的收盤價與成交量序列
            closes = technical.get("_closes", [])
            volumes = technical.get("_volumes", [])
            continuity = await cls._analyze_continuity(stock_id, closes, volumes)
            continuity_score = continuity.get("score", 0)
            ai_score += continuity_score

            # 限制範圍
            ai_score = max(15, min(95, ai_score))
            
            # 判斷訊號
            signal = cls._get_signal(ai_score)
            
            # 產生推薦理由
            reasons = cls._generate_reasons(technical, chip, fundamental, change_pct)
            
            # 風險提示
            risks = cls._generate_risks(technical, chip, fundamental)
            
            # 計算止損/目標價
            price = stock.get("close", 0)
            stop_loss = round(price * 0.95, 2)  # 5% 止損
            target = round(price * (1 + ai_score / 100), 2)  # 依分數設目標
            
            # 取得名稱和產業
            name = await cls._get_stock_name(stock_id)
            industry, tags = await cls._get_industry_tags(stock_id)
            
            # V10.35.5: 將連續性訊號加入推薦理由
            continuity_signals = continuity.get("signals", [])
            if continuity_signals:
                reasons = continuity_signals + reasons

            # V10.35.5 方案 C: 提取穩定度資訊
            volatility = technical.get("volatility", 0)
            stability_score = technical.get("stability_score", 50)

            return {
                "stock_id": stock_id,
                "name": name,
                "price": price,
                "change": stock.get("change", 0),
                "change_percent": change_pct,
                "volume": stock.get("volume", 0),

                "ai_score": ai_score,
                "signal": signal,

                "technical_score": tech_score,
                "chip_score": chip_score,
                "fundamental_score": fund_score,
                "continuity_score": continuity_score,  # V10.35.5: 連續性加分
                "stability_score": stability_score,  # V10.35.5 方案 C: 穩定度分數
                "volatility": volatility,  # V10.35.5 方案 C: 波動率

                "technical_detail": technical,
                "chip_detail": chip,
                "fundamental_detail": fundamental,
                "continuity_detail": continuity,  # V10.35.5: 連續性詳情

                "reasons": reasons,
                "risks": risks,
                "stop_loss": stop_loss,
                "target": target,

                "industry": industry,
                "tags": tags,
            }
            
        except Exception as e:
            print(f"⚠️ {stock_id} 深度分析失敗: {e}")
            return None
    
    # ============================================================
    # 技術面分析
    # ============================================================
    
    @classmethod
    async def _analyze_technical(cls, stock_id: str, current: Dict) -> Dict:
        """技術面分析 - 使用 yfinance 取得歷史資料"""
        try:
            import yfinance as yf
            
            # 使用 yfinance 取得歷史資料
            ticker = yf.Ticker(f"{stock_id}.TW")
            hist = ticker.history(period="3mo")
            
            if hist.empty or len(hist) < 20:
                return {"score": 50, "detail": "資料不足", "signals": []}
            
            closes = hist['Close'].tolist()
            volumes = hist['Volume'].tolist()
            
            # 計算指標
            ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else closes[-1]
            ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
            ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else ma20
            
            current_price = closes[-1]
            
            # RSI
            rsi = cls._calculate_rsi(closes)
            
            # MACD
            macd, signal_line, histogram = cls._calculate_macd(closes)
            
            # 成交量比
            avg_vol = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
            current_vol = volumes[-1] if volumes else 0
            volume_ratio = current_vol / avg_vol if avg_vol > 0 else 1

            # V10.35.5 方案 C: 穩定度指標
            # 計算 20 日波動率 (標準差 / 平均價 * 100)
            volatility = cls._calculate_volatility(closes[-20:]) if len(closes) >= 20 else 0
            stability_score = cls._calculate_stability_score(volatility)

            # 評分
            score = 50
            signals = []
            
            # 均線分析 (25分)
            if current_price > ma5 > ma20:
                score += 15
                signals.append("多頭排列")
            elif current_price > ma5:
                score += 8
                signals.append("站上5日線")
            elif current_price < ma5 < ma20:
                score -= 10
                signals.append("空頭排列")
            
            if current_price > ma60:
                score += 10
                signals.append("站上季線")
            
            # RSI 分析 (20分)
            if 40 <= rsi <= 60:
                score += 10
                signals.append("RSI 中性")
            elif 30 <= rsi < 40:
                score += 15
                signals.append("RSI 超賣回升")
            elif rsi < 30:
                score += 20
                signals.append("RSI 極度超賣")
            elif 60 < rsi <= 70:
                score += 5
            elif rsi > 80:
                score -= 10
                signals.append("RSI 超買")
            
            # MACD 分析 (20分)
            if histogram > 0 and macd > signal_line:
                score += 15
                signals.append("MACD 多方")
            elif histogram > 0:
                score += 8
            elif histogram < 0 and macd < signal_line:
                score -= 10
                signals.append("MACD 空方")
            
            # 量能分析 (15分)
            if volume_ratio > 2:
                score += 15
                signals.append("爆量")
            elif volume_ratio > 1.5:
                score += 10
                signals.append("量增")
            elif volume_ratio < 0.5:
                score -= 5
                signals.append("量縮")
            
            score = max(0, min(100, score))
            
            return {
                "score": score,
                "ma5": round(ma5, 2),
                "ma20": round(ma20, 2),
                "ma60": round(ma60, 2),
                "rsi": round(rsi, 1),
                "macd": round(macd, 3),
                "macd_signal": round(signal_line, 3),
                "macd_hist": round(histogram, 3),
                "volume_ratio": round(volume_ratio, 2),
                "volatility": round(volatility, 2),  # V10.35.5 方案 C: 波動率
                "stability_score": stability_score,  # V10.35.5 方案 C: 穩定度分數
                "signals": signals,
                "_closes": closes,  # V10.35.5: 供連續性分析使用
                "_volumes": volumes,  # V10.35.5: 供連續性分析使用
            }

        except Exception as e:
            return {"score": 50, "error": str(e), "signals": [], "_closes": [], "_volumes": [], "volatility": 0, "stability_score": 50}
    
    @classmethod
    def _calculate_rsi(cls, prices: List[float], period: int = 14) -> float:
        """計算 RSI"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @classmethod
    def _calculate_macd(cls, prices: List[float]) -> Tuple[float, float, float]:
        """計算 MACD"""
        if len(prices) < 26:
            return 0, 0, 0
        
        # EMA 計算
        def ema(data, period):
            if len(data) < period:
                return data[-1] if data else 0
            multiplier = 2 / (period + 1)
            ema_val = sum(data[:period]) / period
            for price in data[period:]:
                ema_val = (price - ema_val) * multiplier + ema_val
            return ema_val
        
        ema12 = ema(prices, 12)
        ema26 = ema(prices, 26)
        macd = ema12 - ema26
        
        # Signal line (9-day EMA of MACD)
        # 簡化計算
        signal = macd * 0.8
        histogram = macd - signal
        
        return macd, signal, histogram

    # V10.35.5 方案 C: 波動率與穩定度計算
    @classmethod
    def _calculate_volatility(cls, prices: List[float]) -> float:
        """
        計算波動率 (標準差 / 平均價 * 100)

        Returns:
            波動率百分比，數值越小越穩定
            - < 2%: 非常穩定
            - 2-5%: 穩定
            - 5-10%: 中等波動
            - > 10%: 高波動
        """
        if not prices or len(prices) < 5:
            return 0

        avg_price = sum(prices) / len(prices)
        if avg_price == 0:
            return 0

        # 計算標準差
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        std_dev = math.sqrt(variance)

        # 波動率 = 標準差 / 平均價 * 100
        return (std_dev / avg_price) * 100

    @classmethod
    def _calculate_stability_score(cls, volatility: float) -> int:
        """
        根據波動率計算穩定度分數 (0-100)

        波動率越低，穩定度分數越高
        """
        if volatility <= 1:
            return 95  # 極度穩定
        elif volatility <= 2:
            return 85
        elif volatility <= 3:
            return 75
        elif volatility <= 5:
            return 65
        elif volatility <= 7:
            return 55
        elif volatility <= 10:
            return 45
        elif volatility <= 15:
            return 35
        else:
            return 25  # 高波動

    # ============================================================
    # 籌碼面分析
    # ============================================================
    
    @classmethod
    async def _analyze_chip(cls, stock_id: str) -> Dict:
        """籌碼面分析"""
        try:
            # 取得三大法人資料
            inst_data = await FinMindService.get_latest_institutional(stock_id)
            
            # 取得融資融券資料
            margin_data = await FinMindService.get_margin_trading(stock_id, days=10)
            latest_margin = margin_data[-1] if margin_data else {}
            
            score = 50
            signals = []
            
            # 三大法人分析 (40分)
            foreign = inst_data.get("foreign", {})
            trust = inst_data.get("trust", {})
            dealer = inst_data.get("dealer", {})
            
            foreign_net = foreign.get("net", 0)
            trust_net = trust.get("net", 0)
            dealer_net = dealer.get("net", 0)
            total_net = foreign_net + trust_net + dealer_net
            
            if total_net > 1000:
                score += 20
                signals.append("三大法人買超")
            elif total_net > 0:
                score += 10
            elif total_net < -1000:
                score -= 15
                signals.append("三大法人賣超")
            
            if foreign_net > 500:
                score += 15
                signals.append("外資買超")
            elif foreign_net < -500:
                score -= 10
                signals.append("外資賣超")
            
            if trust_net > 100:
                score += 10
                signals.append("投信買超")
            
            # 融資融券分析 (20分)
            margin_balance = latest_margin.get("MarginPurchaseTodayBalance", 0)
            short_balance = latest_margin.get("ShortSaleTodayBalance", 0)
            
            if short_balance > 0 and margin_balance > 0:
                short_ratio = short_balance / margin_balance * 100
                if short_ratio > 30:
                    score += 15
                    signals.append(f"券資比高({short_ratio:.1f}%)")
                elif short_ratio > 20:
                    score += 8
            
            score = max(0, min(100, score))
            
            return {
                "score": score,
                "foreign_net": foreign_net,
                "trust_net": trust_net,
                "dealer_net": dealer_net,
                "total_net": total_net,
                "margin_balance": margin_balance,
                "short_balance": short_balance,
                "signals": signals,
            }
            
        except Exception as e:
            return {"score": 50, "error": str(e)}

    # ============================================================
    # V10.35.5 方案 A: 連續性分析
    # ============================================================

    @classmethod
    async def _analyze_continuity(cls, stock_id: str, closes: List[float] = None, volumes: List[float] = None) -> Dict:
        """
        連續性分析 - 計算連續買超、連續站穩均線等加分項

        加分規則：
        - 連續 3 日外資買超：+5 分
        - 連續 5 日站穩 MA5：+5 分
        - 連續 3 日成交量放大：+3 分
        - 上週曾入選 AI 精選：+3 分（需另外記錄，此處先不實作）
        """
        try:
            result = {
                "score": 0,
                "foreign_consecutive_days": 0,
                "above_ma5_days": 0,
                "volume_increase_days": 0,
                "signals": [],
            }

            # 1. 取得三大法人歷史資料（最近 10 天）
            inst_data = await FinMindService.get_institutional_investors(stock_id)

            if inst_data and len(inst_data) >= 3:
                # 計算外資連續買超天數（從最新往回算）
                consecutive_foreign = 0
                for day_data in inst_data[:10]:  # 最近 10 天
                    if day_data.get("foreign_net", 0) > 0:
                        consecutive_foreign += 1
                    else:
                        break

                result["foreign_consecutive_days"] = consecutive_foreign

                if consecutive_foreign >= 5:
                    result["score"] += 8
                    result["signals"].append(f"外資連續{consecutive_foreign}日買超")
                elif consecutive_foreign >= 3:
                    result["score"] += 5
                    result["signals"].append(f"外資連續{consecutive_foreign}日買超")

            # 2. 計算連續站穩 MA5 天數
            if closes and len(closes) >= 10:
                ma5_days = 0
                for i in range(min(10, len(closes) - 5)):
                    idx = -(i + 1)
                    price = closes[idx]
                    ma5 = sum(closes[idx-4:idx+1]) / 5 if idx >= -len(closes) + 4 else closes[idx]
                    if price >= ma5 * 0.99:  # 允許 1% 誤差
                        ma5_days += 1
                    else:
                        break

                result["above_ma5_days"] = ma5_days

                if ma5_days >= 7:
                    result["score"] += 8
                    result["signals"].append(f"連續{ma5_days}日站穩MA5")
                elif ma5_days >= 5:
                    result["score"] += 5
                    result["signals"].append(f"連續{ma5_days}日站穩MA5")

            # 3. 計算成交量連續放大天數
            if volumes and len(volumes) >= 5:
                vol_increase_days = 0
                for i in range(1, min(6, len(volumes))):
                    if volumes[-(i)] > volumes[-(i+1)] * 1.1:  # 成交量增加 10% 以上
                        vol_increase_days += 1
                    else:
                        break

                result["volume_increase_days"] = vol_increase_days

                if vol_increase_days >= 3:
                    result["score"] += 3
                    result["signals"].append(f"成交量連續{vol_increase_days}日放大")

            return result

        except Exception as e:
            print(f"⚠️ {stock_id} 連續性分析失敗: {e}")
            return {"score": 0, "signals": [], "error": str(e)}

    # ============================================================
    # 基本面分析
    # ============================================================
    
    @classmethod
    async def _analyze_fundamental(cls, stock_id: str) -> Dict:
        """基本面分析"""
        try:
            # 取得 PER/PBR
            valuation = await FinMindService.get_per_pbr(stock_id, days=5)
            latest_val = valuation[-1] if valuation else {}
            
            # 取得營收
            revenue = await FinMindExtended.get_latest_revenue(stock_id)
            
            score = 50
            signals = []
            
            # 估值分析 (30分)
            per = latest_val.get("PER", 0)
            pbr = latest_val.get("PBR", 0)
            div_yield = latest_val.get("dividend_yield", 0)
            
            if per and 0 < per < 15:
                score += 15
                signals.append(f"低本益比({per:.1f})")
            elif per and 15 <= per < 25:
                score += 8
            elif per and per > 40:
                score -= 10
                signals.append(f"高本益比({per:.1f})")
            
            if pbr and 0 < pbr < 1.5:
                score += 10
                signals.append(f"低淨值比({pbr:.2f})")
            elif pbr and pbr > 5:
                score -= 5
            
            if div_yield and div_yield > 5:
                score += 15
                signals.append(f"高殖利率({div_yield:.1f}%)")
            elif div_yield and div_yield > 3:
                score += 8
            
            # 營收分析 (20分)
            yoy = revenue.get("yoy")
            if yoy is not None:
                if yoy > 20:
                    score += 20
                    signals.append(f"營收年增{yoy:.1f}%")
                elif yoy > 10:
                    score += 12
                    signals.append(f"營收成長{yoy:.1f}%")
                elif yoy > 0:
                    score += 5
                elif yoy < -10:
                    score -= 10
                    signals.append(f"營收衰退{yoy:.1f}%")
            
            score = max(0, min(100, score))
            
            return {
                "score": score,
                "per": per,
                "pbr": pbr,
                "dividend_yield": div_yield,
                "revenue_yoy": yoy,
                "signals": signals,
            }
            
        except Exception as e:
            return {"score": 50, "error": str(e)}
    
    # ============================================================
    # 輔助函數
    # ============================================================
    
    @classmethod
    def _get_signal(cls, score: int) -> str:
        """根據分數產生訊號"""
        if score >= 80:
            return "強力買進"
        elif score >= 70:
            return "買進"
        elif score >= 55:
            return "持有"
        elif score >= 40:
            return "觀望"
        else:
            return "減碼"
    
    @classmethod
    def _generate_reasons(cls, tech: Dict, chip: Dict, fund: Dict, change_pct: float) -> List[str]:
        """產生推薦理由"""
        reasons = []
        
        # 技術面理由
        tech_signals = tech.get("signals", [])
        for sig in tech_signals[:2]:
            if any(x in sig for x in ["多頭", "站上", "超賣", "量增", "爆量"]):
                reasons.append(f"📈 {sig}")
        
        # 籌碼面理由
        chip_signals = chip.get("signals", [])
        for sig in chip_signals[:2]:
            if "買超" in sig or "券資比" in sig:
                reasons.append(f"💰 {sig}")
        
        # 基本面理由
        fund_signals = fund.get("signals", [])
        for sig in fund_signals[:2]:
            if any(x in sig for x in ["低", "高殖利率", "成長"]):
                reasons.append(f"📊 {sig}")
        
        # 當日表現
        if change_pct > 3:
            reasons.append(f"🔥 今日強勢 +{change_pct:.1f}%")
        
        return reasons[:5]  # 最多 5 條
    
    @classmethod
    def _generate_risks(cls, tech: Dict, chip: Dict, fund: Dict) -> List[str]:
        """產生風險提示"""
        risks = []
        
        # 技術面風險
        if tech.get("rsi", 50) > 70:
            risks.append("⚠️ RSI 偏高，注意回調風險")
        
        # 籌碼面風險
        if chip.get("total_net", 0) < -500:
            risks.append("⚠️ 法人持續賣超")
        
        # 基本面風險
        per = fund.get("per", 0)
        if per and per > 30:
            risks.append("⚠️ 本益比偏高")
        
        yoy = fund.get("revenue_yoy")
        if yoy is not None and yoy < 0:
            risks.append("⚠️ 營收衰退中")
        
        if not risks:
            risks.append("✅ 目前無重大風險")
        
        return risks
    
    @classmethod
    async def _get_stock_name(cls, stock_id: str) -> str:
        """取得股票名稱"""
        from app.services.github_data import GitHubStockService
        return GitHubStockService.POPULAR_STOCKS.get(stock_id, stock_id)
    
    @classmethod
    async def _get_industry_tags(cls, stock_id: str) -> Tuple[str, List[str]]:
        """取得產業和標籤"""
        try:
            from app.services.themes import get_stock_info as get_stock_tags
            theme = get_stock_tags(stock_id)
            return theme.get("industry", "其他"), theme.get("tags", [])
        except:
            return "其他", []
    
    @classmethod
    async def _get_market_summary(cls) -> Dict:
        """取得市場概況"""
        try:
            # 嘗試取得大盤資料
            data = await FinMindService._request("TaiwanVariousIndicators5Seconds", {})
            if data:
                latest = data[-1] if data else {}
                return {
                    "index": latest.get("price", 0),
                    "change": latest.get("change", 0),
                    "status": "交易中" if datetime.now().hour < 14 else "收盤",
                }
        except:
            pass
        
        return {"index": 0, "change": 0, "status": "未知"}
    
    @classmethod
    def _get_cache(cls, key: str):
        """取得快取（使用智能 TTL）"""
        if key in cls._cache:
            # 🆕 V10.7.1: 使用智能 TTL，盤後自動延長快取時間
            ttl = SmartTTL.get_ttl("recommend")
            if datetime.now().timestamp() - cls._cache_time.get(key, 0) < ttl:
                return cls._cache[key]
        return None

    @classmethod
    def _set_cache(cls, key: str, value):
        """設定快取"""
        cls._cache[key] = value
        cls._cache_time[key] = datetime.now().timestamp()


# ============================================================
# 便捷函數
# ============================================================

async def get_ai_top_picks(top_n: int = 10) -> Dict:
    """取得 AI 精選 Top N"""
    return await AIStockPicker.get_top_picks(top_n)
