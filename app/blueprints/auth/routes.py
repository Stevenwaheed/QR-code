from datetime import datetime, timedelta
import json
from app.blueprints.address.methods import get_address_details
from app.blueprints.agency.methods import get_agency_details
from app.blueprints.auth.methods import generate_password, get_user_details, seed_permissions, seed_roles
from app.blueprints.profile.models import Profile
from flask_cors import cross_origin
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.blueprints.agency.models import Agency

from app.utils.validators import (
    generate_otp,
    is_valid_email,
    is_valid_phone_number,
    set_password,
    validate_password,
)
from .models import (
    OTPResetToken,
    RoleType,
    User,
    UserType,
    db,
    Role,
    Permission,
    RolePermission,
)
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    decode_token,
)

auth_pg = Blueprint("auth", __name__)
role_bp = Blueprint("roles", __name__)
permission_bp = Blueprint("permissions", __name__)
user_permission_bp = Blueprint("user_permissions", __name__)


@auth_pg.route("/v1/sign-up", methods=["POST"])
@cross_origin(origins="*")
def sign_up():
    """
    Add New User
    ---
      summary: User Sign-Up
      description: Creates a new user account along with their address and associated entity. Returns user details and tokens upon successful registration.
      tags:
        - User
      
      parameters:
      - in: body
        name: body
        required: true
        schema:
              type: object
              properties:
                first_name:
                  type: string
                  description: First name of the user.
                  example: John
                last_name:
                  type: string
                  description: Last name of the user.
                  example: Doe
                email:
                  type: string
                  description: Email address of the user.
                  example: john.doe@example.com
                phone_number:
                  type: string
                  description: Phone number of the user.
                  example: +1234567890
                password:
                  type: string
                  description: Password for the account.
                  example: P@ssw0rd123
              required:
                - first_name
                - last_name
                - email
                - phone_number
                - password
      responses:
        200:
          description: User successfully registered.
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: added successfully
                  user:
                    type: object
                    properties:
                      id:
                        type: integer
                      email:
                        type: string
                      first_name:
                        type: string
                      last_name:
                        type: string
                      phone_number:
                        type: string
                      role_id:
                        type: integer
                      permissions:
                        type: array
                        items:
                          type: object
                          properties:
                            id:
                              type: integer
                            type:
                              type: string
                            name:
                              type: string
                      created_at:
                        type: string
                      updated_at:
                        type: string
                      access_token:
                        type: string
                      refresh_token:
                        type: string
                      entity:
                        type: object
                        properties:
                          id:
                            type: integer
                          name:
                            type: string
        400:
          description: Bad Request. Invalid input or missing fields.
          content:
            application/json:
              example:
                error: "email is already exist"
        404:
          description: Resource not found.
          content:
            application/json:
              examples:
                country_not_found:
                  message: country not found
                city_not_found:
                  message: city not found
                state_not_found:
                  message: state not found
        500:
          description: Internal Server Error.
    """
    try:
        data = request.json
    except:
        return {"message": "can't receive the request"}, 400
      
    required_fields = [
        # "state_id",
        "password",
        # "city_id",
        # "role_id",
        "last_name",
        "first_name",
        "email",
        "phone_number",
        # "country_id",
        # "street_address",
        # "postal_code",
    ]
    for field in required_fields:
        if field not in data or data[field] == "":
            return jsonify({"error": f"{field} is required"}), 400

    if not is_valid_email(data["email"]):
        return {"message": "invalid email"}, 400

    if not is_valid_phone_number(str(data["phone_number"])):
        return {"message": "invalid phone number"}, 400
    
    # try:
    user = User.query.filter_by(email=data["email"], is_active=True).first()
    if user is not None:
        return {"message": "email is already exist"}, 400

    role = Role.query.filter_by(role_enum=list(RoleType).index(RoleType.ADMIN)).first()
    
    new_user = User(
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_number=str(data["phone_number"]),
        user_type=UserType.ADMIN.value,
        role_id=role.id,
        password_hash=set_password(data["password"]),
    )
    db.session.add(new_user)
    db.session.commit()

    new_profile = Profile(
        phone_number=data["phone_number"], user_id=new_user.id
    )
    db.session.add(new_profile)
    db.session.commit()
    
    # role = Role.query.filter_by(id=user.role_id).first()
    # if role is None:
    #       return {"message": "user does not have role"}, 400

    role_permissions = RolePermission.query.filter_by(role_id=role.id).all()
    permission_ids = [
          role_permission.permission_id for role_permission in role_permissions
      ]

    permissions_list = []
    for permission_id in permission_ids:
      permission = Permission.query.filter_by(id=permission_id).first()

      permissions_list.append(
          {"id": permission.id, "type": permission.type, "name": permission.name}
      )

    access_token = create_access_token(
          identity=json.dumps({"user_id": str(new_user.id)
                                , "permissions": permissions_list
                                }
                              ),
          # additional_claims=additional_claims,
      )

    refresh_token = create_refresh_token(
          identity=json.dumps({"user_id": str(new_user.id)
                                , "permissions": permissions_list
                                }
                              ),
          # additional_claims=additional_claims,
      )
    
    user_details = get_user_details(new_user)
    user_details['permissions'] = permissions_list
    user_details['access_token'] = access_token
    user_details['refresh_token'] = refresh_token
    
    return user_details, 200
    # except:
    #     db.session.rollback()
    #     return {"error": "couldn't add user"}, 400





@auth_pg.route("/v1/user", methods=["POST"])
@cross_origin(origins="*")
@jwt_required()
def add_user():
    """
    Create a new user.
    This endpoint creates a new user with their associated address and profile information.
    Requires JWT authentication from an authorized user.
    ---
    tags:
      - User
    security:
        - bearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            first_name:
              type: string
              example: John
              description: User's first name
            last_name:
              type: string
              example: Doe
              description: User's last name
            email:
              type: string
              example: john.doe@example.com
              description: User's email address
            phone_number:
              type: string
              example: "+1234567890"
              description: User's phone number
            role_id:
              type: integer
              example: 1
              description: ID of the user's role
    responses:
      200:
        description: User created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "added successfully"
                user:
                  type: object
                  properties:
                    id:
                      type: integer
                      example: 1
                    email:
                      type: string
                      example: "john.doe@example.com"
                    first_name:
                      type: string
                      example: "John"
                    last_name:
                      type: string
                      example: "Doe"
                    phone_number:
                      type: string
                      example: "+1234567890"
                    role_id:
                      type: integer
                      example: 1
                    agency:
                      type: object
                      properties:
                        id:
                          type: integer
                          example: 1
                        name:
                          type: string
                          example: "Example agency"
                        icon:
                          type: string
                          example: "https://example.com/icon.png"
                    password:
                      type: string
                      example: "generatedPassword123"
                    created_at:
                      type: string
                      example: "2024-02-08T12:00:00Z"
                    updated_at:
                      type: string
                      example: "2024-02-08T12:00:00Z"
                    entity:
                      type: object
                      properties:
                        id:
                          type: integer
                          example: 1
                        name:
                          type: string
                          example: "USER"
      400:
        description: Bad request
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "email is already exist"
      404:
        description: Resource not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "role not found"
    """
    
    try:
        data = request.json
    except:
        return {"message": "can't receive the request"}, 400

    payload = get_jwt_identity()
    payload = json.loads(payload)
    
    user = User.query.filter_by(id=payload['user_id'], is_active=True).first()
    
    agency = Agency.query.filter_by(id=user.agency_id).first()
    if agency is None and user.user_type != UserType.SUPERADMIN:
      return {"message": "user does not have agency"}, 404
    
    required_fields = [
        # "state_id",
        # "city_id",
        "role_id",
        "last_name",
        "first_name",
        "email",
        "phone_number",
        # "country_id",
        # "street_address",
        # 'max_credit'
        # "postal_code",
    ]
    for field in required_fields:
        if field not in data or data[field] == "":
            return jsonify({"error": f"{field} is required"}), 400

    if not is_valid_email(data["email"]):
        return {"message": "invalid email"}, 400

    if not is_valid_phone_number(str(data["phone_number"])):
        return {"message": "invalid phone number"}, 400

    role = Role.query.filter_by(id=data['role_id']).first()
    if role is None:
      return {"message": "role not found"}, 404
    
    # try:
    stored_user = User.query.filter_by(email=data["email"], is_active=True).first()
    if stored_user is not None:
        return {"message": "email is already exist"}, 400
    
    user_password = generate_password()
    
    new_user = User(
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone_number=data["phone_number"],
        agency_id=agency.id,
        user_type=UserType.USER.value,
        role_id=role.id if role is not None else None,
        password_hash=set_password(user_password),
    )
    db.session.add(new_user)
    db.session.commit()
    

    new_profile = Profile(
        phone_number=data["phone_number"], user_id=new_user.id
    )
    db.session.add(new_profile)
    db.session.commit()
    
    user_details = get_user_details(new_user)
    if agency is not None:
      agency_details = get_agency_details(agency)
      user_details['agency'] = agency_details
    else:
      user_details['agency'] = None
    
    user_details["password"] = user_password
    
    return user_details, 200
    # except:
    #     db.session.rollback()
    #     return {"error": "couldn't add user"}, 400



@auth_pg.route("/v1/user", methods=["GET"])
@jwt_required()
def get_users():
  """
  Get users based on requester's permissions
  ---
  tags:
    - user
  summary: Retrieve users based on authorization
  description: Returns a list of users. For superadmins, returns all users; for other users, returns only users from their agency.
  operationId: getUsers
  security:
    - bearerAuth: []
  responses:
    200:
      description: List of users retrieved successfully
      schema:
        type: array
        items:
          type: object
          properties:
            id:
              type: integer
              description: User ID
            email:
              type: string
              description: User's email address
            name:
              type: string
              description: User's name
            user_type:
              type: string
              description: Type of user (e.g., SUPERADMIN, ADMIN, USER)
            is_active:
              type: boolean
              description: Whether the user is active
            agency:
              type: object
              description: Details of the agency this user belongs to (null for superadmins)
              properties:
                id:
                  type: integer
                  description: Agency ID
                name:
                  type: string
                  description: Agency name
                # Additional agency properties would be listed here
    401:
      description: Unauthorized - Invalid or expired token
      schema:
        type: object
        properties:
          msg:
            type: string
            description: Error message
    403:
      description: Forbidden - User does not have required permissions
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    500:
      description: Server error
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
  """
  payload = get_jwt_identity()
  payload = json.loads(payload)
  
  user = User.query.filter_by(id=payload['user_id'], is_active=True).first()
  agency = Agency.query.filter_by(id=user.agency_id).first()
  if agency is None and user.user_type == UserType.SUPERADMIN:
    users = User.query.all()
  else:
    users = User.query.filter_by(agency_id=agency.id).all()
  
  users_list = []
  for user  in users:
    
    user_details = get_user_details(user)
    if agency is not None:
      agency_details = get_agency_details(agency)
      user_details['agency'] = agency_details
    else:
      user_details['agency'] = None
      
    users_list.append(user_details)
    
  return users_list, 200





@auth_pg.route("/v1/user/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user_by_id(user_id):
  """
  Get a specific user by ID
  ---
  tags:
    - user
  summary: Retrieve a user by ID
  description: Returns details of a specific user. Superadmins can access any user. Other users can only access users from their own agency.
  operationId: getUserById
  security:
    - bearerAuth: []
  parameters:
    - name: user_id
      in: path
      description: ID of the user to retrieve
      required: true
      type: integer
      format: int64
  responses:
    200:
      description: User details retrieved successfully
      schema:
        type: object
        properties:
          id:
            type: integer
            description: User ID
          email:
            type: string
            description: User's email address
          name:
            type: string
            description: User's name
          user_type:
            type: string
            description: Type of user (e.g., SUPERADMIN, ADMIN, USER)
          is_active:
            type: boolean
            description: Whether the user is active
          agency:
            type: object
            description: Details of the agency this user belongs to (null for superadmins)
            properties:
              id:
                type: integer
                description: Agency ID
              name:
                type: string
                description: Agency name
              # Additional agency properties would be listed here
    400:
      description: Bad request - User not part of requester's agency
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    401:
      description: Unauthorized - Invalid or expired token
      schema:
        type: object
        properties:
          msg:
            type: string
            description: Error message
    404:
      description: User not found
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    500:
      description: Server error
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
  """
  payload = get_jwt_identity()
  payload = json.loads(payload)

  owner = User.query.filter_by(id=payload['user_id'], is_active=True).first()
  user = User.query.filter_by(id=user_id, is_active=True).first()
  if owner and owner.user_type != UserType.SUPERADMIN:
    if user is None:
      return {"message":"user not found"}, 404
    
    if owner.agency_id != user.agency_id:
      return {"message":"this user is not part of your agency"}, 400

  agency = Agency.query.filter_by(id=user.agency_id).first()
  
  user_details = get_user_details(user)
  if agency is not None:
    agency_details = get_agency_details(agency)
    user_details['agency'] = agency_details
  else:
    user_details['agency'] = None
    
  return user_details, 200






@auth_pg.route('/v1/roles/<int:role_id>/permissions', methods=['POST'])
def assign_permissions_to_role(role_id):
  """
  Assign permissions to a role
  ---
  tags:
    - roles
    - permissions
  summary: Assign permissions to a specific role
  description: Replaces all existing permission assignments for the specified role with the new set of permissions
  operationId: assignPermissionsToRole
  parameters:
    - name: role_id
      in: path
      description: ID of the role to assign permissions to
      required: true
      type: integer
      format: int64
    - name: body
      in: body
      description: List of permission IDs to assign to the role
      required: true
      schema:
        type: object
        required:
          - permission_ids
        properties:
          permission_ids:
            type: array
            items:
              type: integer
            description: Array of permission IDs to assign to the role
  responses:
    200:
      description: Permissions successfully assigned to role
      schema:
        type: object
        properties:
          message:
            type: string
            description: Success message
          role_id:
            type: integer
            description: ID of the role
          permission_ids:
            type: array
            items:
              type: integer
            description: IDs of the permissions assigned to the role
    400:
      description: Bad request - Invalid input data
      schema:
        type: object
        properties:
          error:
            type: string
            description: Error message
    404:
      description: Role or permissions not found
      schema:
        type: object
        properties:
          error:
            type: string
            description: Error message
          missing_ids:
            type: array
            items:
              type: integer
            description: IDs of permissions that do not exist
    500:
      description: Server error
      schema:
        type: object
        properties:
          error:
            type: string
            description: Error message
  """
  try:
      # Get the role
      role = Role.query.get(role_id)
      if not role:
          return jsonify({"error": "Role not found"}), 404
          
      # Get the permission IDs from the request
      data = request.get_json()
      if not data or 'permission_ids' not in data:
          return jsonify({"error": "Permission IDs are required"}), 400
          
      permission_ids = data['permission_ids']
      if not isinstance(permission_ids, list):
          return jsonify({"error": "Permission IDs must be a list"}), 400
          
      # Verify all permissions exist
      existing_permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
      existing_ids = [p.id for p in existing_permissions]
      
      missing_ids = [pid for pid in permission_ids if pid not in existing_ids]
      if missing_ids:
          return jsonify({
              "error": "Some permission IDs do not exist", 
              "missing_ids": missing_ids
          }), 404
      
      # Delete existing role permissions to avoid duplicates
      RolePermission.query.filter_by(role_id=role_id).delete()
      
      # Create new role permissions
      new_role_permissions = []
      for permission_id in permission_ids:
          role_permission = RolePermission(
              role_id=role_id,
              permission_id=permission_id
          )
          new_role_permissions.append(role_permission)
          
      db.session.add_all(new_role_permissions)
      db.session.commit()
      
      return jsonify({
          "message": f"Successfully assigned {len(permission_ids)} permissions to role {role.name}",
          "role_id": role_id,
          "permission_ids": permission_ids
      }), 200
      
  except SQLAlchemyError as e:
      db.session.rollback()
      return jsonify({"error": str(e)}), 500

@auth_pg.route('/v1/roles/<int:role_id>/permissions', methods=['GET'])
def get_role_permissions(role_id):
    """
    Get all permissions assigned to a role
    ---
    tags:
      - roles
      - permissions
    summary: Retrieve all permissions assigned to a specific role
    description: Returns the role details and a list of all permissions assigned to the specified role
    operationId: getRolePermissions
    parameters:
      - name: role_id
        in: path
        description: ID of the role to get permissions for
        required: true
        type: integer
        format: int64
    responses:
      200:
        description: Role permissions retrieved successfully
        schema:
          type: object
          properties:
            role:
              type: object
              properties:
                id:
                  type: integer
                  description: Role ID
                name:
                  type: string
                  description: Role name
                role_enum:
                  type: string
                  description: Role enumeration value
            permissions:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Permission ID
                  type:
                    type: string
                    description: Permission type
                  name:
                    type: string
                    description: Permission name
      404:
        description: Role not found
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message
    """
    try:
        # Check if role exists
        role = Role.query.get(role_id)
        if not role:
            return jsonify({"error": "Role not found"}), 404
            
        # Get all role permissions
        role_permissions = RolePermission.query.filter_by(role_id=role_id).all()
        permission_ids = [rp.permission_id for rp in role_permissions]
        
        # Get permission details
        permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
        permission_data = [{
            "id": p.id,
            "type": p.type,
            "name": p.name
        } for p in permissions]
        
        return jsonify({
            "role": {
                "id": role.id,
                "name": role.name,
                "role_enum": role.role_enum
            },
            "permissions": permission_data
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500




@auth_pg.route("/v1/login", methods=["POST"])
@cross_origin(origins="*")
def log_in():
    """
    Log in an existing user.

    This endpoint allows a user to log in by providing their email and password.
    It validates the credentials and returns an access token and refresh token if successful.

    ---
    tags:
      - User
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            properties:
                email:
                    type: string
                    example: user@example.com
                    description: User's email address
                password:
                    type: string
                    example: securepassword
                    description: User's password
    responses:
      200:
        description: User logged in successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                user:
                  type: object
                  properties:
                    id:
                      type: integer
                      example: 1
                    first_name:
                      type: string
                      example: John
                    last_name:
                      type: string
                      example: Doe
                    phone_number:
                      type: string
                      example: "+1234567890"
                    email:
                      type: string
                      example: user@example.com
                    user_type:
                      type: string
                      example: "regular"
                    access_token:
                      type: string
                      example: "your_access_token"
                    refresh_token:
                      type: string
                      example: "your_refresh_token"
      400:
        description: Bad request, invalid credentials
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "wrong password"
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "wrong email"
    """
    try:
        data = request.json
    except:
        return {"message": "can't receive the request"}, 400

    if "email" not in data or data["email"] == "":
        return {"message": "email is required"}, 400

    if "password" not in data or data["password"] == "":
        return {"message": "password is required"}, 400

    user = User.query.filter_by(email=data["email"], is_active=True).first()
    if user is None:
        return {"message": "wrong email"}, 404
    
    if not user.check_password(data["password"]):
        return {"message": "wrong password"}, 400

    # additional_claims = {"user_type": user.user_type.value, "email": user.email}

    role = Role.query.filter_by(id=user.role_id).first()
    if role is None:
        return {"message": "user does not have role"}, 400

    role_permissions = RolePermission.query.filter_by(role_id=role.id).all()
    permission_ids = [
        role_permission.permission_id for role_permission in role_permissions
    ]

    permissions_list = []
    for permission_id in permission_ids:
        permission = Permission.query.filter_by(id=permission_id).first()

        permissions_list.append(
            {"id": permission.id, "type": permission.type, "name": permission.name}
        )

    access_token = create_access_token(
        identity=json.dumps({"user_id": str(user.id)
                             , "permissions": permissions_list
                             }),
        # additional_claims=additional_claims,
    )

    refresh_token = create_refresh_token(
        identity=json.dumps({"user_id": str(user.id)
                             , "permissions": permissions_list
                             }),
        # additional_claims=additional_claims,
    )

    addresses = get_address_details(user.id, is_primary=True)
    
    agency = Agency.query.filter_by(id=user.agency_id).first()
    if agency is None:
        agency_json = None
    else:
        agency_json = get_agency_details(agency)
        

    user_details = get_user_details(user)
    # user_details['permissions'] = permissions_list
    user_details['access_token'] = access_token
    user_details['refresh_token'] = refresh_token
    user_details['address'] = addresses
    user_details['agency'] = agency_json

    return user_details, 200


@auth_pg.route("/v1/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    payload = get_jwt_identity()
    payload = json.loads(payload)
    user = User.query.filter_by(id=payload["user_id"], is_active=True).first()
    if user is None:
      return {"message": "user not found"}, 404
    
    additional_claims = {"user_type": user.user_type, "email": user.email}

    new_access_token = create_access_token(
        identity=payload["user_id"], additional_claims=additional_claims
    )

    return {"access_token": new_access_token}, 200


@auth_pg.route("/v1/request-otp", methods=["POST"])
def request_otp():
    """
    Request an OTP for password reset
    This endpoint sends an OTP to the user's email for password reset. It does not reveal whether the email exists in the system
    to prevent enumeration attacks.

    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            properties:
              email:
                type: string
                example: user@example.com
                description: User's email address
    responses:
      200:
        description: OTP sent successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "If an account exists, an OTP will be sent"
      400:
        description: Missing email
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Email is required"
    """
    email = request.json.get("email", None)

    if not email:
        return {"error": "Email is required"}, 400

    user = User.query.filter_by(email=email).first()

    if not user:
        # Don't reveal if email exists to prevent enumeration
        return {"message": "If an account exists, an OTP will be sent"}, 200

    # Delete any existing unused OTP tokens
    OTPResetToken.query.filter_by(user_id=user.id, is_used=False).delete()

    # Generate OTP
    otp = generate_otp()

    # Create new OTP token (valid for 15 minutes)
    otp_token = OTPResetToken(
        user_id=user.id, otp=otp, expires_at=datetime.utcnow() + timedelta(minutes=15)
    )

    db.session.add(otp_token)
    db.session.commit()

    # TODO: Send OTP via email or SMS
    # send_otp_to_user(user.email, otp)

    return {"message": "OTP sent successfully", "otp": otp}, 200


@auth_pg.route("/v1/verify-otp", methods=["POST"])
def verify_otp():
    """
    Verify OTP for password reset
    This endpoint allows the user to verify the OTP sent to their email for password reset.

    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            properties:
              email:
                type: string
                example: user@example.com
                description: User's email address
              otp:
                type: string
                example: "123456"
                description: OTP received by the user
    responses:
      200:
        description: OTP verified successfully and reset token created
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "OTP verified successfully"
                reset_token:
                  type: string
                  example: "your_temp_reset_token"
      400:
        description: Invalid OTP or OTP expired
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Invalid OTP"
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "User not found"
    """
    email = request.json.get("email")
    otp = request.json.get("otp")

    if not email or not otp:
        return {"error": "Email and OTP are required"}, 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return {"error": "User not found"}, 404

    # Find valid, unused OTP token
    otp_token = OTPResetToken.query.filter_by(
        user_id=user.id, otp=otp, is_used=False
    ).first()

    if not otp_token:
        return {"error": "Invalid OTP"}, 400

    # Check if OTP is expired
    if otp_token.expires_at < datetime.utcnow():
        db.session.delete(otp_token)
        db.session.commit()
        return {"error": "OTP has expired"}, 400

    # Mark OTP as used and create a temporary reset token
    otp_token.is_used = True
    db.session.commit()

    # Generate a temporary reset token
    additional_claims = {"user_type": user.user_type.value, "email": user.email}

    reset_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims,
        expires_delta=timedelta(minutes=15),
    )

    # reset_token = create_access_token(
    #     identity=user.id,
    #     expires_delta=timedelta(minutes=15)
    # )

    return {"message": "OTP verified successfully", "reset_token": reset_token}, 200


@auth_pg.route("/v1/reset-password", methods=["POST"])
def reset_password():
    """
    Reset the user's password using a valid reset token
    This endpoint allows the user to reset their password by providing a valid reset token and a new password.

    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            properties:
              reset_token:
                type: string
                example: "your_temp_reset_token"
                description: Temporary reset token received after OTP verification
              new_password:
                type: string
                example: "new_secure_password"
                description: New password to be set for the user
    responses:
      200:
        description: Password reset successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Password reset successfully"
      400:
        description: Invalid or expired reset token or weak password
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Invalid or expired reset token"
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "User not found"
    """
    reset_token = request.json.get("reset_token")
    new_password = request.json.get("new_password")

    if not reset_token or not new_password:
        return {"error": "Reset token and new password are required"}, 400

    # Validate password strength
    is_valid, validation_message = validate_password(new_password)
    if not is_valid:
        return {"error": validation_message}, 400

    try:
        # user_id = verify_jwt_in_request(reset_token)
        decoded_token = decode_token(reset_token)
        user_id = decoded_token["sub"]

        # Get user
        user = User.query.get(user_id)

        if not user:
            return {"error": "User not found"}, 404

        # Update password
        user.password_hash = set_password(new_password)
        db.session.commit()

        return {"message": "Password reset successfully"}, 200

    except Exception as e:
        return {"error": "Invalid or expired reset token"}, 400


# Helper function for error handling
def handle_error(error, message="An error occurred"):
    """
    Helper function to handle and format database errors
    """
    db.session.rollback()
    return jsonify({"status": "error", "message": message, "details": str(error)}), 400


@role_bp.route("/v1/role", methods=["GET"])
@jwt_required()
def get_roles():
    """
        Retrieve all roles for the authenticated user
        ---
        tags:
          - Roles
        description: |
          This endpoint retrieves a list of all roles associated with the authenticated user's agency. 
          Each role includes its permissions and timestamps for creation and last update.
        responses:
          200:
            description: Successfully retrieved the list of roles
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: The ID of the role.
                  name:
                    type: string
                    description: The name of the role.
                  permission:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: integer
                          description: The ID of the permission.
                        type:
                          type: string
                          description: The type of the permission.
                        name:
                          type: string
                          description: The name of the permission.
                        created_at:
                          type: string
                          format: date-time
                          description: Timestamp when the permission was created.
                        updated_at:
                          type: string
                          format: date-time
                          description: Timestamp when the permission was last updated.
                  created_at:
                    type: string
                    format: date-time
                    description: Timestamp when the role was created.
                  updated_at:
                    type: string
                    format: date-time
                    description: Timestamp when the role was last updated.
          500:
            description: Internal server error
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: "error"
                message:
                  type: string
                  description: Error message describing the issue.
        security:
          - bearerAuth: []
    """
    try:
        roles = Role.query.all()
        
        roles_list = []
        for role in roles:
          permissions_list = []
          role_permissions = RolePermission.query.filter_by(role_id=role.id).all()
          for role_permission in role_permissions:
            permission = Permission.query.filter_by(id=role_permission.permission_id).first()
            
            permissions_list.append({
              "id": permission.id,
              "type": permission.type,
              "name": permission.name,
              "created_at": permission.created_at,
              "updated_at": permission.updated_at,
            })
          
          roles_list.append(
            {
              "id": role.id,
              "name": role.name,
              "permission": permissions_list,
              "created_at": role.created_at.isoformat(),
              "updated_at": role.updated_at.isoformat(),
            }
          )
        return jsonify(roles_list), 200

    except SQLAlchemyError as e:
        return handle_error(e, "Failed to retrieve roles")


@role_bp.route("/v1/role/<int:role_id>", methods=["GET"])
# @jwt_required()
def get_role_by_id(role_id):
  """
      Retrieve a specific role by its ID for the authenticated user
      ---
      tags:
        - Roles
      description: |
        This endpoint retrieves a specific role identified by its ID for the authenticated user's agency. 
        It returns the role details along with its associated permissions.
      parameters:
        - name: role_id
          in: path
          required: true
          type: integer
          description: The ID of the role to retrieve.
      responses:
        200:
          description: Successfully retrieved the role
          schema:
            type: object
            properties:
              id:
                type: integer
                description: The ID of the role.
              name:
                type: string
                description: The name of the role.
              permission:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The ID of the permission.
                    type:
                      type: string
                      description: The type of the permission.
                    name:
                      type: string
                      description: The name of the permission.
                    created_at:
                      type: string
                      format: date-time
                      description: Timestamp when the permission was created.
                    updated_at:
                      type: string
                      format: date-time
                      description: Timestamp when the permission was last updated.
              created_at:
                type: string
                format: date-time
                description: Timestamp when the role was created.
              updated_at:
                type: string
                format: date-time
                description: Timestamp when the role was last updated.
        404:
          description: Role not found for the given ID.
          schema:
            type: object
            properties:
              message:
                type: string
        500:
          description: Internal server error.
          schema:
            type: object
            properties:
              status:
                type: string
                example: "error"
              message:
                type: string
      security:
        - bearerAuth: []
  """
  try:
      # payload = get_jwt_identity()
      # payload = json.loads(payload)
      # user = User.query.filter_by(id=payload["user_id"]).first()
      role = Role.query.filter_by(id=role_id).first()
      if role is None:
          return {"message": "role not found"}, 404

      permissions_list = []
      role_permissions = RolePermission.query.filter_by(role_id=role.id).all()
      for role_permission in role_permissions:
        permission = Permission.query.filter_by(id=role_permission.permission_id).first()
        permissions_list.append({
          "id": permission.id,
          "type": permission.type,
          "name": permission.name,
          "created_at": permission.created_at,
          "updated_at": permission.updated_at,
        })
        
      return jsonify(
          {
              "id": role.id,
              "name": role.name,
              "permission":permissions_list,
              "created_at": role.created_at.isoformat(),
              "updated_at": role.updated_at.isoformat(),
          }
      )

  except SQLAlchemyError as e:
      return handle_error(e, "Failed to retrieve role")


@role_bp.route("/v1/role/<int:role_id>/user/<int:user_id>", methods=["GET"])
@jwt_required()
def assign_user_role(role_id, user_id):
  """
      Assign a role to a user
      ---
      tags:
        - Roles
      description: |
        This endpoint assigns a specified role to a user. It requires both the role ID and the user ID.
        If successful, it returns the user's details along with the assigned role and its permissions.
      parameters:
        - name: role_id
          in: path
          required: true
          type: integer
          description: The ID of the role to assign.
        - name: user_id
          in: path
          required: true
          type: integer
          description: The ID of the user to whom the role will be assigned.
      responses:
        200:
          description: Role assigned successfully.
          schema:
            type: object
            properties:
              first_name:
                type: string
                description: The first name of the user.
              last_name:
                type: string
                description: The last name of the user.
              phone_number:
                type: string
                description: The phone number of the user.
              email:
                type: string
                description: The email address of the user.
              agency:
                type: object
                properties:
                  id:
                    type: integer
                    description: The ID of the agency.
                  name:
                    type: string
                    description: The name of the agency.
                  created_at:
                    type: string
                    format: date-time
                    description: Timestamp when the agency was created.
              role:
                type: object
                properties:
                  id:
                    type: integer
                    description: The ID of the assigned role.
                  name:
                    type: string
                    description: The name of the assigned role.
                  permission:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: integer
                          description: The ID of the permission.
                        type:
                          type: string
                          description: The type of permission.
                        name:
                          type: string
                          description: The name of the permission.
                        created_at:
                          type: string
                          format: date-time
                          description: Timestamp when the permission was created.
                        updated_at:
                          type: string
                          format: date-time
                          description: Timestamp when the permission was last updated.
                  created_at:
                    type: string
                    format: date-time
                    description: Timestamp when the role was created.
                  updated_at:
                    type: string
                    format: date-time
                    description: Timestamp when the role was last updated.
              created_at:
                type: string
                format: date-time
                description: Timestamp when the user was created.
              updated_at:
                type: string
                format: date-time
                description: Timestamp when the user was last updated.
              user_type:
                type: string
                description: Type of user (e.g., admin, regular).
        404:
          description: User or role not found for given IDs.
          schema:
            type: object
            properties:
              message:
                type: string
        400:
          description: Failed to assign role due to an error in processing.
          schema:
            type: object
            properties:
              message:
                type: string
        500:
          description: Internal server error.
          schema:
            type: object
            properties:
              status:
                type: string
                example: "error"
              message:
                type: string  
      security:
        - bearerAuth: []
  """
  user = User.query.filter_by(id=user_id).first()
  if user is None:
      return {"message": "user not found"}, 404

  role = Role.query.filter_by(id=role_id).first()
  if role is None:
      return {"message": "role not found"}, 404

  permissions_list = []
  role_permissions = RolePermission.query.filter_by(role_id=role.id).all()
  
  for role_permission in role_permissions:
    permission = Permission.query.filter_by(id=role_permission.permission_id).first()
    
    permissions_list.append({
      "id": permission.id,
      "type": permission.type,
      "name": permission.name,
      "created_at": permission.created_at,
      "updated_at": permission.updated_at,
    })
  
  try:
      user.role_id = role.id
      db.session.commit()

      agency = agency.query.filter_by(id=user.agency_id).first()
      if agency is None:
          agency_json = None
      else:
          agency_json = {
              "id": agency.id,
              "name": agency.name,
              "created_at": agency.created_at,
          }

      return {
          "first_name": user.first_name,
          "last_name": user.last_name,
          "phone_number": user.phone_number,
          "email": user.email,
          "agency": agency_json,
          "role": {
            "id": role.id,
            "name": role.name,
            "permission":permissions_list,  
            "created_at": role.created_at,
            "updated_at": role.updated_at,
          } if role is not None else None,
          "created_at": user.created_at,
          "updated_at": user.updated_at,
          "user_type": user.user_type.value,
      }
  except:
      db.session.rollback()
      return {"message": "can't assign the role"}, 400




@auth_pg.route("/v1/user-permission", methods=["GET"])
@jwt_required()
def get_user_permissions():
    """
    Retrieve all permissions
    ---
    tags:
      - Permissions
    description: |
      This endpoint retrieves a list of all permissions available in the system.
    responses:
      200:
        description: Successfully retrieved the list of permissions
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: The ID of the permission.
              type:
                type: string
                description: The type of the permission.
              name:
                type: string
                description: The name of the permission.
              created_at:
                type: string
                format: date-time
                description: Timestamp when the permission was created.
              updated_at:
                type: string
                format: date-time
                description: Timestamp when the permission was last updated.
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
              description: Error message describing the issue.
    security:
      - bearerAuth: []  # Assuming JWT authentication is required for this endpoint
    """
    try:
        payload = get_jwt_identity()
        payload = json.loads(payload)
        user = User.query.filter_by(id=payload["user_id"]).first()
        if user is None:
            return {"message": "user not found"}, 404

        permissions = Permission.query.filter_by(agency_id=user.agency_id).all()

        return jsonify(
            [
                {
                    "id": permission.id,
                    "type": permission.type,
                    "name": permission.name,
                    "created_at": permission.created_at.isoformat(),
                    "updated_at": permission.updated_at.isoformat(),
                }
                for permission in permissions
            ]
        )

    except SQLAlchemyError as e:
        return handle_error(e, "Failed to retrieve permissions")






@auth_pg.route("/v1/permission", methods=["GET"])
@jwt_required()
def get_permissions():
    """
    Retrieve all permissions
    ---
    tags:
      - Permissions
    description: |
      This endpoint retrieves a list of all permissions available in the system.
    responses:
      200:
        description: Successfully retrieved the list of permissions
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: The ID of the permission.
              type:
                type: string
                description: The type of the permission.
              name:
                type: string
                description: The name of the permission.
              created_at:
                type: string
                format: date-time
                description: Timestamp when the permission was created.
              updated_at:
                type: string
                format: date-time
                description: Timestamp when the permission was last updated.
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
              description: Error message describing the issue.
    security:
      - bearerAuth: []  # Assuming JWT authentication is required for this endpoint
    """
    try:
        permissions = Permission.query.all()

        return jsonify(
            [
                {
                    "id": permission.id,
                    "type": permission.type,
                    "name": permission.name,
                    "created_at": permission.created_at.isoformat(),
                    "updated_at": permission.updated_at.isoformat(),
                }
                for permission in permissions
            ]
        )

    except SQLAlchemyError as e:
        return handle_error(e, "Failed to retrieve permissions")



@auth_pg.route("/v1/permission/<int:permission_id>", methods=["GET"])
@jwt_required()
def get_permission_by_id(permission_id):
    """
    Retrieve a permission by ID
    ---
    tags:
      - Permissions
    description: |
      This endpoint retrieves a specific permission based on the provided permission ID.
    parameters:
      - name: permission_id
        in: path
        required: true
        type: integer
        description: The ID of the permission to retrieve.
    responses:
      200:
        description: Successfully retrieved the permission
        schema:
          type: object
          properties:
            id:
              type: integer
              description: The ID of the permission.
            type:
              type: string
              description: The type of the permission.
            name:
              type: string
              description: The name of the permission.
            created_at:
              type: string
              format: date-time
              description: Timestamp when the permission was created.
            updated_at:
              type: string
              format: date-time
              description: Timestamp when the permission was last updated.
      404:
        description: Permission not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Permission not found"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            status:
              type: string
              example: "error"
            message:
              type: string
              description: Error message describing the issue.
    security:
      - bearerAuth: []  # Assuming JWT authentication is required for this endpoint
    """
    try:
        payload = get_jwt_identity()
        payload = json.loads(payload)
        user = User.query.filter_by(id=payload["user_id"]).first()
        if user is None:
            return {"message": "user not found"}, 404

        permission = Permission.query.filter_by(
            id=permission_id, agency_id=user.agency_id
        ).first()
        if permission is None:
            return jsonify("Permission not found"), 404

        return jsonify(
            {
                "id": permission.id,
                "type": permission.type,
                "name": permission.name,
                "created_at": permission.created_at.isoformat(),
                "updated_at": permission.updated_at.isoformat(),
            }
        )

    except SQLAlchemyError as e:
        return handle_error(e, "Failed to retrieve permission")



@auth_pg.route("/v1/sync-roles-permission", methods=["GET"])
def sync_permission_api():
    """
    Synchronize permissions
    ---
    tags:
      - Permissions
    description: |
      This endpoint synchronizes the permissions for the current user or system.
      It retrieves the latest permissions and updates them as necessary.
    responses:
      200:
        description: Successfully synchronized permissions
        schema:
          type: object
          properties:
            permissions:
              type: array
              items:
                type: string
              description: List of synchronized permissions
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            message:
              type: string
              description: Error message describing the issue
    """
    seed_permissions()
    seed_roles()
    return "Done", 200
