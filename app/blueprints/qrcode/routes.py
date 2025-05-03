from datetime import datetime, timedelta
import json
from flask import Blueprint, redirect, request, jsonify, url_for
from app.blueprints.agency.models import Agency
from app.blueprints.product.methods import get_product_details
from app.blueprints.product.models import Product
from app.blueprints.qrcode.methods import get_qr_details
from app.blueprints.qrcode.models import QRCode
from db.database import db


# from flask_jwt_extended import (
#     jwt_required,
#     get_jwt_identity,
# )

qrcode_bp = Blueprint("qrcode_bp", __name__)


@qrcode_bp.route('/qrcode/<int:agency_id>', methods=['GET', 'POST'])
def create_qrcode(agency_id):
    agency = Agency.query.get_or_404(agency_id)
    
    if request.method == 'POST':
        # Check if agency can create more QR codes
        if not agency.can_create_qr():
            return  {"message":"Monthly QR code limit reached for this agency"}, 404
        
        # Get form data
        name = request.form.get('name')
        product_ids = request.form.getlist('product_ids')
        
        # Calculate expiration date
        expire_at = datetime.now() + timedelta(days=30)
        
        products_list = []
        for id in product_ids:
            product = Product.query.filter_by(id=id).first()
            product_details = get_product_details(product)
            products_list.append(product_details)
            
        # Create content as JSON
        content = json.dumps({
            'product': products_list,
            'created_by': agency.name
        })
        
        # Create new QR code
        new_qr = QRCode(
            name=name,
            content=content,
            agency_id=agency_id,
            expire_at=expire_at
        )
        
        db.session.add(new_qr)
        db.session.commit()
        
        # Generate the actual QR code
        new_qr.generate_qr_code()
        
        return {
            get_qr_details(new_qr)
        }
    
    # GET request - show form
    
    qr_codes = QRCode.query.all()
    return [
        {
            get_qr_details(qr)
        } for qr in qr_codes
    ]




@qrcode_bp.route('/qrcode/scan/<int:qr_id>', methods=['GET'])
def scan_qrcode(qr_id):
    """Public endpoint that users will access when scanning a QR code"""
    qr_code = QRCode.query.get_or_404(qr_id)
    
    # Check if QR code is expired
    if qr_code.is_expired():
        return {"message": "this qr is expired"}, 400
    
    return get_qr_details(qr_code), 200




@qrcode_bp.route('/qrcode/<int:qr_id>', methods=['GET'])
def api_qrcode_info(qr_id):
    """API endpoint to get QR code data"""
    qr_code = QRCode.query.get_or_404(qr_id)
    
    if qr_code.is_expired():
        return jsonify({
            'status': 'expired',
            'message': 'This QR code has expired'
        }), 410
    
    products = qr_code.get_products()
    product_data = [{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'image_url': product.image_url
    } for product in products]
    
    return jsonify({
        'status': 'active',
        'qr_code': {
            'id': qr_code.id,
            'name': qr_code.name,
            'expire_at': qr_code.expire_at.isoformat() if qr_code.expire_at else None,
            'created_at': qr_code.created_at.isoformat()
        },
        'agency': {
            'id': qr_code.agency.id,
            'name': qr_code.agency.name
        },
        'products': product_data
    })