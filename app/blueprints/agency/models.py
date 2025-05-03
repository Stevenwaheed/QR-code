

from datetime import datetime
from app.blueprints.qrcode.models import QRCode
from db.database import db
from sqlalchemy import func, ForeignKey
import enum
from sqlalchemy import func, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import relationship

class AgencyStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

agency_status_enum = PGEnum(AgencyStatus, name="agencystatus")


class Agency(db.Model):
    __tablename__ = 'agencies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address_id = db.Column(db.Integer)
    icon_url = db.Column(db.String)
    status = db.Column(agency_status_enum, default=AgencyStatus.PENDING)
    subscription_tier = db.Column(db.String(20), default='basic')  # basic, premium, enterprise
    monthly_qr_limit = db.Column(db.Integer, default=5)
    qr_codes = relationship('QRCode', backref='agency', lazy=True)
    products = relationship('Product', backref='agency', lazy=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    def get_used_qr_count_this_month(self):
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return QRCode.query.filter(
            QRCode.agency_id == self.id,
            QRCode.created_at >= start_of_month
        ).count()
    
    def can_create_qr(self):
        return self.get_used_qr_count_this_month() < self.monthly_qr_limit


