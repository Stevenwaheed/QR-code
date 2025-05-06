import json
from app.blueprints.auth.models import User
from flask import Blueprint, request
from app.blueprints.category.models import Category, db
from app.blueprints.category.methods import get_category_json
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)


category_pg = Blueprint('category', __name__)


@category_pg.route('/v1/category', methods=['POST'])
@jwt_required()
def add_category():
    """
    Add a new category to a menu.

    This endpoint allows an authenticated user to create a new category for a specified menu. 
    The category is associated with a particular menu and agency.

    **Authentication Required**: JWT Token

    ---
    tags:
      - Categories
    parameters:
      - in: body
        required: true
        schema:
            type: object
            properties:
              name:
                type: string
                description: The name of the new category.
                example: "Desserts"
              agency_id:
                type: integer
                description: The ID of the agency to which the menu belongs.
                example: 1
    responses:
      200:
        description: Successfully added the new category.
        content:
          application/json:
            schema:
              type: object
              properties:
                category:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The unique ID of the category.
                    name:
                      type: string
                      description: The name of the category.
                    agency_id:
                      type: integer
                      description: The ID of the agency associated with the category.
              example:
                category:
                  {
                    "id": 1,
                    "name": "Desserts",
                    "agency_id": 1
                  }
      400:
        description: Invalid request body or missing required parameters.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "menu id is required"
      404:
        description: The specified menu was not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "menu not found"
      401:
        description: Unauthorized. Missing or invalid JWT token.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Missing or invalid JWT token"
    security:
      - bearerAuth: []
    """
    try:
        data = request.json
    except:
        return {"message":"can't receive the request"}, 400
    
    payload = get_jwt_identity()
    payload = json.loads(payload)
    
    user = User.query.filter_by(id=payload['user_id']).first()
    if 'name' not in data:
        return {"message": "name is required"}, 400
    
    # try:
    
    new_category = Category(name=data['name'], agency_id=user.agency_id).first()
    db.session.add(new_category)
    db.session.commit()
    
    return get_category_json(new_category), 200


@category_pg.route('/v1/category', methods=['GET'])
@jwt_required()
def get_categories():
  payload = get_jwt_identity()
  payload = json.loads(payload)
  user = User.query.filter_by(id=payload['user_id']).first()
  categories = Category.query.filter_by(agency_id=user.agency_id).all()
  
  category_list = []
  for category in categories:
    category_list.append(
      get_category_json(category)
      )
    
  return category_list, 200


@category_pg.route('/v1/category/<int:category_id>', methods=['GET'])
@jwt_required()
def get_category(category_id):
  payload = get_jwt_identity()
  payload = json.loads(payload)
  user = User.query.filter_by(id=payload['user_id']).first()
  category = Category.query.filter_by(id=category_id, agency_id=user.agency_id).first()
  
  return get_category_json(category), 200


