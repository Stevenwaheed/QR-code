
from functools import wraps
import json
import random
import string
from app.blueprints.agency.models import Agency
from app.blueprints.profile.models import Profile
from db.database import db
from app.blueprints.auth.models import Permission, Role, RolePermission, RoleType, User
from flask_jwt_extended import (
    get_jwt_identity,
)
from flask import jsonify

def permission_required(*permission_names):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            payload = get_jwt_identity()
            payload = json.loads(payload)
            user = User.query.filter_by(id=payload['user_id']).first()

            if not user:
                return jsonify({"message": "User not found"}), 404

            # role = Role.query.filter_by(id=user.role_id).first()
            # if not role:
            #     return jsonify({"message": "Role not found"}), 404

            user_permissions = payload.get('permissions', [])

            for permission_type, permission_name in permission_names:
                if any(
                    perm.get('type') == permission_type and perm.get('name') == permission_name
                    for perm in user_permissions
                ):
                    return f(*args, **kwargs)

            return jsonify({"message": "Permission denied"}), 403

        return decorated_function
    return decorator




def generate_password(length=12, use_uppercase=True, use_numbers=True, use_special_chars=True):
    # Define the character sets to choose from
    character_set = string.ascii_lowercase  # Always include lowercase letters
    
    if use_uppercase:
        character_set += string.ascii_uppercase
    if use_numbers:
        character_set += string.digits
    if use_special_chars:
        character_set += string.punctuation
    
    # Ensure the password length is at least 1
    if length < 1:
        raise ValueError("Password length must be at least 1")
    
    # Generate the password
    password = ''.join(random.choice(character_set) for _ in range(length))
    
    return password



def seed_permissions():
    permissions = ["read", 'write', 'delete', 'update']
    scopes = ["qr", 'user']
    
    # Create permissions
    for permission in permissions:
        for scope in scopes:
            new_permission = Permission(
                type=permission,
                name=scope
            )
            db.session.add(new_permission)
            db.session.commit()
    

def seed_roles():
    # Create roles using RoleType enum
    for role_type in RoleType:
        new_role = Role(
            name=role_type.value,
            role_enum=list(RoleType).index(role_type)
        )
        db.session.add(new_role)
        db.session.commit()
    
    

        
        
def get_user_details(user):
    role = Role.query.filter_by(id=user.role_id).first()
    profile = Profile.query.filter_by(user_id=user.id).first()
    return {
              "id": user.id,
              "email": user.email,
              "first_name": user.first_name,
              "last_name": user.last_name,
              "phone_number": user.phone_number,
              "role": {
                "id": role.id,
                "name":role.name
                } if role is not None else None,
              "profile":{
                  "id":profile.id,
                  "phone_number":profile.phone_number,
                  "is_visible":profile.is_visible
              },
              "is_verified": user.is_verified,
              "is_active": user.is_active,
              "user_type": user.user_type.value,
              "created_at": user.created_at,
              "updated_at": user.updated_at,
              
          }