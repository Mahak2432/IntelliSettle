from claims_api.products.base import InsuranceProduct
from claims_api.products.crop import CropParametricProduct

_PRODUCTS: dict[str, InsuranceProduct] = {product.code: product for product in (CropParametricProduct(),)}


def get_product(code: str) -> InsuranceProduct:
    try:
        return _PRODUCTS[code]
    except KeyError:
        raise KeyError(f"Unknown insurance product: {code}") from None


def all_products() -> list[InsuranceProduct]:
    return list(_PRODUCTS.values())
