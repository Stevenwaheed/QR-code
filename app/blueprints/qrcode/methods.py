


import os
import uuid
import qrcode
import json
from app.blueprints.agency.methods import get_agency_details
from app.blueprints.agency.models import Agency
from werkzeug.utils import secure_filename

def get_qr_details(qr_code):
    agency = Agency.query.filter_by(id=qr_code.agency_id).first()
    agency_details = get_agency_details(agency)
    
    return {
        "id": qr_code.id,
        "name": qr_code.name,
        "qrcode_url": qr_code.qrcode_url,
        "expire_at": qr_code.expire_at,
        "created_at": qr_code.created_at,
        "updated_at": qr_code.updated_at,
        "agency":agency_details
    }
    
    
def generate_qr_code(content, agency_id, qr_name):
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to the QR code
    qr.add_data(content)
    qr.make(fit=True)
    
    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image to a file
    filename = f"{secure_filename(qr_name)}_{agency_id}_{uuid.uuid4().hex}.png"
    img_path = os.path.join('static', 'qrcodes', filename)
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    img.save(img_path)
    
    # Return the relative URL to the image
    return f'/static/qrcodes/{filename}'