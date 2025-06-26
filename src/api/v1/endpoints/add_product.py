from __future__ import annotations
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, and_, or_

from database import get_db
from schemas.product_schema import *
from models.product_model import *

router = APIRouter(prefix="/add-product", tags=["Add product - for internal use"])


@router.post("/add_item", response_model=ProductDetailSchema)
async def add_product(
    product_data: ProductDetailSchema,
    db: AsyncSession = Depends(get_db),
):
    try:
        product_fields = product_data.dict(exclude={
            "average_rating", "review_count",
            "traits", "images", "features",
            "reviews", "variations",
            "category", "subcategory", "brand"
        })

        # Prepare related nested models
        traits_list = [Traits(**t.dict()) for t in product_data.traits] if product_data.traits else []
        images_list = [ProductImage(**i.dict()) for i in product_data.images] if product_data.images else []
        features_list = [Feature(**f.dict()) for f in product_data.features] if product_data.features else []
        reviews_list = [Review(**r.dict()) for r in product_data.reviews] if product_data.reviews else []
        variations_list = [ProductVariation(**v.dict()) for v in product_data.variations] if product_data.variations else []

        new_product = Product(**product_fields)
        
        # Attach nested relationships
        new_product.traits = traits_list[0] if traits_list else None  # Assuming one-to-one
        new_product.images = images_list
        new_product.features = features_list
        new_product.reviews = reviews_list
        new_product.variations = variations_list

        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        return await new_product.to_dict()  # or use a converter if needed

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating product: {str(e)}")


###add category
###add subcaterody
# add brand


@router.post("/add_category", response_model=CategorySchema)
async def add_category(
    data_to_add: CategorySchema,
    db: AsyncSession = Depends(get_db),
):
    new_category = Category(**data_to_add.dict())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category


###
@router.post("/add_subcategory", response_model=SubCategorySchema)
async def add_category(
    data_to_add: SubCategorySchema,
    db: AsyncSession = Depends(get_db),
):
    new_sub_category = Subcategory(**data_to_add.dict(exclude_unset=True))
    db.add(new_sub_category)
    await db.commit()
    await db.refresh(new_sub_category)
    return new_sub_category


###
@router.post("/add_brand", response_model=BrandSchema)
async def add_category(
    data_to_add: BrandSchema,
    db: AsyncSession = Depends(get_db),
):
    new_brand = Brand(**data_to_add.dict(exclude_unset=True))
    db.add(new_brand)
    await db.commit()
    await db.refresh(new_brand)
    return new_brand


@router.post("/add_trait", response_model=TraitsSchema)
async def add_category(
    data_to_add: TraitsSchema,
    db: AsyncSession = Depends(get_db),
):
    new_trait = Brand(**data_to_add.dict())
    db.add(new_trait)
    await db.commit()
    await db.refresh(new_trait)
    return new_trait
