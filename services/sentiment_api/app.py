from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Sentiment API")


class NewsItem(BaseModel):
    id: str = Field(..., description="Unique id of the news item")
    title: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None


class ScoredItem(BaseModel):
    id: str
    sentiment_score: float


@app.post("/score_news_batch", response_model=List[ScoredItem])
def score_news_batch(items: List[NewsItem]):
    """
    Trivial heuristic: positive words (+1), negative words (-1); normalize to [-1, 1].
    """
    pos = {"beat", "surge", "gain", "strong", "positive", "rally", "up"}
    neg = {"miss", "plunge", "loss", "weak", "negative", "selloff", "down"}
    out: List[ScoredItem] = []
    for it in items:
        text = f"{it.title or ''} {it.text or ''}".lower()
        score = 0
        score += sum(1 for w in pos if w in text)
        score -= sum(1 for w in neg if w in text)
        if score > 0:
            norm = min(1.0, score / 3.0)
        elif score < 0:
            norm = max(-1.0, score / 3.0)
        else:
            norm = 0.0
        out.append(ScoredItem(id=it.id, sentiment_score=float(norm)))
    return out
