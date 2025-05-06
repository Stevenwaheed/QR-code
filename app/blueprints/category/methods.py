from typing import Dict
from app.blueprints.agency.methods import get_agency_details
from app.blueprints.agency.models import Agency
from app.blueprints.category.models import Category

def get_category_json(category: Category)-> Dict:
    agency = Agency.query.filter_by(id=category.agency_id).first()
    agency_details = get_agency_details(agency)
    return {
        "id": category.id,
        "name": category.name,
        "agency": agency_details
    }