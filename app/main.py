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
	title = "Inventory Sync Engine",
	version = "1.0.0",
	description = "Real-time inventory management system preventing race conditions"
)

# Pydantic models for request / response validation
# request
class WebhookPayload(BaseModel):
	order_id: str
	product_sku: str
	quantity: int
	idempotency_key: Optional[str] = None

# response
class InventoryResponse(BaseModel):
	sku: str
	available: int
	reserved: int
	total: int

# Startup event -> Creates database tables when app first runs
# Create all database tables defines in models if they don't exist
@app.on_event("startup")
async def create_tables():

	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.created_all)
	print("Database tables successfully created")

# Health check endpoint
# Endpoint to verify API is running
@app.get("/")
async def health_check():

	return {"status": "healthy", "service": "Inventory Sync Engine"}

# WEBHOOK receving endpoint
# Receives order notifcations from external systems (eg. Shopify, Amazon)
# Handles stock reservations and prevents overselling
@app.post("/api/webhooks/order-created")
async def receive_order(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):

	try:
		# Use payload.order_id as the idempotency key if not provided
		key = payload.idempotency_key or payload.order_id

		result = await process_webhook_order(db, key, payload.product_sku, payload.quantity)

		return {
			"status": "success",
			"message": result["message"],
			"order_id": result["order_id"]
		}

	except ValueError as e:
		# Stock insufficient or concurrent update conflict
		raise HTTPException(status_code = 409, detail = str(e))

	except Exception as e:
		# Unexpected error
		print(f"Unexpected error: {str(e)}")

# Stock Status endpoint
# Returns current stock levels for a give product SKU
@app.get("/api/products/{sku}/stock", response_model = InventoryResponse)
async def get_stock(sku: str, db: AsyncSession = Depends(get_db)):

	statement = select(Product).where(Product.sku == sku)
	result = await db.execute(statement)
	product = result.scalars().first()

	if not product:
		raise HTTPException(status_code = 404, details = f"Product with SKU '{sku}' not found")

	return InventoryResponse(
		sku = product.sku,
		available = product.stock_level - product.reserved_stock,
		reserved = product.reserved_stock,
		total = product.stock_level
	)
















