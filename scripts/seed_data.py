"""
Seed Script - Populates database with test products
Run: docker-compose exec app python scripts/seed_data.py
"""

import asyncio
import sys
sys.path.append('/app')  # Ensure Python can find 'app' module

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import Product, Base
from app.database import DATABASE_URL, AsyncLocalSession


async def seed():
    """Creates tables and inserts sample products."""
    
    print("Starting seed process...")
    
    # Create engine for table creation
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")
    
    # Sample products
    sample_products = [
        {"sku": "WATCH-001", "name": "Luxury Silver Watch", "stock_level": 100},
        {"sku": "PHONE-CASE-IPHONE", "name": "iPhone 15 Pro Case - Black", "stock_level": 500},
        {"sku": "SCREEN-PROTECTOR-SAMSUNG", "name": "Galaxy S24 Screen Protector (Pack of 3)", "stock_level": 750}
    ]
    
    async with AsyncLocalSession() as session:
        for product_data in sample_products:
            # Check if product already exists
            existing = await session.execute(
                select(Product).where(Product.sku == product_data["sku"])
            )
            
            if not existing.scalars().first():
                new_product = Product(**product_data)
                session.add(new_product)
                print(f"✓ Created: {product_data['sku']} ({product_data['stock_level']} units)")
            else:
                print(f"- Already exists: {product_data['sku']}")
        
        await session.commit()
    
    print("\nSeed complete! Database populated with test products.")
    print("You can now test the API at http://localhost:8000/api/products/WATCH-001/stock")


if __name__ == "__main__":
    asyncio.run(seed())