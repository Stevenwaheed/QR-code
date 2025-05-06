
from datetime import datetime, timedelta
from app.blueprints.product.models import Product
from config.config import Config
from db.database import db
from sqlalchemy import func, ForeignKey
import qrcode
import json
import os
import uuid
from io import BytesIO
import base64


def default_expire_at():
        return datetime.utcnow() + timedelta(days=30)

class QRCode(db.Model):
    __tablename__ = 'qr_code'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    content = db.Column(db.String)
    agency_id = db.Column(db.Integer, ForeignKey('agencies.id'))
    qrcode_url = db.Column(db.String(200))
    expire_at = db.Column(db.DateTime, default=default_expire_at)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    
    def is_expired(self):
        if not self.expire_at:
            return False
        return datetime.now() > self.expire_at
    
    
    
    def get_products(self):
        if not self.content:
            return []
        try:
            product_ids = json.loads(self.content).get('product_ids', [])
            return Product.query.filter(Product.id.in_(product_ids)).all()
        except:
            return []
    
    def generate_qr_code(self):
        """Generate QR code and save to file system"""
        if not self.content:
            return False
            
        # Create unique filename
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        # Generate QR code with some metadata
        qr_data = {
            'id': self.id,
            'content': json.loads(self.content) if self.content else {},
            'expires': self.expire_at.isoformat() if self.expire_at else None
        }
        
        # Generate the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the image
        img.save(filepath)
        
        # Update the URL
        self.qrcode_url = f"/static/qrcodes/{filename}"
        db.session.commit()
        
        return True



