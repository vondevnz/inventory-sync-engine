from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import Product, OrderReservation


async def process_webhook_order(db: AsyncSession, order_id: str, product_sku: str, quantity: int):
    """Handles incoming order webhook with two safeguards."""
    
    # STEP 1: Idempotency Check
    existing = await db.execute(
        select(OrderReservation).where(OrderReservation.order_id == order_id)
    )
    
    if existing.scalars().first():
        return {
            "status": "success",
            "message": "Order already processed (idempotent)",
            "order_id": order_id
        }
    
    # STEP 2: Atomic Stock Deduction - CHECK FIRST, THEN UPDATE
    # Instead of relying on rowcount (which breaks with async), we verify existence first
    
    check_stmt = (
        select(Product)
        .where(Product.sku == product_sku)
        .with_for_update()  # Lock row while checking
    )
    
    check_result = await db.execute(check_stmt)
    product = check_result.scalars().first()
    
    if not product or product.stock_level < quantity:
        raise ValueError("Stock insufficient or concurrent update conflict")
    
    # Now perform the atomic update
    stmt_update = (
        update(Product)
        .where(Product.sku == product_sku)
        .where(Product.stock_level >= quantity)
        .values(
            stock_level=Product.stock_level - quantity,
            reserved_stock=Product.reserved_stock + quantity,
        )
        .returning(Product.id)
    )
    
    update_result = await db.execute(stmt_update)
    product_id = update_result.scalar_one()  # Get the returned ID
    
    # STEP 3: Create Reservation Record
    new_reservation = OrderReservation(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        status="reserved"
    )
    
    db.add(new_reservation)
    await db.commit()
    await db.refresh(new_reservation)
    
    return {
        "status": "success",
        "order_id": order_id,
        "message": f"Reserved {quantity} units of SKU {product_sku}"
    }