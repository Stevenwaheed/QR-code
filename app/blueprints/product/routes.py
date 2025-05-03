
from flask import Blueprint, redirect, request, jsonify, url_for
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)
from app.blueprints.product.methods import get_product_details
from db.database import db
from app.blueprints.agency.models import Agency
from app.blueprints.product.models import Product

product_bp = Blueprint("agency_bp", __name__)


@product_bp.route('/product/<int:agency_id>', methods=['GET', 'POST'])
def manage_products(agency_id):
    agency = Agency.query.filter_by(id=agency_id).first()
    if agency is None:
        return {"message": "agency not found"}, 404
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        image_url = request.form.get('image_url', '')
        
        new_product = Product(
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            agency_id=agency_id
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        return get_product_details(new_product), 200
    
    products = Product.query.filter_by(agency_id=agency_id).all()
    
    return [
        {
            get_product_details(product)
        } for product in products
    ]
