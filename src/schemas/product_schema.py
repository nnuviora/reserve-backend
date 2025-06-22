from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Optional, List


class CategorySchema(BaseModel):
    category_id: Optional[int] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    #icon: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class SubCategorySchema(BaseModel):
    subcategory_id: Optional[int] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    category_id: Optional[int] = Field(default=None)

    class Config:
        from_attributes = True


class BrandSchema(BaseModel):
    brand_id: Optional[int] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    logo_url: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True

class TraitsSchema(BaseModel):
    trait_id: Optional[int] = Field(default=None)
    traits_name: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class ProductImageSchema(BaseModel):
    product_image_id: Optional[int] = Field(default=None)
    image_description: Optional[str] = Field(default=None)
    image_url: str
    is_main: Optional[bool] = Field(default=False)
    sort_order: Optional[int] = Field(default=0)

    class Config:
        from_attributes = True


class FeatureSchema(BaseModel):
    feature_id: Optional[int] = Field(default=None)
    feature_name: Optional[str] = Field(default=None)
    feature_text: Optional[str] = Field(default=None)
    feature_value: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class ReviewSchema(BaseModel):
    review_id: Optional[int] = Field(default=None)
    rating: Optional[int] = Field(default=None)
    review_text: Optional[str] = Field(default=None)
    reviewer_name: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None)

    class Config:
        from_attributes = True


class ProductVariationSchema(BaseModel):
    variation_id: Optional[int] = Field(default=None)
    variation_type: Optional[str] = Field(default=None)
    variation_value: Optional[str] = Field(default=None)
    price_modifier: Optional[float] = Field(default=None)
    stock_quantity: Optional[int] = Field(default=None)

    class Config:
        from_attributes = True


class ProductCardSchema(BaseModel):
    product_id: int
    name: str
    price: float
    currency: str = "UAH"
    average_rating: Optional[float] = 0.0
    small_description: Optional[str] = Field(default=None)
    main_image_urls: Dict[str, Optional[str]] = Field(default={"small": None, "medium": None, "large": None})
    category_name: Optional[str] = None
    brand_name: Optional[str] = None
    is_certified: Optional[bool] = False
    in_stock: bool = True
    
    class Config:
        from_attributes = True


class ProductDetailSchema(BaseModel):
    product_id: int
    name: str
    description: str
    small_description: Optional[str] = None
    traits_id: Optional[int] = None
    price: float
    currency: str = "UAH"
    availability: bool = True
    in_stock: bool = True
    stock_quantity: int = 0
    is_certified: bool = False
    certification_info: Optional[str] = None
    benefits: Optional[str] = None
    usage_instructions: Optional[str] = None

    average_rating: Optional[float] = 0.0
    review_count: Optional[int] = 0

    category: Optional[CategorySchema] = None
    subcategory: Optional[SubCategorySchema] = None
    brand: Optional[BrandSchema] = None
    traits: Optional[List[TraitsSchema]] = None
    images: List[ProductImageSchema] = []
    features: List[FeatureSchema] = []
    reviews: List[ReviewSchema] = []
    variations: List[ProductVariationSchema] = []

    class Config:
        from_attributes = True


class ProductSearchSuggestionSchema(BaseModel):
    product_id: int
    name: str
    category_name: Optional[str] = None
    brand_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductComparisonSchema(BaseModel):
    product_id: int
    name: str
    price: float
    currency: str = "UAH"
    brand_name: Optional[str] = None
    image_url: Optional[str] = None
    features: List[FeatureSchema] = []
    average_rating: Optional[float] = 0.0

    class Config:
        from_attributes = True


class ProductRecommendationSchema(BaseModel):
    product_id: int
    name: str
    price: float
    currency: str = "UAH"
    main_image_url: Optional[str] = None
    average_rating: Optional[float] = 0.0
    small_description: Optional[str] = None

    class Config:
        from_attributes = True


class ProductSubscriptionSchema(BaseModel):
    product_id: int
    email: EmailStr

    class Config:
        from_attributes = True


class ProductSubscriptionResponse(BaseModel):
    message: str

    class Config:
        from_attributes = True


class ProductFiltersSchema(BaseModel):
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    brand_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_certified: Optional[bool] = None
    in_stock_only: Optional[bool] = None
    min_rating: Optional[float] = None
    search_query: Optional[str] = None


class ProductCatalogResponse(BaseModel):
    products: List[ProductCardSchema]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True


class PriceRangeSchema(BaseModel):
    min_price: float
    max_price: float

    class Config:
        from_attributes = True


class ProductVariationPriceSchema(BaseModel):
    base_price: float
    variations: List[ProductVariationSchema]
    total_price: float
    currency: str = "UAH"

    class Config:
        from_attributes = True


class ProductImportSchema(BaseModel):
    product_id: int
    name: str
    description: str
    traits_id: Optional[int] = None
    price: float
    currency: str = "UAH"
    availability: bool = True
    in_stock: bool = True
    stock_quantity: int
    is_certified: bool = False
    certification_info: Optional[str] = None
    benefits: Optional[str] = None
    usage_instructions: Optional[str] = None
    average_rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    category: CategorySchema
    subcategory: SubCategorySchema
    brand: BrandSchema
    images: List[ProductImageSchema]
    features: List[FeatureSchema]
    reviews: List[ReviewSchema]
    variations: List[ProductVariationSchema]

    class Config:
        from_attributes = True