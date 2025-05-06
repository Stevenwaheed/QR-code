import uuid

from app.blueprints.agency.methods import get_agency_details
from app.blueprints.agency.models import Agency
from app.blueprints.auth.methods import get_user_details
from app.blueprints.auth.models import User
from app.blueprints.category.methods import get_category_json
from app.blueprints.category.models import Category


def generate_random_filename(extension=""):
    random_name = uuid.uuid4().hex  # Generate a unique identifier
    return f"{random_name}.{extension}"



def get_product_details(product):
    agency = Agency.query.filter_by(id=product.agency_id).first()
    user = User.query.filter_by(id=product.created_by).first()
    category = Category.query.filter_by(id=product.category_id).first()


    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "image_url": product.image_url,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "agency": get_agency_details(agency),
        "created_by": get_user_details(user),
        "category": get_category_json(category)
    }