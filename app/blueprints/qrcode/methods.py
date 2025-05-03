



import json
from app.blueprints.agency.methods import get_agency_details
from app.blueprints.agency.models import Agency


def get_qr_details(qr_code):
    agency = Agency.query.filter_by(id=qr_code.agency_id).first()
    agency_details = get_agency_details(agency)
    
    return {
        "id": qr_code.id,
        "content": json.loads(qr_code.content),
        "name": qr_code.name,
        "qrcode_url": qr_code.qrcode_url,
        "expire_at": qr_code.expire_at,
        "created_at": qr_code.created_at,
        "updated_at": qr_code.updated_at,
        "agency":agency_details
    }