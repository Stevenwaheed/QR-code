import uuid

from app.blueprints.agency.methods import get_agency_details
from app.blueprints.agency.models import Agency


def generate_random_filename(extension=""):
    random_name = uuid.uuid4().hex  # Generate a unique identifier
    return f"{random_name}.{extension}"



def get_product_details(product):
    agency = Agency.query.filter_by(id=product.agency_id).first()
    agency_details = get_agency_details(agency)
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "image_url": product.image_url,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "agency":agency_details
    }