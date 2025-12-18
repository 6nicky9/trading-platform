"""
FastAPI Web API for Trading Platform
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Trading Platform API",
    version="0.1.0",
    description="REST API for cryptocurrency trading platform"
)

class HealthResponse(BaseModel):
    status: str
    version: str

@app.get("/")
async def root():
    return {"message": "Trading Platform API"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="0.1.0")

@app.get("/markets")
async def get_markets():
    return {"markets": ["BTC/USDT", "ETH/USDT", "BNB/USDT"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
