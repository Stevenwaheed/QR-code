from datetime import datetime, timedelta
import json
import uuid
from app.blueprints.auth.models import User
from flask import Blueprint, redirect, request, jsonify, url_for
from app.blueprints.agency.models import Agency
from app.blueprints.product.methods import get_product_details
from app.blueprints.product.models import Product
from app.blueprints.qrcode.methods import generate_qr_code, get_qr_details
from app.blueprints.qrcode.models import QRCode, default_expire_at
from db.database import db


from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

qrcode_bp = Blueprint("qrcode_bp", __name__)



@qrcode_bp.route('/v1/qrcode', methods=['POST'])
@jwt_required()
def create_qr_code():
    """
    Create a new QR code
    ---
    tags:
      - QR Codes
    security:
      - bearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - redirect_base_url
          properties:
            name:
              type: string
              description: Name of the QR code
              example: "Store Entry QR"
            redirect_base_url:
              type: string
              description: Base URL where users will be redirected after scanning
              example: "https://myapp.com/store"
            qr_base_url:
              type: string
              description: Optional base URL for QR code endpoint (defaults to host URL)
              example: "https://api.myapp.com"
    responses:
      201:
        description: QR code created successfully
        schema:
          type: object
          properties:
            id:
              type: integer
              description: QR code ID
            name:
              type: string
              description: QR code name
            agency_id:
              type: integer
              description: Agency ID
            qrcode_url:
              type: string
              description: URL to the QR code image
            scanner_url:
              type: string
              description: URL encoded in the QR code
            redirect_target:
              type: string
              description: Where users will be redirected after scanning
            expire_at:
              type: string
              format: date-time
              description: Expiration date and time in ISO format
            created_at:
              type: string
              format: date-time
              description: Creation date and time
      400:
        description: Bad request - missing required fields
      401:
        description: Unauthorized, invalid or expired token
      500:
        description: Server error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ['name', 'redirect_base_url']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
            
        # Check if agency exists
        payload = get_jwt_identity()
        payload = json.loads(payload)
        
        user = User.query.filter_by(id=payload['user_id']).first()
        
        # Create a unique identifier for this QR code
        qr_uuid = uuid.uuid4().hex
        
        # Get base URL for QR code endpoint
        qr_base_url = data.get('qr_base_url', request.host_url.rstrip('/'))
        
        # Build the scanner URL (what the QR code will contain)
        scanner_url = f"{qr_base_url}/api/qr/{qr_uuid}"
        
        # Store the redirection target (where users will ultimately end up)
        redirect_target = f"{data['redirect_base_url']}/{user.agency_id}"
        
        # Generate QR code image
        qrcode_url = generate_qr_code(scanner_url, user.agency_id, data['name'])
        
        # Create new QR code record
        new_qr = QRCode(
            name=data['name'],
            content=qr_uuid,                # The UUID part that identifies this QR
            agency_id=user.agency_id,
            qrcode_url=qrcode_url,
            expire_at=default_expire_at()
        )
        
        db.session.add(new_qr)
        db.session.commit()
        
        return {
                "id": new_qr.id,
                "name": new_qr.name,
                "agency_id": new_qr.agency_id,
                "qrcode_url": new_qr.qrcode_url,             # URL to the QR code image
                "scanner_url": scanner_url,                  # URL encoded in the QR
                "redirect_target": redirect_target,          # Where users will end up
                "expire_at": new_qr.expire_at.isoformat() if new_qr.expire_at else None,
                "created_at": new_qr.created_at
            }, 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@qrcode_bp.route('/v1/qrcode/<int:qr_id>', methods=['PATCH'])
def update_qr_code(qr_id):
    """
    Update an existing QR code
    ---
    tags:
      - QR Codes
    security:
      - bearerAuth: []
    parameters:
      - name: qr_id
        in: path
        type: integer
        required: true
        description: ID of the QR code to update
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: Updated name for the QR code
              example: "Updated Store Entry QR"
            expire_at:
              type: string
              format: date-time
              description: Updated expiration date in ISO format (YYYY-MM-DDTHH:MM:SS), or null to remove expiration
              example: "2025-12-31T23:59:59"
    responses:
      200:
        description: QR code updated successfully
        schema:
          type: object
          properties:
            id:
              type: integer
              description: QR code ID
            name:
              type: string
              description: Updated QR code name
            agency_id:
              type: integer
              description: Agency ID
            qrcode_url:
              type: string
              description: URL to the QR code image
            expire_at:
              type: string
              format: date-time
              description: Updated expiration date and time in ISO format
            created_at:
              type: string
              format: date-time
              description: Creation date and time
            updated_at:
              type: string
              format: date-time
              description: Last update date and time
      400:
        description: Bad request - no update data or invalid date format
      401:
        description: Unauthorized, invalid or expired token
      404:
        description: QR code not found
      500:
        description: Server error
    """
    try:
        qr = QRCode.query.get(qr_id)
        if not qr:
            return jsonify({"error": "QR code not found"}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "No update data provided"}), 400
            
        # Update fields
        if 'name' in data:
            qr.name = data['name']
            
        if 'expire_at' in data:
            if data['expire_at'] is None:
                qr.expire_at = None
            else:
                try:
                    qr.expire_at = datetime.fromisoformat(data['expire_at'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({"error": "Invalid expire_at date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
        
        db.session.commit()
        
        return {
                "id": qr.id,
                "name": qr.name,
                "agency_id": qr.agency_id,
                "qrcode_url": qr.qrcode_url,
                "expire_at": qr.expire_at.isoformat() if qr.expire_at else None,
                "created_at": qr.created_at,
                "updated_at": qr.updated_at
            }, 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@qrcode_bp.route('/v1/qrcode', methods=['GET'])
def get_all_qr_codes():
    """
    Get all QR codes, optionally filtered by agency
    ---
    tags:
      - QR Codes
    parameters:
      - name: agency_id
        in: query
        type: integer
        required: false
        description: Filter QR codes by agency ID
        example: 1
    responses:
      200:
        description: List of QR codes
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: QR code ID
              name:
                type: string
                description: QR code name
              agency_id:
                type: integer
                description: Agency ID
              qrcode_url:
                type: string
                description: URL to the QR code image
              scanner_url:
                type: string
                description: URL encoded in the QR code
              expire_at:
                type: string
                format: date-time
                description: Expiration date and time in ISO format
              is_expired:
                type: boolean
                description: Whether the QR code has expired
              created_at:
                type: string
                format: date-time
                description: Creation date and time
              updated_at:
                type: string
                format: date-time
                description: Last update date and time
      500:
        description: Server error
    """
    try:
        agency_id = request.args.get('agency_id', type=int)
        
        query = QRCode.query
        if agency_id:
            query = query.filter_by(agency_id=agency_id)
            
        qr_codes = query.all()
        
        # Base URL for QR scanner endpoint
        qr_base_url = request.host_url.rstrip('/')
        
        qr_data = [{
            "id": qr.id,
            "name": qr.name,
            "agency_id": qr.agency_id,
            "qrcode_url": qr.qrcode_url,
            "scanner_url": f"{qr_base_url}/api/qr/{qr.content}",
            "expire_at": qr.expire_at.isoformat() if qr.expire_at else None,
            "is_expired": qr.expire_at and qr.expire_at < datetime.now(),
            "created_at": qr.created_at,
            "updated_at": qr.updated_at
        } for qr in qr_codes]
        
        return qr_data, 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@qrcode_bp.route('/v1/qrcode/<int:qr_id>', methods=['GET'])
def get_qr_code(qr_id):
    """
    Get a specific QR code by ID
    ---
    tags:
      - QR Codes
    parameters:
      - name: qr_id
        in: path
        type: integer
        required: true
        description: ID of the QR code to retrieve
        example: 1
    responses:
      200:
        description: QR code details
        schema:
          type: object
          properties:
            id:
              type: integer
              description: QR code ID
            name:
              type: string
              description: QR code name
            agency_id:
              type: integer
              description: Agency ID
            qrcode_url:
              type: string
              description: URL to the QR code image
            scanner_url:
              type: string
              description: URL encoded in the QR code
            expire_at:
              type: string
              format: date-time
              description: Expiration date and time in ISO format
            is_expired:
              type: boolean
              description: Whether the QR code has expired
            created_at:
              type: string
              format: date-time
              description: Creation date and time
            updated_at:
              type: string
              format: date-time
              description: Last update date and time
      404:
        description: QR code not found
      500:
        description: Server error
    """
    try:
        qr = QRCode.query.get(qr_id)
        if not qr:
            return jsonify({"error": "QR code not found"}), 404
            
        # Base URL for QR scanner endpoint
        qr_base_url = request.host_url.rstrip('/')
        
        return {
                "id": qr.id,
                "name": qr.name,
                "agency_id": qr.agency_id,
                "qrcode_url": qr.qrcode_url,
                "scanner_url": f"{qr_base_url}/api/qr/{qr.content}",
                "expire_at": qr.expire_at.isoformat() if qr.expire_at else None,
                "is_expired": qr.expire_at and qr.expire_at < datetime.now(),
                "created_at": qr.created_at,
                "updated_at": qr.updated_at
            }, 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@qrcode_bp.route('/qr/<string:qr_uuid>', methods=['GET'])
def redirect_qr(qr_uuid):
    """
    Redirect user after scanning a QR code
    ---
    tags:
      - QR Codes
    parameters:
      - name: qr_uuid
        in: path
        type: string
        required: true
        description: UUID of the QR code
        example: "a1b2c3d4e5f6"
    responses:
      302:
        description: Redirect to the appropriate product page
      404:
        description: QR code or agency not found
      410:
        description: QR code has expired
      500:
        description: Server error
    """
    try:
        # Find the QR code record
        qr = QRCode.query.filter_by(content=qr_uuid).first()
        if not qr:
            return jsonify({"error": "QR code not found"}), 404
            
        # Check if QR code has expired
        if qr.expire_at and qr.expire_at < datetime.now():
            return jsonify({"error": "This QR code has expired"}), 410
            
        # Get agency information to confirm it exists
        agency = Agency.query.get(qr.agency_id)
        if not agency:
            return jsonify({"error": "Agency not found"}), 404
            
        # Determine frontend URL (in a real app, this would come from configuration)
        # Here I'm using a query parameter approach, but you can structure this however your frontend expects
        frontend_url = f"{request.host_url}/api/v1/product/agency/{qr.agency_id}"
        
        # Redirect to frontend with agency ID
        return redirect(frontend_url, code=302)
        
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
