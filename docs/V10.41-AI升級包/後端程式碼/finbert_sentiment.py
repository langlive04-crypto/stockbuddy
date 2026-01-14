"""
FinBERT 情緒分析模組 V10.41

使用預訓練 FinBERT 模型進行金融新聞情緒分析

安裝位置: stockbuddy-backend/app/services/finbert_sentiment.py

依賴:
    pip install transformers>=4.36.0 torch>=2.1.0 sentencepiece>=0.1.99
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# 延遲導入
torch = None
transformers = None


def _ensure_dependencies():
    """確保依賴已導入"""
    global torch, transformers
    if torch is None:
        try:
            import torch as _torch
            import transformers as _transformers
            torch = _torch
            transformers = _transformers
            logger.info("[FinBERT] 依賴載入成功")
        except ImportError as e:
            raise ImportError(
                "請安裝依賴: pip install transformers>=4.36.0 torch>=2.1.0"
            ) from e


@dataclass
class SentimentResult:
    """情緒分析結果"""
    label: str           # "positive", "negative", "neutral"
    score: float         # 信心分數 (0-1)
    probabilities: Dict[str, float]  # 各類別機率
    model: str           # 使用的模型
    processing_time_ms: float


class FinBERTSentiment:
    """
    FinBERT 情緒分析器

    支援英文和中文金融新聞情緒分析

    使用方式:
    ```python
    analyzer = FinBERTSentiment(language="zh")
    result = analyzer.analyze("台積電營收創新高")
    print(result.label)  # "positive"
    ```
    """

    # 預設模型
    MODELS = {
        "en": "ProsusAI/finbert",
        "zh": "hw2942/chinese-finbert-sentiment",
        "zh_backup": "uer/roberta-base-finetuned-chinanews-chinese"
    }

    # 標籤對應 (不同模型可能有不同標籤)
    LABEL_MAP = {
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral",
        "POSITIVE": "positive",
        "NEGATIVE": "negative",
        "NEUTRAL": "neutral",
        "LABEL_0": "negative",
        "LABEL_1": "neutral",
        "LABEL_2": "positive",
    }

    def __init__(self, language: str = "zh", device: str = "auto"):
        """
        初始化 FinBERT 分析器

        Args:
            language: 語言 ("en" 英文, "zh" 中文)
            device: 裝置 ("auto", "cpu", "cuda")
        """
        _ensure_dependencies()

        self.language = language
        self.model_name = self.MODELS.get(language, self.MODELS["en"])

        # 自動選擇裝置
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self._model = None
        self._tokenizer = None
        self._loaded = False

    def _load_model(self):
        """載入模型 (延遲載入)"""
        if self._loaded:
            return

        logger.info(f"[FinBERT] 載入模型: {self.model_name}")

        try:
            self._tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.model_name
            )
            self._model = transformers.AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            self._model.to(self.device)
            self._model.eval()

            self._loaded = True
            logger.info(f"[FinBERT] 模型載入完成 (device: {self.device})")

        except Exception as e:
            # 嘗試備用模型
            if self.language == "zh":
                logger.warning(f"[FinBERT] 主模型載入失敗，嘗試備用模型")
                self.model_name = self.MODELS["zh_backup"]
                self._tokenizer = transformers.AutoTokenizer.from_pretrained(
                    self.model_name
                )
                self._model = transformers.AutoModelForSequenceClassification.from_pretrained(
                    self.model_name
                )
                self._model.to(self.device)
                self._model.eval()
                self._loaded = True
            else:
                raise e

    def analyze(self, text: str) -> SentimentResult:
        """
        分析單條文本情緒

        Args:
            text: 待分析文本

        Returns:
            SentimentResult 情緒分析結果
        """
        import time
        start_time = time.time()

        self._load_model()

        # Tokenize
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 推論
        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)

        # 取得結果
        probs_np = probs.cpu().numpy()[0]
        predicted_idx = int(torch.argmax(probs).item())

        # 取得標籤
        if hasattr(self._model.config, 'id2label'):
            raw_label = self._model.config.id2label[predicted_idx]
        else:
            raw_label = f"LABEL_{predicted_idx}"

        # 標準化標籤
        label = self.LABEL_MAP.get(raw_label, "neutral")

        # 建立機率字典
        if hasattr(self._model.config, 'id2label'):
            probabilities = {
                self.LABEL_MAP.get(self._model.config.id2label[i], f"class_{i}"): float(probs_np[i])
                for i in range(len(probs_np))
            }
        else:
            probabilities = {
                "negative": float(probs_np[0]) if len(probs_np) > 0 else 0,
                "neutral": float(probs_np[1]) if len(probs_np) > 1 else 0,
                "positive": float(probs_np[2]) if len(probs_np) > 2 else 0,
            }

        processing_time = (time.time() - start_time) * 1000

        return SentimentResult(
            label=label,
            score=float(probs_np[predicted_idx]),
            probabilities=probabilities,
            model=self.model_name,
            processing_time_ms=round(processing_time, 2)
        )

    def analyze_batch(
        self,
        texts: List[str],
        batch_size: int = 8
    ) -> List[SentimentResult]:
        """
        批次分析多條文本

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            SentimentResult 列表
        """
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                try:
                    result = self.analyze(text)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"[FinBERT] 分析失敗: {e}")
                    # 返回中性結果
                    results.append(SentimentResult(
                        label="neutral",
                        score=0.5,
                        probabilities={"positive": 0.33, "neutral": 0.34, "negative": 0.33},
                        model=self.model_name,
                        processing_time_ms=0
                    ))
        return results

    def get_sentiment_score(self, text: str) -> float:
        """
        取得情緒分數 (0-100)

        正面 = 高分, 負面 = 低分

        Args:
            text: 待分析文本

        Returns:
            情緒分數 (0-100)
        """
        result = self.analyze(text)

        # 轉換為 0-100 分數
        pos = result.probabilities.get("positive", 0)
        neg = result.probabilities.get("negative", 0)

        # 正面 - 負面 的加權分數
        score = 50 + (pos - neg) * 50

        return max(0, min(100, score))


# 全域實例 (單例模式)
_zh_analyzer: Optional[FinBERTSentiment] = None
_en_analyzer: Optional[FinBERTSentiment] = None


def get_analyzer(language: str = "zh") -> FinBERTSentiment:
    """取得分析器實例"""
    global _zh_analyzer, _en_analyzer

    if language == "zh":
        if _zh_analyzer is None:
            _zh_analyzer = FinBERTSentiment(language="zh")
        return _zh_analyzer
    else:
        if _en_analyzer is None:
            _en_analyzer = FinBERTSentiment(language="en")
        return _en_analyzer


def analyze_sentiment(text: str, language: str = "zh") -> Dict[str, Any]:
    """
    便捷函數：分析情緒

    Returns:
        {
            "label": "positive",
            "score": 0.92,
            "probabilities": {...},
            "model": "...",
            "processing_time_ms": 45
        }
    """
    analyzer = get_analyzer(language)
    result = analyzer.analyze(text)
    return asdict(result)


def get_sentiment_score(text: str, language: str = "zh") -> float:
    """
    便捷函數：取得情緒分數 (0-100)
    """
    analyzer = get_analyzer(language)
    return analyzer.get_sentiment_score(text)
