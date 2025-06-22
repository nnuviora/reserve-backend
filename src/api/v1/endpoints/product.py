from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, and_, or_

from database import get_db
from schemas.product_schema import *
from models.product_model import *

router = APIRouter(prefix="/product", tags=["Product"])


@router.post("/import", response_model=List[ProductDetailSchema],
    responses={
        200: {"description": "Дані успішно імпортовано"},
        400: {"description": "Невірні дані"},
        500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def import_products(
    products_data: List[ProductImportSchema],
    db: AsyncSession = Depends(get_db)
):
    try:
        imported_products = []
        for product_data in products_data:
            category_result = await db.execute(
                select(Category).where(Category.category_id == product_data.category.category_id)
            )
            category = category_result.scalar_one_or_none()
            if not category:
                category = Category(
                    category_id=product_data.category.category_id,
                    name=product_data.category.name,
                    description=product_data.category.description
                )
                db.add(category)
                await db.flush()

            subcategory_result = await db.execute(
                select(Subcategory).where(Subcategory.subcategory_id == product_data.subcategory.subcategory_id)
            )
            subcategory = Subcategory(
                subcategory_id=product_data.subcategory.subcategory_id,
                name=product_data.subcategory.name,
                description=product_data.subcategory.description,
                category_id=product_data.category.category_id
                )
            db.add(subcategory)
            await db.flush()

            brand_result = await db.execute(
                select(Brand).where(Brand.brand_id == product_data.brand.brand_id)
            )
            brand = brand_result.scalar_one_or_none()
            if not brand:
                brand = Brand(
                    brand_id=product_data.brand.brand_id,
                    name=product_data.brand.name,
                    description=product_data.brand.description,
                    logo_url=product_data.brand.logo_url
                )
                db.add(brand)
                await db.flush()
            
            product_result = await db.execute(
                select(Product).where(Product.product_id == product_data.product_id)
            )
            product = product_result.scalar_one_or_none()
            if product:
                product.name = product_data.name
                product.description = product_data.description
                product.price = product_data.price
                product.currency = product_data.currency
                product.availability = product_data.availability
                product.in_stock = product_data.in_stock
                product.stock_quantity = product_data.stock_quantity
                product.is_certified = product_data.is_certified
                product.certification_info = product_data.certification_info
                product.benefits = product_data.benefits
                product.usage_instructions = product_data.usage_instructions
                product.category_id = category.category_id
                product.subcategory_id = subcategory.subcategory_id
                product.brand_id = brand.brand_id
            else:
                product = Product(
                    product_id=product_data.product_id,
                    name=product_data.name,
                    description=product_data.description,
                    small_description=product_data.description[:200],
                    price=product_data.price,
                    currency=product_data.currency,
                    availability=product_data.availability,
                    in_stock=product_data.in_stock,
                    stock_quantity=product_data.stock_quantity,
                    is_certified=product_data.is_certified,
                    certification_info=product_data.certification_info,
                    benefits=product_data.benefits,
                    usage_instructions=product_data.usage_instructions,
                    category_id=category.category_id,
                    subcategory_id=subcategory.subcategory_id,
                    brand_id=brand.brand_id,
                    product_image=product_data.images[0].image_url if product_data.images else None
                )
                db.add(product)
                await db.flush()
            
            for image_data in product_data.images:
                image_result = await db.execute(
                    select(ProductImage).where(ProductImage.product_image_id == image_data.product_image_id)
                )
                image = image_result.scalar_one_or_none()
                if not image:
                    image = ProductImage(
                        product_image=image_data.product_image_id,
                        product_id=product.product_id,
                        image_description=image_data.image_description,
                        image_url={
                            "small": image_data.image_url,
                            "medium": image_data.image_url,
                            "large": image_data.image_url
                        },
                        is_main=image_data.is_main,
                        sort_order=image_data.sort_order
                    )
                    db.add(image)
                    await db.flush()

            imported_products.append(product)

        await db.commit()

        result = await db.execute(
            select(Product).options(
                joinedload(Product.images),
                joinedload(Product.reviews),
                joinedload(Product.features),
                joinedload(Product.variations),
                joinedload(Product.category),
                joinedload(Product.subcategory),
                joinedload(Product.brand)
            ).where(Product.product_id.in_([p.product_id for p in imported_products]))
        )
        products = result.scalars().all()
        return [ProductDetailSchema.from_orm(p) for p in products]
    
    except ValueError as e:
        await db.rollback()
        raise HTTPException(400, detail=f"Некоректні дані: {str(e)}")
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")


@router.get("/products/{product_id}",
            responses={
        200: {"description": "Товар знайдено"},
        404: {"description": "Товар не знайдено"},
        500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},   
}
)
async def get_product(product_id: int):
    try:
        if product_id <= 0:
            raise HTTPException(404, detail="Товар не знайдено")
        
        return {"product_id": product_id}
    
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")
    

@router.get("/categories/{category_id}", 
            responses={
        200: {"description": "Категорія знайдена"},
        404: {"description": "Категорію не знайдено"},
        500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_category(category_id: int):
    try:
        if category_id <= 0:
            raise HTTPException(404, detail="Категорію не знайдено")
        
        return {"category_id": category_id}
    
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")
    

@router.get("/subcategories/{subcategory_id}",
            responses={
        200: {"description": "Підкатегорія знайдена"},
        404: {"description": "Підкатегорію не знайдено"},
        500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_subcategory(subcategory_id: int):
    try:
        if subcategory_id <= 0:
            raise HTTPException(404, detail="Підкатегорію не знайдено")
    
        return {"subcategory_id": subcategory_id}
    
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

@router.get("/products/{product_id}/categories/{category_id}",
            responses={
        200: {"description": "Зв’язок знайдено"},
        404: {"description": "Неприпустимі значення ID"},
        500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_product_category(product_id: int, category_id: int):
    try:
        if product_id <= 0 or category_id <= 0:
            raise HTTPException(404, detail="Неприпустимі значення ID")
        
        return {"product_id": product_id, "category_id": category_id}
    
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")


@router.get("/catalog",
            responses={
                200: {"description": "Відповідь успішна"},
                400: {"description": "Некоректні параметри фільтрації"},
                404: {"description": "За заданими фільтрами товари не знайдено"},
                422: {"description": "Некоректні параметри запиту"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
            },
            )
async def get_product_catalog(
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=100),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_certified: Optional[bool] = None,
    in_stock: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        filters = []

        if category:
            filters.append(Product.category.has(name=category))

        if brand:
            filters.append(Product.brand.has(name=brand))

        if min_price is not None:
            filters.append(Product.price >= min_price)

        if max_price is not None:
            filters.append(Product.price <= max_price)

        if is_certified is not None:
            filters.append(Product.is_certified == is_certified)

        if in_stock is not None:
            filters.append(Product.in_stock == in_stock)

        if search:
            filters.append(or_(
                Product.name.ilike(f"%{search}%"),
                Product.small_description.ilike(f"%{search}%")
            ))

        query = select(Product).options(
            joinedload(Product.reviews),
            joinedload(Product.features),
            joinedload(Product.images)
        )
        if filters:
            query = query.where(and_(*filters))

        count_query = select(func.count(Product.product_id))
        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await db.execute(count_query)
        total_count = total_result.scalar()

        if total_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="За заданими фільтрами товари не знайдено"
            )

        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        products = result.scalars().all()

        product_cards = []
        for p in products:
            avg_rating = round(sum(r.rating for r in p.reviews) / len(p.reviews), 1) if p.reviews else 0.0
            product_cards.append({
                "product_id": p.product_id,
                "name": p.name,
                "price": float(p.price),
                "currency": "UAH",
                "average_rating": avg_rating,
                "small_description": p.small_description,
                "main_image_url": p.main_image_url,
                "category_name": p.category,
                "brand_name": p.brand,
                "is_certified": p.is_certified,
                "in_stock": p.in_stock,

            "features": [
                {
                    "feature_id": f.feature_id,
                    "feature_name": f.feature_name,
                    "feature_text": f.feature_text,
                }
                for f in p.features
            ],

            "images": [
                {
                    "image_url": i.image_url,
                    "image_description": i.image_description,
                }
                for i in p.images
            ]
            })

        return {
            "products": product_cards,
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": (total_count + per_page - 1) // per_page,
            "has_next": page * per_page < total_count,
            "has_prev": page > 1
        }
    
    except HTTPException:
        raise

    except ValueError:
        raise HTTPException(400, detail="Некоректні параметри запиту")
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")


@router.get("/search/suggestions", response_model=List[ProductSearchSuggestionSchema],
            responses={
                200: {"description": "Список знайдених товарів"},
                400: {"description": "Пошукова фраза занадто коротка"},
                404: {"description": "Товари не знайдено"},
                422: {"description": "Некоректні параметри запиту"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
            })
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Пошукова фраза"),
    limit: int = Query(10, ge=1, le=20, description="Максимальна кількість результатів"),
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Product).where(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%")
            )
        ).limit(limit)
        result = await db.execute(stmt)
        products = result.scalars().all()

        return[
            ProductSearchSuggestionSchema(
                product_id=p.product_id,
                name=p.name,
                category_name=p.category,
                brand_name=p.brand
            ) for p in products
        ]
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

@router.post("/compare", response_model=List[ProductComparisonSchema],
             responses={
                 200: {"description": "Список знайдених товарів"},
                 400: {"description": "Мінімум 2 товари для порівняння, максимум 5"},
                 404: {"description": "Товари не знайдено"},
                 422: {"description": "Некоректні параметри запиту"},
                 500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
             }
             )
async def compare_products(
    product_id: list[int],
    db: AsyncSession = Depends(get_db)
):
    try:
        if len(product_id) < 2:
            raise HTTPException(400, detail="Мінімум 2 товари для порівняння")
        
        if len(product_id) > 5:
            raise HTTPException(400, detail="Максимум 5 товарів для порівняння")
        
        stmt = select(Product).where(Product.product_id.in_(product_id))
        result = await db.execute(stmt)
        products = result.scalars().all()

        if len(products) != len(product_id):
            raise HTTPException(404, "Деякі товари не знайдено")

        return [ProductComparisonSchema.from_orm(p) for p in products]
    
    except Exception:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")


@router.post("/subscribe", response_model=ProductSubscriptionResponse,
             responses={
                 200: {"description": "Підписка оформлена"},
                 400: {"description": "Невірні дані підписки"},
                 404: {"description": "Товар не знайдено"},
                 500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def subscribe(
    data: ProductSubscriptionSchema,
    db: AsyncSession = Depends(get_db)):
    try:
        product = await db.get(Product, data.product_id)
        if not product:
            raise HTTPException(404, detail="Товар не знайдено")
        
        subscription = ProductSubscription(
            product_id=data.product_id,
            email=data.email,
        )
        db.add(subscription)
        await db.commit()

        return ProductSubscriptionResponse(
            message="Підписка оформлена"
        )
    except Exception:
        raise

    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")


@router.get("/{product_id}", response_model=ProductDetailSchema,
            responses={
                200: {"description": "Детальна інформація про товар"},
                404: {"description": "Товар не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
}
)
async def get_product_detail(product_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Product).options(
            joinedload(Product.images),
            joinedload(Product.reviews),
            joinedload(Product.features),
            joinedload(Product.variations)
        ).where(Product.product_id == product_id)

        result = await db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(404, detail="Товар не знайдено")

        return ProductDetailSchema.from_orm(product)
    
    except Exception:
        raise

    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")


@router.get("/{product_id}/recommended", response_model=List[ProductRecommendationSchema],
            responses={
                200: {"description": "Рекомендовані товари"},
                404: {"description": "Товар не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_recommended(product_id: int, db: AsyncSession = Depends(get_db)):
    try:
        product = await db.get(Product, product_id)
        if not product:
            raise HTTPException(404, detail="Товар не знайдено")
        
        stmt = select(Product).where(Product.product_id != product_id).limit(5)
        result = await db.execute(stmt)
        return [ProductRecommendationSchema.from_orm(p) for p in result.scalars().all()]
    
    except Exception:
        raise

    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")


@router.get("/{product_id}/prices", response_model=List[ProductVariationPriceSchema],
            responses={
                200: {"description": "Ціни за варіаціями"},
                404: {"description": "Варіації не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_price_with_variations(
    product_id: int, 
    variation_type: Optional[str] = None,
    variation_value: Optional[str] = None,
    db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(ProductVariation).where(ProductVariation.product_id == product_id)

        if variation_type:
            stmt = stmt.where(ProductVariation.variation_type == variation_type)
        if variation_value:
            stmt = stmt.where(ProductVariation.variation_value == variation_value)

        result = await db.execute(stmt)
        variation = result.scalars().all()

        if not variation:
            raise HTTPException(404, detail="Варіацію не знайдено")
    
        return [ProductVariationPriceSchema.from_orm(v) for v in variation]
    
    except Exception:
        raise

    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")