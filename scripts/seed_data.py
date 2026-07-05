import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select
from app.models import Product, Base
from app.database import DATABASE_URL, AsyncLocalSession, Base


async def seed():
    
    # Create tables from models
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")
    
    # Sample products
    sample_products = [
        {"sku": "WATCH-001", "name": "Luxury Silver Watch", "stock_level": 100},
        {"sku": "PHONE-CASE-IPHONE", "name": "iPhone 15 Pro Case - Black", "stock_level": 500},
        {"sku": "SCREEN-PROTECTOR-SAMSUNG", "name": "Galaxy S24 Screen Protector", "stock_level": 750}
    ]
    
    async with AsyncLocalSession() as session:
        for product_data in sample_products:
            existing = await session.execute(
                select(Product).where(Product.sku == product_data["sku"])
            )
            
            if not existing.scalars().first():
                new_product = Product(**product_data)
                session.add(new_product)
                print(f"✓ Created: {product_data['sku']} ({product_data['stock_level']} units)")
            else:
                print(f"- Exists: {product_data['sku']}")
        
        await session.commit()
        print("\n🎉 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())

    