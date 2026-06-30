from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from app.models import Product, OrderReservation

async def process_webhook_order(db: AsyncSession, order_id: str, product_sku: str, quantity: int):

	existing = await db.execute(
		select(OrderReservation).where(OrderReservation.order_id == order_id)
	)

	if existing.scalars().first():
		return {
			"status": "success",
			"message": "Order already processed (idempotent)"
			"order_id": order_id
		}

	stmt_update = {
		update(Product)
		.where(Product.sku == product_sku)
		.where(Product.stock_level == >= quantity)
		.values(
			stock_level = Product.stock_level - quantity,
			reserved_stock = Product.reserved_stock + quantity,
		)
		.returning(Product.id)
	}

	result = await db.execute(stmt_update)
	rows_affected = result.rowcount

	if rows_affected == 0:

		raise ValueError("Stock insufficient or concurrent update conflict")

	product_id = result.scalar_one()

	new_reservation = OrderReservation(
		order_id = order_id,
		product_id = product_id,
		quantity = quantity,
		status = "reserved"
	)

	db.add(new_reservation)

	await db.commit()
	await db.refresh(new_reservation)

	return {
		"status": "success",
		"order_id": order_id,
		"message": f"Reserved {quantity} units pf SKU {product_sku}"
	}





