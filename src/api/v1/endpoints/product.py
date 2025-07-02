from __future__ import annotations
import math
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
    products_data: List[ProductDetailSchema],
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
        raise HTTPException(status_code=400, detail=f"Некоректні дані: {str(e)}")
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")
    
@router.get("/products/{product_id}", response_model=ProductDetailSchema,
            responses={
                200: {"description": "Детальна інформація про товар"},
                404: {"description": "Товар не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
            })
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Product).options(
            joinedload(Product.images),
            joinedload(Product.reviews),
            joinedload(Product.features),
            joinedload(Product.variations),
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.brand)
        ).where(Product.product_id == product_id)
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(404, detail="Товар не знайдено")
        return ProductDetailSchema.from_orm(product)
    
    except HTTPException:
        raise

    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")
    

@router.get("/categories/{category_id}", response_model=CategorySchema,
            responses={
                200: {"description": "Детальна інформація про категорію"},
                404: {"description": "Категорію не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
            })
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Category).options(
            joinedload(Category.subcategories)
        ).where(Category.category_id == category_id)
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(404, detail="Категорію не знайдено")
        return CategorySchema.from_orm(category)
    
    except HTTPException:
        raise

    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")
    

@router.get("/subcategories/{subcategory_id}", response_model=SubCategorySchema,
            responses={
                200: {"description": "Детальна інформація про підкатегорію"},
                404: {"description": "Підкатегорію не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
            })
async def get_subcategory(subcategory_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Subcategory).options(
            joinedload(Subcategory.category)
        ).where(Subcategory.subcategory_id == subcategory_id)
        result = await db.execute(stmt)
        subcategory = result.scalar_one_or_none()
        if not subcategory:
            raise HTTPException(404, detail="Підкатегорію не знайдено")
        return SubCategorySchema.from_orm(subcategory)
        
    except HTTPException:
        raise

    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")


@router.get("/products/{product_id}/categories/{category_id}", response_model=ProductDetailSchema,
            responses={
                200: {"description": "Детальна інформація про товар"},
                404: {"description": "Товар не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_product_category(product_id: int, category_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Product).options(
            joinedload(Product.images),
            joinedload(Product.reviews),
            joinedload(Product.features),
            joinedload(Product.variations),
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.brand)
        ).where(and_(Product.product_id == product_id, Product.category_id == category_id))
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(404, detail="Товар не знайдено")
        return ProductDetailSchema.from_orm(product)
    
    except HTTPException:
        raise

    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")
    

@router.get("/catalog", response_model=ProductCatalogResponse,
            responses={
                200: {"description": "Відповідь успішна"},
                400: {"description": "Некоректні параметри фільтрації"},
                404: {"description": "За заданими фільтрами товари не знайдено"},
                422: {"description": "Некоректні параметри запиту"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
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
    sort_by: Optional[str] = Query(None, regex="^(name|price|created_at)$"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
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
            joinedload(Product.images),
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.brand)
        )
        if filters:
            query = query.where(and_(*filters))

        if sort_by:
            sort_column = getattr(Product, sort_by)
            query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

        count_query = select(func.count(Product.product_id))
        if filters:
            count_query = count_query.where(and_(*filters))

        total_result = await db.execute(count_query)
        total_count = total_result.scalar()

        if total_count is None or per_page is None:
            raise HTTPException(400, detail="Некоректні параметри запиту")

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
                "currency": p.currency,
                "average_rating": avg_rating,
                "small_description": p.small_description,
                "main_image_url": p.product_image,
                "category": {
                    "category_id": p.category.category_id,
                    "name": p.category.name,
                    "description": p.category.description
                },
                "subcategory": {
                    "subcategory_id": p.subcategory.subcategory_id,
                    "name": p.subcategory.name,
                    "description": p.subcategory.description
                },
                "brand": {
                    "brand_id": p.brand.brand_id,
                    "name": p.brand.name,
                    "logo_url": p.brand.logo_url
                },
                "is_certified": p.is_certified,
                "in_stock": p.in_stock,
                "stock_quantity": p.stock_quantity,
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
                        "is_main": i.is_main
                    }
                    for i in p.images
                ]
            })

        return {
            "products": product_cards,
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": math.ceil(total_count / per_page),
            "has_next": page < math.ceil(total_count / per_page),
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
                200: {"description": "Список знайдених товарів"},
                400: {"description": "Пошукова фраза занадто коротка"},
                404: {"description": "Товари не знайдено"},
                422: {"description": "Некоректні параметри запиту"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Пошукова фраза"),
    limit: int = Query(10, ge=1, le=20, description="Максимальна кількість результатів"),
    db: AsyncSession = Depends(get_db)
):
    try:
        stmt = select(Product).options(
            joinedload(Product.category),
            joinedload(Product.brand)
        ).where(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.description.ilike(f"%{query}%")
            )
        ).limit(limit)
        result = await db.execute(stmt)
        products = result.scalars().all()

        if not products:
            raise HTTPException(404, detail="Товари не знайдено")

        return [
            ProductSearchSuggestionSchema(
                product_id=p.product_id,
                name=p.name,
                category_name=p.category.name if p.category else None,
                brand_name=p.brand.name if p.brand else None,
                main_image_url=p.product_image
            ) for p in products
        ]
    
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

@router.post("/compare", response_model=List[ProductComparisonSchema],
             responses={
                 200: {"description": "Список знайдених товарів"},
                 400: {"description": "Мінімум 2 товари для порівняння, максимум 5"},
                 404: {"description": "Товари не знайдено"},
                 422: {"description": "Некоректні параметри запиту"},
                 500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def compare_products(
    product_ids: list[int] = Query(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        if len(product_ids) < 2:
            raise HTTPException(400, detail="Мінімум 2 товари для порівняння")
        
        if len(product_ids) > 5:
            raise HTTPException(400, detail="Максимум 5 товарів для порівняння")
        
        stmt = select(Product).options(
            joinedload(Product.features),
            joinedload(Product.variations),
            joinedload(Product.images),
            joinedload(Product.category),
            joinedload(Product.brand)
        ).where(Product.product_id.in_(product_ids))
        result = await db.execute(stmt)
        products = result.scalars().all()

        if len(products) != len(product_ids):
            raise HTTPException(404, detail="Деякі товари не знайдено")

        return [ProductComparisonSchema.from_orm(p) for p in products]
    
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

@router.post("/subscribe", response_model=ProductSubscriptionResponse,
             responses={
                 200: {"description": "Підписка оформлена"},
                 400: {"description": "Невірні дані підписки"},
                 404: {"description": "Товар не знайдено"},
                 500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def subscribe(
    product_id: int,
    data: ProductSubscriptionSchema,
    db: AsyncSession = Depends(get_db)):
    try:
        product = await db.get(Product, product_id)
        if not product:
            raise HTTPException(404, detail="Товар не знайдено")
        
        subscription = ProductSubscription(
            product_id=product_id,
            email=data.email,
        )
        db.add(subscription)
        await db.commit()

        return ProductSubscriptionResponse(
            message="Підписка оформлена",
            product_id=product_id,
            email=data.email
        )
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

@router.get("/{product_id}", response_model=ProductDetailSchema,
            responses={
                200: {"description": "Детальна інформація про товар"},
                404: {"description": "Товар не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_product_detail(product_id: int, db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(Product).options(
            joinedload(Product.images),
            joinedload(Product.reviews),
            joinedload(Product.features),
            joinedload(Product.variations),
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.brand)
        ).where(Product.product_id == product_id)

        result = await db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(404, detail="Товар не знайдено")

        return ProductDetailSchema.from_orm(product)
    
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

@router.get("/{product_id}/recommended", response_model=List[ProductRecommendationSchema],
            responses={
                200: {"description": "Рекомендовані товари"},
                404: {"description": "Товар не знайдено"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_recommended(product_id: int, limit: int = Query(5, ge=1, le=10), db: AsyncSession = Depends(get_db)):
    try:
        product = await db.get(Product, product_id)
        if not product:
            raise HTTPException(404, detail="Товар не знайдено")
        
        stmt = select(Product).options(
            joinedload(Product.category),
            joinedload(Product.brand)
        ).where(
            and_(
                Product.product_id != product_id,
                Product.category_id == product.category_id
            )
        ).limit(limit)
        result = await db.execute(stmt)
        return [ProductRecommendationSchema.from_orm(p) for p in result.scalars().all()]
    
    except HTTPException:
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
        variations = result.scalars().all()

        if not variations:
            raise HTTPException(404, detail="Варіації не знайдено")
    
        return [ProductVariationPriceSchema.from_orm(v) for v in variations]
    
    except HTTPException:
        raise
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")

@router.get("/stats", response_model=ProductStatsSchema,
            responses={
                200: {"description": "Статистика продуктів"},
                500: {"description": "Упс! Щось пішло не так. Спробуйте пізніше"},
})
async def get_product_stats(
    category_id: Optional[int] = None,
    brand_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        filters = []
        if category_id:
            filters.append(Product.category_id == category_id)
        if brand_id:
            filters.append(Product.brand_id == brand_id)

        total_query = select(func.count(Product.product_id))
        if filters:
            total_query = total_query.where(and_(*filters))
        total_result = await db.execute(total_query)
        total_products = total_result.scalar()

        in_stock_query = select(func.count(Product.product_id)).where(Product.in_stock == True)
        if filters:
            in_stock_query = in_stock_query.where(and_(*filters))
        in_stock_result = await db.execute(in_stock_query)
        in_stock_count = in_stock_result.scalar()

        avg_price_query = select(func.avg(Product.price))
        if filters:
            avg_price_query = avg_price_query.where(and_(*filters))
        avg_price_result = await db.execute(avg_price_query)
        avg_price = round(float(avg_price_result.scalar() or 0), 2)

        category_stats_query = select(
            Category.category_id,
            Category.name,
            func.count(Product.product_id).label("product_count"),
            func.avg(Product.price).label("avg_price")
        ).join(Product, Product.category_id == Category.category_id)
        if brand_id:
            category_stats_query = category_stats_query.where(Product.brand_id == brand_id)
        category_stats_query = category_stats_query.group_by(Category.category_id, Category.name)
        category_stats_result = await db.execute(category_stats_query)
        category_stats = [
            {
                "category_id": row.category_id,
                "name": row.name,
                "product_count": row.product_count,
                "avg_price": round(float(row.avg_price or 0), 2)
            }
            for row in category_stats_result.all()
        ]

        brand_stats_query = select(
            Brand.brand_id,
            Brand.name,
            func.count(Product.product_id).label("product_count"),
            func.avg(Product.price).label("avg_price")
        ).join(Product, Product.brand_id == Brand.brand_id)
        if category_id:
            brand_stats_query = brand_stats_query.where(Product.category_id == category_id)
        brand_stats_query = brand_stats_query.group_by(Brand.brand_id, Brand.name)
        brand_stats_result = await db.execute(brand_stats_query)
        brand_stats = [
            {
                "brand_id": row.brand_id,
                "name": row.name,
                "product_count": row.product_count,
                "avg_price": round(float(row.avg_price or 0), 2)
            }
            for row in brand_stats_result.all()
        ]

        return {
            "total_products": total_products,
            "in_stock_count": in_stock_count,
            "out_of_stock_count": total_products - in_stock_count,
            "average_price": avg_price,
            "category_stats": category_stats,
            "brand_stats": brand_stats
        }
    
    except Exception:
        raise HTTPException(500, detail="Упс! Щось пішло не так. Спробуйте пізніше")