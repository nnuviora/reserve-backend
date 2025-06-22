from datetime import datetime
import uuid
from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class Category(Base):
    __tablename__ = "category"

    category_id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    #icon: Mapped[str] = mapped_column(String, nullable=True)

    subcategories = relationship("Subcategory", back_populates="category")
    products = relationship("Product", back_populates="category")

    async def to_dict(self):
        return {
            "category_id": self.category_id,
            "name": self.name,
            "description": self.description,
            #"icon": self.icon
        }

class Subcategory(Base):
    __tablename__ = "subcategory"

    subcategory_id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)

    category_id: Mapped[int] = mapped_column(ForeignKey("category.category_id"))

    category: Mapped["Category"] = relationship(back_populates="subcategories")
    products = relationship("Product", back_populates="subcategory")

    async def to_dict(self):
        return {
            "subcategory_id": self.subcategory_id,
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id
        }
    
class Brand(Base):
    __tablename__ = "brand"

    brand_id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    logo_url: Mapped[str] = mapped_column(String, nullable=True)

    products = relationship("Product", back_populates="brand")

    async def to_dict(self):
        return {
            "brand_id": self.brand_id,
            "name": self.name,
            "description": self.description,
            "logo_url": self.logo_url
        }
    
class Product(Base):
    __tablename__ = "product"

    product_id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    small_description: Mapped[str] = mapped_column(Text)
    #traits_id: Mapped[int] = mapped_column(ForeignKey("traits.traits_id"))
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    availability: Mapped[bool] = mapped_column(Boolean)
    currency: Mapped[str] = mapped_column(String(10))
    in_stock: Mapped[bool] = mapped_column(Boolean)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.category_id"))
    subcategory_id: Mapped[int] = mapped_column(ForeignKey("subcategory.subcategory_id"))
    product_image: Mapped[str] = mapped_column(String)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brand.brand_id"), nullable=True)

    is_certified: Mapped[bool] = mapped_column(Boolean, default=False)
    certification_info: Mapped[str] = mapped_column(Text, nullable=True)
    benefits: Mapped[str] = mapped_column(Text, nullable=True)
    usage_instructions: Mapped[str] = mapped_column(Text, nullable=True)

    category = relationship("Category", back_populates="products")
    subcategory = relationship("Subcategory", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    traits = relationship("Traits", back_populates="product")
    images = relationship("ProductImage", back_populates="product")
    features = relationship("Feature", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    variations = relationship("ProductVariation", back_populates="product")
    subscription = relationship("ProductSubscription", back_populates="product")


    async def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "small_description": self.small_description,
            "traits_id": self.traits_id,
            "price": self.price,
            "availability": self.availability,
            "currency": self.currency,
            "in_stock": self.in_stock,
            "stock_quantity": self.stock_quantity,
            "category_id": self.category_id,
            "subcategory_id": self.subcategory_id,
            "product_image": self.product_image,
            "brand_id": self.brand_id,
            "is_certified": self.is_certified,
            "certification_info": self.certification_info,
            "benefits": self.benefits,
            "usage_instructions": self.usage_instructions,
        }
    
    @property
    def average_rating(self):
        if not self.reviews:
            return 0.0
        return sum(review.rating for review in self.reviews) / len(self.reviews)

class ProductVariation(Base):
    __tablename__ = "product_variation"

    variations_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"))
    variation_type: Mapped[str] = mapped_column(String) # color, size, etc.
    variation_value: Mapped[str] = mapped_column(String) # red, small, etc.
    price_modifier: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0.0)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped["Product"] = relationship(back_populates="variations")

    async def to_dict(self):
        return {
            "variations_id": self.variations_id,
            "product_id": self.product_id,
            "variation_type": self.variation_type,
            "variation_value": self.variation_value,
            "price_modifier": self.price_modifier,
            "stock_quantity": self.stock_quantity,
        }
    
class Traits(Base):
    __tablename__ = "traits"

    traits_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"))
    traits_name: Mapped[str] = mapped_column(String)
    traits_text: Mapped[str] = mapped_column(Text)

    product: Mapped["Product"] = relationship(back_populates="traits")

    async def to_dict(self):
        return {
            "traits_id": self.traits_id,
            "product_id": self.product_id,
            "traits_name": self.traits_name,
            "traits_text": self.traits_text,
    }

class ProductImage(Base):
    __tablename__ = "product_image"

    product_image_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"))
    image_description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped["Product"] = relationship(back_populates="images")

    async def to_dict(self):
        return {
            "product_image_id": self.product_image_id,
            "product_id": self.product_id,
            "image_description": self.image_description,
            "image_urls": self.image_urls,
            "is_main": self.is_main,
            "sort_order": self.sort_order
        }

class Feature(Base):
    __tablename__ = "feature"

    feature_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"))
    feature_name: Mapped[str] = mapped_column(String)
    feature_text: Mapped[str] = mapped_column(Text)
    feature_value: Mapped[str] = mapped_column(String, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="features")

    async def to_dict(self):
        return {
            "feature_id": self.feature_id,
            "product_id": self.product_id,
            "feature_name": self.feature_name,
            "feature_text": self.feature_text,
            "feature_value": self.feature_value
        }
    
class Review(Base):
    __tablename__ = "review"

    review_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"))
    rating: Mapped[int] = mapped_column(Integer)
    review_text: Mapped[str] = mapped_column(Text)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="reviews")

    async def to_dict(self):
        return {
            "review_id": self.review_id,
            "product_id": self.product_id,
            "rating": self.rating,
            "review_text": self.review_text,
            "reviewer_name": self.reviewer_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_id": str(self.user_id) if self.user_id else None
        }
    
class ProductSubscription(Base):
    __tablename__ = "product_subscription"

    subscription_id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"))
    email: Mapped[str] = mapped_column(String)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())

    product: Mapped["Product"] = relationship(back_populates="subscription")

    async def to_dict(self):
        return {
            "subscription_id": self.subscription_id,
            "product_id": self.product_id,
            "email": self.email,
            "is_notified": self.is_notified,
            "created_at": self.created_at
        }