
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
    """
    Get all products or create a new product
    ---
    tags:
      - Products
    security:
      - jwt: []
    parameters:
      - in: formData
        name: name
        type: string
        required: true
        description: Product name
        example: "Premium Widget"
      - in: formData
        name: description
        type: string
        required: true
        description: Product description
        example: "A high-quality widget for all your needs"
      - in: formData
        name: category_id
        type: integer
        required: true
        description: ID of the category this product belongs to
        example: 1
      - in: formData
        name: price
        type: number
        format: float
        required: false
        description: Product price
        default: 0.0
        example: 29.99
      - in: formData
        name: image_url
        type: string
        required: false
        description: URL to product image
        default: ""
        example: "https://example.com/images/product.jpg"
    responses:
      200:
        description: Product created successfully or list of all products
        schema:
          type: object
          properties:
            id:
              type: integer
              description: Product ID
            name:
              type: string
              description: Product name
            description:
              type: string
              description: Product description
            price:
              type: number
              format: float
              description: Product price
            category_id:
              type: integer
              description: Category ID
            image_url:
              type: string
              description: URL to product image
            agency_id:
              type: integer
              description: Agency ID
            created_by:
              type: integer
              description: User ID who created this product
      404:
        description: Agency or category not found
      401:
        description: Unauthorized, invalid or expired token
    """
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
    """
    Get a specific product by ID
    ---
    tags:
      - Products
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: ID of the product to retrieve
        example: 1
    responses:
      200:
        description: Product details
        schema:
          type: object
          properties:
            id:
              type: integer
              description: Product ID
            name:
              type: string
              description: Product name
            description:
              type: string
              description: Product description
            price:
              type: number
              format: float
              description: Product price
            category_id:
              type: integer
              description: Category ID
            image_url:
              type: string
              description: URL to product image
            agency_id:
              type: integer
              description: Agency ID
            created_by:
              type: integer
              description: User ID who created this product
      404:
        description: Product not found
      500:
        description: Server error
    """
    try:
        product = Product.query.filter_by(id=product_id, is_visible=True).first()
        if not product:
            return jsonify({"message": "Product not found"}), 404
        
        return get_product_details(product), 200
        
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    


@product_bp.route('/v1/product/agency/<int:agency_id>', methods=['GET'])
def get_products_by_agency(agency_id):
    """
    Get all products for a specific agency
    ---
    tags:
      - Products
    parameters:
      - name: agency_id
        in: path
        type: integer
        required: true
        description: ID of the agency whose products to retrieve
        example: 1
    responses:
      200:
        description: List of products for the specified agency
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: Product ID
              name:
                type: string
                description: Product name
              description:
                type: string
                description: Product description
              price:
                type: number
                format: float
                description: Product price
              category_id:
                type: integer
                description: Category ID
              image_url:
                type: string
                description: URL to product image
              agency_id:
                type: integer
                description: Agency ID
              created_by:
                type: integer
                description: User ID who created this product
      500:
        description: Server error
    """
    try:
        products = Product.query.filter_by(agency_id=agency_id, is_visible=True).all()
        products_list = []
        for product in products:
            products_list.append(
                get_product_details(product)
            )
        return products_list, 200
        
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
    

@product_bp.route('/v1/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    Soft delete a product (mark as not visible)
    ---
    tags:
      - Products
    security:
      - jwt: []
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: ID of the product to delete
        example: 1
    responses:
      200:
        description: Product successfully marked as deleted
        schema:
          type: object
          properties:
            id:
              type: integer
              description: Product ID
            name:
              type: string
              description: Product name
            is_visible:
              type: boolean
              description: Product visibility status (will be false)
      404:
        description: Product not found
      500:
        description: Server error
      401:
        description: Unauthorized, invalid or expired token
    """
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
    """
    Update a product's details
    ---
    tags:
      - Products
    security:
      - jwt: []
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: ID of the product to update
        example: 1
      - in: formData
        name: name
        type: string
        required: false
        description: Updated product name
        example: "Premium Widget v2"
      - in: formData
        name: description
        type: string
        required: false
        description: Updated product description
        example: "An improved high-quality widget for all your needs"
      - in: formData
        name: category_id
        type: integer
        required: false
        description: Updated category ID
        example: 2
      - in: formData
        name: price
        type: number
        format: float
        required: false
        description: Updated product price
        example: 39.99
      - in: formData
        name: image_url
        type: string
        required: false
        description: Updated URL to product image
        example: "https://example.com/images/product_v2.jpg"
    responses:
      200:
        description: Product successfully updated
        schema:
          type: object
          properties:
            id:
              type: integer
              description: Product ID
            name:
              type: string
              description: Updated product name
            description:
              type: string
              description: Updated product description
            price:
              type: number
              format: float
              description: Updated product price
            category_id:
              type: integer
              description: Updated category ID
            image_url:
              type: string
              description: Updated URL to product image
      404:
        description: Product or category not found
      500:
        description: Server error
      401:
        description: Unauthorized, invalid or expired token
    """
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



