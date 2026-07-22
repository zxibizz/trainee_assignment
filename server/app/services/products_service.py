"""Business logic for the product catalog.

Writes (create, update, delete) publish a mutation event to the downstream
event bus; reads do not.
"""

from app.gateways.event_bus_gateway import ProductEventBusGateway, ProductEventType
from app.repositories.products_repository import ProductRepository
from app.schemas import (
    Pagination,
    Product,
    ProductCreate,
    ProductPage,
    ProductUpdate,
)
from app.services.auth_service import AuthService


class ProductService:
    def __init__(
        self,
        repository: ProductRepository,
        auth_service: AuthService,
        event_bus: ProductEventBusGateway,
    ) -> None:
        self._repo = repository
        self._authz = auth_service
        self._events = event_bus

    def list_products(
        self,
        subject: str,
        *,
        section: str | None = None,
        name: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        has_discount: bool | None = None,
        limit: int,
        offset: int,
    ) -> ProductPage:
        self._authz.authorize(subject, "products:list")
        items, total = self._repo.list(
            section=section,
            name=name,
            min_price=min_price,
            max_price=max_price,
            has_discount=has_discount,
            limit=limit,
            offset=offset,
        )
        return ProductPage(
            items=items,
            pagination=Pagination(
                limit=limit, offset=offset, count=len(items), total=total
            ),
        )

    def get_product(self, subject: str, product_id: int) -> Product | None:
        self._authz.authorize(subject, "products:read")
        return self._repo.get(product_id)

    def create_product(self, subject: str, body: ProductCreate) -> Product:
        self._authz.authorize(subject, "products:create")
        product = self._repo.create(body)
        self._events.publish(
            ProductEventType.CREATED,
            actor=subject,
            product_id=product.id,
            data=product.model_dump(),
        )
        return product

    def update_product(
        self, subject: str, product_id: int, body: ProductUpdate
    ) -> Product | None:
        self._authz.authorize(subject, "products:update")
        product = self._repo.update(product_id, body)
        if product is not None:
            self._events.publish(
                ProductEventType.UPDATED,
                actor=subject,
                product_id=product.id,
                data=product.model_dump(),
            )
        return product

    def delete_product(self, subject: str, product_id: int) -> bool:
        self._authz.authorize(subject, "products:delete")
        deleted = self._repo.delete(product_id)
        if deleted:
            self._events.publish(
                ProductEventType.DELETED,
                actor=subject,
                product_id=product_id,
            )
        return deleted
