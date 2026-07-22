"""Product routes: CRUD and filtered listing.

Controllers stay thin: they validate/translate HTTP concerns and delegate all
business logic to :class:`app.services.products_service.ProductService`.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.dependencies import get_product_service
from app.schemas import Product, ProductCreate, ProductPage, ProductUpdate
from app.services.products_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductPage)
def list_products(
    user: str = Depends(get_current_user),
    section: str | None = Query(default=None),
    name: str | None = Query(default=None, description="case-insensitive substring"),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    has_discount: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    product_service: ProductService = Depends(get_product_service),
) -> ProductPage:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price must be less than or equal to max_price",
        )
    return product_service.list_products(
        user,
        section=section,
        name=name,
        min_price=min_price,
        max_price=max_price,
        has_discount=has_discount,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    user: str = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> Product:
    return product_service.create_product(user, body)


@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    user: str = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> Product:
    product = product_service.get_product(user, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return product


@router.patch("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    body: ProductUpdate,
    user: str = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> Product:
    product = product_service.update_product(user, product_id, body)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    user: str = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> None:
    if not product_service.delete_product(user, product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
