from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Amazon Arbitrage Sourcing API",
    description="Evaluate retail products as Amazon arbitrage opportunities.",
    version="0.1.0",
)

app.include_router(router)