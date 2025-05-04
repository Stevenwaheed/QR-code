from datetime import datetime
from db.database import db
from sqlalchemy import func, Enum as SQLAlchemyEnum
from enum import Enum
from werkzeug.security import check_password_hash


class UserType(Enum):
    SUPERADMIN = 'SUPERADMIN'
    ADMIN = "ADMIN"
    USER='USER'


class RoleType(Enum):
    MANAGER='MANAGER'
    ADMIN='ADMIN'
    EMPLOYEE='EMPLOYEE'


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_number = db.Column(db.String(50))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    user_type = db.Column(SQLAlchemyEnum(UserType, name='usertype'))
    is_active = db.Column(db.Boolean, default=True)
    agency_id = db.Column(db.Integer, db.ForeignKey('agencies.id'))
    is_superuser = db.Column(db.Boolean, default=False)
    is_staff = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    role_enum = db.Column(db.Integer)
    # agency_id = db.Column(db.Integer, db.ForeignKey('agencies.id'))
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    


class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    name = db.Column(db.String)
    agency_id = db.Column(db.Integer, db.ForeignKey('agencies.id'))
    
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())


class RolePermission(db.Model):
    __tablename__ = 'role_permission'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())




class OTPResetToken(db.Model):
    __tablename__ = 'otp_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='otp_reset_tokens')
