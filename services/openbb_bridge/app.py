from fastapi import FastAPI

app = FastAPI()


@app.get("/price")
def price(ticker: str):
    return {"ticker": ticker, "prices": []}
