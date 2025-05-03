import json
import os

from .models import QRCode
from sqlalchemy import desc
from app.blueprints.address.models import Address, City, Country, State
from app.blueprints.agency.methods import get_agency_details
from app.blueprints.auth.methods import seed_roles
from app.blueprints.auth.models import User, UserType
from app.blueprints.product.methods import generate_random_filename
from app.blueprints.product.models import Product
from app.blueprints.profile.models import Profile
from config.config import Config
from flask import Blueprint, request, jsonify
from db.database import db
from .models import Agency, AgencyStatus
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

agency_bp = Blueprint("agency_bp", __name__)


@agency_bp.route("/v1/agency", methods=["POST"])
@jwt_required()
def create_agency():
    """
    Create a new agency
    ---
    tags:
      - Companies
    summary: Create a new agency
    description: |
      This endpoint creates a new agency with the provided details, including address information.
      Files can also be uploaded and associated with each document in the agency.
    security:
      - bearerAuth: []
    parameters:
      - name: name
        in: formData
        type: string
        required: true
        description: The name of the agency.
      - name: agency_type_id
        in: formData
        type: integer
        required: true
        description: The ID of the agency type.
      - name: tax_number
        in: formData
        type: string
        required: true
        description: The tax number of the agency.
      - name: city_id
        in: formData
        type: integer
        required: true
        description: The ID of the city for the agency's address.
      - name: state_id
        in: formData
        type: integer
        required: true
        description: The ID of the state for the agency's address.
      - name: country_id
        in: formData
        type: integer
        required: true
        description: The ID of the country for the agency's address.
      - name: street_address
        in: formData
        type: string
        required: true
        description: The street address of the agency.
      - name: postal_code
        in: formData
        type: string
        required: false
        description: The postal code of the agency's address (optional).
      - name: lat
        in: formData
        type: number
        format: float
        required: false
        description: The latitude of the agency's address (optional).
      - name: lan
        in: formData
        type: number
        format: float
        required: false
        description: The longitude of the agency's address (optional).
      - name: categories
        in: formData
        type: array
        items:
          type: integer
        required: true
        description: List of category IDs associated with the agency.
      - name: documents
        in: formData
        type: array
        items:
          type: object
          properties:
            id:
              type: integer
              description: The ID of the document.
            file:
              type: file
              description: The file to upload for this document.
        required: true
        description: List of documents associated with the agency, each with an upload button for file upload.
    responses:
      201:
        description: agency created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                  description: The unique identifier of the agency.
                name:
                  type: string
                  description: The name of the agency.
                type:
                  type: string
                  description: The type of the agency.
                icon:
                  type: string
                  description: The URL of the agency's icon.
                tax_number:
                  type: string
                  description: The tax number of the agency.
                address:
                  type: object
                  properties:
                    city:
                      type: object
                      properties:
                        id:
                          type: integer
                          description: The ID of the city.
                        name:
                          type: string
                          description: The name of the city.
                    state:
                      type: object
                      properties:
                        id:
                          type: integer
                          description: The ID of the state.
                        name:
                          type: string
                          description: The name of the state.
                    country:
                      type: object
                      properties:
                        id:
                          type: integer
                          description: The ID of the country.
                        name:
                          type: string
                          description: The name of the country.
                    street_address:
                      type: string
                      description: The street address of the agency.
                documents:
                  type: array
                  description: List of uploaded documents
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        description: The ID of the document.
                      file_url:
                        type: string
                        description: The URL of the uploaded file.
                created_at:
                  type: string
                  format: date-time
                  description: The timestamp when the agency was created.
                updated_at:
                  type: string
                  format: date-time
                  description: The timestamp when the agency was last updated.
      400:
        description: Bad request (e.g., missing required fields or invalid data)
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message.
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
      500:
        description: Internal server error
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
    """
    payload = get_jwt_identity()
    payload = json.loads(payload)
    user = User.query.filter_by(id=payload['user_id']).first()
    if user is None:
      return {"message": "user not found"}, 200

    data = request.json
    required_fields = [
        "name",
        'city_id',
        'state_id',
        'country_id',
        'street_address',
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    if data['name'] == "":
      return {"message": "agency name is empty"}
    
    
    try:
      postal_code=data['postal_code']
    except:
      postal_code = None
    
    
    try:
      lat=data['lat']
      lan=data['lan']
    except:
      lan = lat = None
    
    
    # try:
    city = City.query.filter_by(id=data['city_id']).first()
    state = State.query.filter_by(id=data['state_id']).first()
    country = Country.query.filter_by(id=data['country_id']).first()
    address = Address(
      country_id=int(country.id),
      state_id=int(state.id),
      city_id=int(city.id),
      user_id=user.id,
      postal_code=postal_code,
      lat=lat,
      lan=lan,
      street_address=data['street_address'],
    )
    db.session.add(address)
    db.session.commit()
    
    
    new_agency = Agency(name=data["name"]
                        , address_id=address.id
                        )

    
    db.session.add(new_agency)
    db.session.commit()
    
    agency_details = get_agency_details(new_agency)
    
    # seed_roles(new_agency.id)
    
    if user.user_type.value == UserType.SUPERADMIN.value:
      if 'user_id' not in data:
        return {"message": "user id is required"}
      admin_user = User.query.filter_by(id=data['user_id']).first()
      admin_user.agency_id = new_agency.id
      db.session.commit()
    else:
      user.agency_id = new_agency.id
      db.session.commit()

    return (
        jsonify(
            agency_details
        ),
        201,
    )
    # except Exception as e:
    #     db.session.rollback()
    #     return jsonify({"message": str(e)}), 500


# Retrieve all companies
@agency_bp.route("/v1/agency", methods=["GET"])
# @jwt_required()
def get_companies():
    """
    Retrieve all companies
    ---
    tags:
      - Companies
    responses:
      200:
        description: A list of companies
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  type:
                    type: string
                  icon:
                    type: string
                  tax_number:
                    type: string
                  address:
                    type: object
                    properties:
                      city:
                        type: object
                        properties:
                          id:
                            type: integer
                          name:
                            type: string
                      state:
                        type: object
                        properties:
                          id:
                            type: integer
                          name:
                            type: string
                      country:
                        type: object
                        properties:
                          id:
                            type: integer
                          name:
                            type: string
                      street_address:
                        type: string
                  created_at:
                    type: string
                    format: date-time
                  updated_at:
                    type: string
                    format: date-time
    """
    companies = Agency.query.all()

    companies_list = []
    for agency in companies:
      agency_details = get_agency_details(agency)
        
      companies_list.append(
        agency_details
      )
    return (
        jsonify(companies_list), 200
    )




@agency_bp.route("/v1/agency/<agency_id>", methods=["GET"])
def get_agency(agency_id):
    """
    Retrieve a agency by its ID
    ---
    tags:
      - Companies
    parameters:
      - name: agency_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: A single agency object
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                type:
                  type: string
                icon:
                  type: string
                tax_number:
                  type: string
                address:
                  type: object
                  properties:
                    city:
                      type: object
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
                    state:
                      type: object
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
                    country:
                      type: object
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
                    street_address:
                      type: string
                created_at:
                  type: string
                  format: date-time
                updated_at:
                  type: string
                  format: date-time
      404:
        description: agency not found
    """
    agency = Agency.query.filter_by(id=agency_id).first()
    if agency is None:
      return {"message": "agency not found"}, 404
    
    agency_details = get_agency_details(agency)
    return agency_details, 200
      


@agency_bp.route('/v1/agency/subscribe', methods=['PATCH'])
@jwt_required()
def subscribe():
  payload = get_jwt_identity()
  payload = json.loads(payload)
  
  file = request.files['file']
  
  extension = file.filename.split('.')[-1]
  if extension.lower() not in ['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx']:
    return {"message":"invalid file type"}, 400
  
  file_name = generate_random_filename(extension)
  file_path = os.path.join(Config.IMAGE_ICONS_URL, file_name)
  file.save(file_path)

  user = User.query.filter_by(id=payload['user_id']).first()
  agency = Agency.query.filter_by(id=user.agency_id).first()
  agency.is_subscribed = True
  db.sessions.commit()
  
  agency_details = get_agency_details(agency)
  return agency_details, 200
  



@agency_bp.route('/v1/agency/<int:agency_id>/upload/logo', methods=['POST'])
@jwt_required()
def upload_category_logo(agency_id):
  """
  Upload a agency icon
  ---
  tags:
    - Companies
  description: |
    This endpoint allows the upload of an icon for a specified agency. 
    The uploaded file must be an image of type PNG, JPG, JPEG, or GIF.
  parameters:
    - name: file
      in: formData
      required: true
      type: file
      description: The image file to upload.
  responses:
    200:
      description: Successfully uploaded the agency icon
      schema:
        type: object
        properties:
          id:
            type: integer
            description: The ID of the agency.
          name:
            type: string
            description: The name of the agency.
          icon:
            type: string
            description: The URL of the uploaded icon.
          address:
            type: object
            properties:
              id:
                type: integer
                description: The ID of the city associated with the agency's address.
              name:
                type: string
                description: The name of the city.
              state:
                type: object
                properties:
                  id:
                    type: integer
                    description: The ID of the state.
                  name:
                    type: string
                    description: The name of the state.
              country:
                type: object
                properties:
                  id:
                    type: integer
                    description: The ID of the country.
                  name:
                    type: string
                    description: The name of the country.
              postal_code_prefix:
                type: string
                description: The postal code prefix for the city.
    400:
      description: Bad request due to missing file or invalid file type
      schema:
        type: object
        properties:
          error:
            type: string
            description: Error message describing the issue.
    404:
      description: agency or address not found, or related entities missing
      schema:
        type: object
        properties:
          message:
            type: string
    500:
      description: Internal server error during file upload or processing
      schema:
        type: object
        properties:
          error:
            type: string
            description: Error message describing the issue.
  security:
    - bearerAuth: []  # Assuming JWT authentication is required for this endpoint 
  """
  if 'file' not in request.files:
    return jsonify({"error": "No file part"}), 400

  # payload = get_jwt_identity()
  # payload = json.loads(payload)
  # user = User.query.filter_by(id=payload['user_id']).first()
  
  agency = Agency.query.filter_by(id=agency_id).first()
  if agency is None:
    return {"message":"agency not found"}, 404
  
  file = request.files['file']
  if file is None:
    return {"message": "image is required"}
  
  try:
    extension = file.filename.split('.')[-1]
    if extension.lower() not in ['png', 'jpg', 'jpeg', 'gif']:
      return {"message":"invalid file type"}, 400
    
    file_name = generate_random_filename(extension)
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join(Config.IMAGE_ICONS_URL, file_name)
    file.save(file_path)
    
    agency.icon_url=Config.IMAGE_ICONS_GLOBAL_URL+file_name
    db.session.commit()
    
    agency_details = get_agency_details(agency)
    return jsonify(agency_details), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({"error": str(e)}), 500
  




@agency_bp.route("/v1/agency/<int:agency_id>", methods=["PATCH"])
def update_agency(agency_id):
    '''
    Update a agency by its ID
    ---
    tags:
      - Companies
    parameters:
      - name: agency_id
        in: path
        type: integer
        description: The ID of the agency to update
        required: true
        example: 1
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: The name of the agency
              example: "Updated agency Name"
            type:
              type: string
              description: The type of the agency (enum value)
              example: "MANUFACTURER"
            icon_url:
              type: string
              description: The URL of the agency's icon
              example: "https://example.com/icon.png"
            tax_number:
              type: string
              description: The tax number of the agency
              example: "TAX123456"
            address_id:
              type: integer
              description: The ID of the address associated with the agency
              example: 1
    responses:
      200:
        description: agency updated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                  description: The ID of the agency
                  example: 1
                name:
                  type: string
                  description: The name of the agency
                  example: "Updated agency Name"
                agency_type_id:
                  type: integer
                  description: The type of the agency
                  example: 1
                icon_url:
                  type: string
                  description: The URL of the agency's icon
                  example: "https://example.com/icon.png"
                tax_number:
                  type: string
                  description: The tax number of the agency
                  example: "TAX123456"
                address_id:
                  type: integer
                  description: The ID of the address associated with the agency
                  example: 1
                is_visible:
                  type: boolean
                  description: Whether the agency is visible
                  example: true
                created_at:
                  type: string
                  description: The creation timestamp of the agency
                  example: "2025-02-09T00:00:00Z"
                updated_at:
                  type: string
                  description: The last updated timestamp of the agency
                  example: "2025-02-09T00:00:00Z"
      404:
        description: agency not found
      400:
        description: Invalid input or update failed
      500:
        description: Internal server error
    '''
    agency = Agency.query.filter_by(id=agency_id, is_visible=True).first()
    if agency is None:
        return {"message": "agency not found"}, 404

    data = request.json

    try:
        if "name" in data:
            agency.name = data["name"]
        if "icon_url" in data:
            agency.icon_url = data["icon_url"]
        if "address_id" in data:
            agency.address_id = data["address_id"]

        db.session.commit()
        agency_details = get_agency_details(agency)
        return jsonify(
            agency_details
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
      
      
@agency_bp.route("/v1/agency/<int:agency_id>", methods=["DELETE"])
def delete_agency(agency_id):
    '''
    Delete a agency by its ID (soft delete)
    ---
    tags:
      - Companies
    parameters:
      - name: agency_id
        in: path
        type: integer
        description: The ID of the agency to delete
        required: true
        example: 1
    responses:
      200:
        description: agency soft-deleted successfully, and a list of remaining visible companies is returned
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: The ID of the agency
                    example: 2
                  name:
                    type: string
                    description: The name of the agency
                    example: "agency Name"
                  type:
                    type: string
                    description: The type of the agency
                    example: "MANUFACTURER"
                  icon_url:
                    type: string
                    description: The URL of the agency's icon
                    example: "https://example.com/icon.png"
                  tax_number:
                    type: string
                    description: The tax number of the agency
                    example: "TAX123456"
                  address_id:
                    type: integer
                    description: The ID of the address associated with the agency
                    example: 1
                  is_visible:
                    type: boolean
                    description: Whether the agency is visible
                    example: true
                  created_at:
                    type: string
                    description: The creation timestamp of the agency
                    example: "2025-02-09T00:00:00Z"
                  updated_at:
                    type: string
                    description: The last updated timestamp of the agency
                    example: "2025-02-09T00:00:00Z"
      404:
        description: agency not found
      500:
        description: Internal server error
    '''
    agency = Agency.query.filter_by(id=agency_id, is_visible=True).first()
    if agency is None:
        return {"message": "agency not found"}, 404

    try:
        agency.is_visible = False
        users = User.query.filter_by(agency_id=agency.id).all()
        for user in users:
          profile = Profile.query.filter_by(user_id=user.id).first()
          
          profile.is_visible = False
          user.is_visible = False
          
        db.session.commit()
        # Return a list of all visible companies after deletion
        companies = Agency.query.filter_by(is_visible=True).all()
        return jsonify(
          [
            get_agency_details(agency)
            for agency in companies
          ]
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
      
      


  
@agency_bp.route('/v1/agency/<int:agency_id>/approved', methods=['PATCH'])
@jwt_required()
def approve_agency_files(agency_id):
  """
  Approve a agency's files
  ---
  tags:
    - Companies
  summary: Approve a agency's files
  description: This endpoint updates the status of a agency to APPROVED and returns the agency details along with its associated files.
  parameters:
    - name: agency_id
      in: path
      type: integer
      required: true
      description: The ID of the agency to approve.
  security:
    - bearerAuth: []
  responses:
    200:
      description: agency approved successfully
      content:
        application/json:
          schema:
            type: object
            properties:
              id:
                type: integer
                description: The agency unique identifier
              name:
                type: string
                description: The agency name
              type:
                type: string
                description: The agency type
              icon_url:
                type: string
                description: URL to the agency icon
              tax_number:
                type: string
                description: The agency tax number
              status:
                type: string
                description: The agency status
              urls:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The document unique identifier
                    url:
                      type: string
                      description: URL to the document
    404:
      description: agency not found
    401:
      description: Unauthorized - JWT token missing or invalid
  """
  agency = Agency.query.filter_by(id=agency_id).first()
  if agency is None:
    return {"message": "agency not found"}, 404
  
  agency.status = AgencyStatus.APPROVED
  user = User.query.filter_by(agency_id=agency.id).first()
  user.is_verified = True
  db.session.commit()
  
  agency_details = get_agency_details(agency)
  return agency_details, 200
  
  
  
@agency_bp.route('/v1/agency/<int:agency_id>/rejected', methods=['PATCH'])
@jwt_required()
def reject_agency_files(agency_id):
  """
  Reject a agency's files
  ---
  tags:
    - Companies
  summary: Reject a agency's files
  description: This endpoint updates the status of a agency to REJECTED and returns the agency details along with its associated files.
  parameters:
    - name: agency_id
      in: path
      type: integer
      required: true
      description: The ID of the agency to reject.
  security:
    - bearerAuth: []
  responses:
    200:
      description: agency rejected successfully
      content:
        application/json:
          schema:
            type: object
            properties:
              id:
                type: integer
                description: The agency unique identifier
              name:
                type: string
                description: The agency name
              type:
                type: string
                description: The agency type
              icon_url:
                type: string
                description: URL to the agency icon
              tax_number:
                type: string
                description: The agency tax number
              status:
                type: string
                description: The agency status
              urls:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The document unique identifier
                    url:
                      type: string
                      description: URL to the document
    404:
      description: agency not found
    401:
      description: Unauthorized - JWT token missing or invalid
  """
  agency = Agency.query.filter_by(id=agency_id).first()
  if agency is None:
    return {"message": "agency not found"}, 404
  agency.status = AgencyStatus.REJECTED
  db.session.commit()
  
  agency_details = get_agency_details(agency)
  return agency_details, 200

