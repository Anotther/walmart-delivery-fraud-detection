"""
SQLAlchemy ORM models for Walmart Fraud Detection.
"""
from datetime import date, time
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, Integer, Date, Time, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base


class Customer(Base):
    """Customer model - stores customer information."""

    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_age: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")

    __table_args__ = (CheckConstraint("customer_age > 0", name="check_customer_age"),)

    def __repr__(self) -> str:
        return f"<Customer(id={self.customer_id}, name={self.customer_name})>"


class Driver(Base):
    """Driver model - stores delivery driver information."""

    __tablename__ = "drivers"

    driver_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    driver_name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[Optional[int]] = mapped_column(Integer)
    trips: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="driver")

    __table_args__ = (
        CheckConstraint("age >= 18", name="check_driver_age"),
        CheckConstraint("trips >= 0", name="check_trips"),
    )

    def __repr__(self) -> str:
        return f"<Driver(id={self.driver_id}, name={self.driver_name})>"


class Product(Base):
    """Product model - stores product catalog information."""

    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    __table_args__ = (CheckConstraint("price >= 0", name="check_price"),)

    def __repr__(self) -> str:
        return f"<Product(id={self.product_id}, name={self.product_name})>"


class Order(Base):
    """Order model - main fact table for delivery orders."""

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    order_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    items_delivered: Mapped[int] = mapped_column(Integer, default=0)
    items_missing: Mapped[int] = mapped_column(Integer, default=0)
    delivery_hour: Mapped[Optional[time]] = mapped_column(Time)
    driver_id: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("drivers.driver_id")
    )
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("customers.customer_id")
    )

    # Relationships
    driver: Mapped[Optional["Driver"]] = relationship("Driver", back_populates="orders")
    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer", back_populates="orders"
    )
    missing_items: Mapped[Optional["MissingItem"]] = relationship(
        "MissingItem", back_populates="order", uselist=False
    )

    __table_args__ = (
        CheckConstraint("order_amount >= 0", name="check_order_amount"),
        CheckConstraint("items_delivered >= 0", name="check_items_delivered"),
        CheckConstraint("items_missing >= 0", name="check_items_missing"),
    )

    @property
    def total_items(self) -> int:
        """Total items in the order."""
        return self.items_delivered + self.items_missing

    @property
    def missing_rate(self) -> float:
        """Percentage of items missing."""
        if self.total_items == 0:
            return 0.0
        return (self.items_missing / self.total_items) * 100

    def __repr__(self) -> str:
        return f"<Order(id={self.order_id}, date={self.order_date}, region={self.region})>"


class MissingItem(Base):
    """MissingItem model - links orders to missing products."""

    __tablename__ = "missing_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("orders.order_id"))
    product_id_1: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("products.product_id")
    )
    product_id_2: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("products.product_id")
    )
    product_id_3: Mapped[Optional[str]] = mapped_column(
        String(30), ForeignKey("products.product_id")
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="missing_items")
    product_1: Mapped[Optional["Product"]] = relationship(
        "Product", foreign_keys=[product_id_1]
    )
    product_2: Mapped[Optional["Product"]] = relationship(
        "Product", foreign_keys=[product_id_2]
    )
    product_3: Mapped[Optional["Product"]] = relationship(
        "Product", foreign_keys=[product_id_3]
    )

    @property
    def missing_product_ids(self) -> List[str]:
        """Get list of all missing product IDs."""
        products = []
        if self.product_id_1:
            products.append(self.product_id_1)
        if self.product_id_2:
            products.append(self.product_id_2)
        if self.product_id_3:
            products.append(self.product_id_3)
        return products

    def __repr__(self) -> str:
        return f"<MissingItem(order_id={self.order_id}, products={len(self.missing_product_ids)})>"
