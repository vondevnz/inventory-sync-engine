from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

# stock_level and reserved_stock ensures no overselling
# if a customer abandons their cart the reserved stock will decrease

# creates sql products table (inherits Base)
class Product(Base):
	__tablename__ = "products"

	id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
	sku = Column(String(50), unique = True, index = True, nullable = False)
	name = Column(String(100), nullable = False)
	stock_level = Column(Integer, default = 0)
	reserved_stock = Column(Integer, default = 0)
	updated_at = Column(DateTime(timezone = True), server_default = func.now(), onupdate = func.now())

	# Ensure stock never goes negative
	__table_args__ = (
		CheckConstraint('stock_level + reserved_stock >= 0', name = 'check_total_stock_non_negative'),
	)

# creates sql order_reservations table (inherits Base)
class OrderReservation(Base):
	__tablename__ = "order_reservations"

	id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
	order_id = Column(String(50), unique = True, index = True, nullable = False)
	product_id = Column(UUID(as_uuid = True), ForeignKey("products.id"), nullable = False)
	quantity = Column(Integer, nullable = False)
	status = Column(String(20), default="reserved") # reserved, confirmed, cancelled
	created_at = Column(DateTime(timezone = True), server_default = func.now())