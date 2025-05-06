
import json
from app.blueprints.auth.models import User
from app.blueprints.category.models import Category
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)
from app.blueprints.product.methods import get_product_details
from db.database import db
from app.blueprints.agency.models import Agency
from app.blueprints.product.models import Product

product_bp = Blueprint("product", __name__)


@product_bp.route('/v1/product', methods=['GET', 'POST'])
@jwt_required()
def manage_products():
    payload = get_jwt_identity()
    payload = json.loads(payload)
    user = User.query.filter_by(id=payload['user_id']).first()
    agency = Agency.query.filter_by(id=user.agency_id).first()
    if agency is None:
        return {"message": "agency not found"}, 404
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        price = float(request.form.get('price', 0))
        image_url = request.form.get('image_url', '')
        category = Category.query.filter_by(id=category_id).first()
        if category is None:
            return {"message": "category not found"}, 404
        
        new_product = Product(
            name=name,
            created_by=user.id,
            description=description,
            price=price,
            category_id=category_id,
            image_url=image_url,
            agency_id=user.agency_id
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        return get_product_details(new_product), 200
    
    products = Product.query.filter_by(agency_id=user.agency_id, is_visible=True).all()
    
    return [
        {
            get_product_details(product)
        } for product in products
    ], 200


@product_bp.route('/v1/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.filter_by(id=product_id, is_visible=True).first()
        if not product:
            return jsonify({"message": "Product not found"}), 404
        
        return get_product_details(product), 200
        
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
    
    

@product_bp.route('/v1/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        # Get the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"message": "Product not found"}), 404
        
        product.is_visible = False
        db.session.commit()
        
        return get_product_details(product), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500



@product_bp.route('/v1/product/<int:product_id>', methods=['PATCH'])
def update_product(product_id):
    try:
        # Get the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"message": "Product not found"}), 404
            
        # Get update data from request
        name = request.form.get('name')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        price = float(request.form.get('price'))
        image_url = request.form.get('image_url')
        
        if name is not None and name != '':
            product.name = name
        if description is not None and description != '':
            product.description = description
        if description is not None and price > 0:
            product.price = price
        if description is not None:
            product.image_url = image_url
        if category_id is not None:
            category = Category.query.filter_by(id=category_id).first()
            if category is None:
                return {"message": "category not found"}, 404
            
            product.category_id = category_id
            
        db.session.commit()
        
        # Return updated product data
        return get_product_details(product), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500



