"""CRUD operations for products."""

from sqlalchemy import func

from . import database
from .base_crud import BaseCRUD
from .product import Product


class ProductCRUD(BaseCRUD[Product]):
    """CRUD operations for Product entities."""

    def __init__(self):
        super().__init__(Product)

    def create(
        self,
        reference: str,
        name: str = None,
        price: float | None = None,
        stock: int | None = None,
        sold: int | None = None,
    ) -> Product:
        """Create a new product.

        Args:
            reference: Product reference
            name: Product name (optional)
            price: Product price (optional)
            stock: Stock quantity (optional)
            sold: Sold quantity (optional)

        Returns:
            The created product
        """
        with database.SessionLocal() as session:
            product = Product(reference=reference, name=name, price=price, stock=stock, sold=sold)
            session.add(product)
            session.commit()
            session.refresh(product)
            return product

    def update(
        self,
        product_ref: str,
        name: str = None,
        price: float = None,
        stock: int = None,
        sold: int = None,
    ) -> Product | None:
        """Update an existing product.

        Args:
            product_ref: The product's reference (PK)
            name: New name (optional)
            price: New price (optional)
            stock: New stock quantity (optional)
            sold: New sold quantity (optional)

        Returns:
            The updated product if found, None otherwise
        """
        with database.SessionLocal() as session:
            product = session.query(Product).filter(Product.reference == product_ref).first()
            if product:
                if name is not None:
                    product.name = name
                if price is not None:
                    product.price = price
                if stock is not None:
                    product.stock = stock
                if sold is not None:
                    product.sold = sold
                session.commit()
                session.refresh(product)
            return product

    def _get_search_filters(self, query: str) -> list:
        """Get search filters for products.

        Searches in: reference, name
        """
        return [
            Product.reference.ilike(f"%{query}%"),
            Product.name.ilike(f"%{query}%"),
        ]

    def _get_sort_field(self):
        """Sort products by reference (case-insensitive)."""
        return func.lower(Product.reference)


# Create singleton instance
product_crud = ProductCRUD()
