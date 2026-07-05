from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, Base, engine
from app.service import process_webhook_order
from app.models import Product
import asyncio

# Initialise FastAPI app
app = FastAPI(
    title="Inventory Sync Engine",
    version="1.0.0",
    description="Real-time inventory management system preventing race conditions"
)

# Pydantic models for request/response validation
class WebhookPayload(BaseModel):
    order_id: str
    product_sku: str
    quantity: int
    idempotency_key: Optional[str] = None

class InventoryResponse(BaseModel):
    sku: str
    available: int
    reserved: int
    total: int

# Startup event -> Creates database tables when app first runs
@app.on_event("startup")
async def create_tables():
    # Create all database tables defined in models if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables successfully created")

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "Inventory Sync Engine"}

# WEBHOOK receiving endpoint
# Receives order notifications from external systems (e.g., Shopify, Amazon)
@app.post("/api/webhooks/order-created")
async def receive_order(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    try:
        key = payload.idempotency_key or payload.order_id
        result = await process_webhook_order(db, key, payload.product_sku, payload.quantity)

        return {
            "status": "success",
            "message": result["message"],
            "order_id": result["order_id"]
        }

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Stock Status endpoint
@app.get("/api/products/{sku}/stock", response_model=InventoryResponse)
async def get_stock(sku: str, db: AsyncSession = Depends(get_db)):
    statement = select(Product).where(Product.sku == sku)
    result = await db.execute(statement)
    product = result.scalars().first()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")

    return InventoryResponse(
        sku=product.sku,
        available=product.stock_level - product.reserved_stock,
        reserved=product.reserved_stock,
        total=product.stock_level
    )

# Root info -> documentation about all available endpoints
@app.get("/info")
async def info():
    return {
        "title": "Inventory Sync Engine v1.0.0",
        "endpoints": {
            "/": "Health check",
            "/api/webhooks/order-created": "Receive order notification (POST)",
            "/api/products/{sku}/stock": "Get stock status (GET)",
            "/docs": "Swagger UI documentation"
        },
        "features": [
            "Race condition prevention via optimistic locking",
            "Idempotent webhook processing",
            "Two-stage stock reservation system"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)