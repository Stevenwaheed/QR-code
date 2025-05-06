from db.database import db
from sqlalchemy import func, ForeignKey


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, ForeignKey('users.id'))
    price = db.Column(db.Float)
    image_url = db.Column(db.String(200))
    is_visible = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, ForeignKey('categories.id'))
    agency_id = db.Column(db.Integer, ForeignKey('agencies.id'))
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    