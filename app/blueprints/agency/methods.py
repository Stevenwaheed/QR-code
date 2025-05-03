
from app.blueprints.address.models import Address, City, Country, State
# from app.blueprints.product.methods import get_product_details
# from app.blueprints.qrcode.methods import get_qr_details


def get_agency_details(agency):
  address = Address.query.filter_by(id=agency.address_id).first()
  city = City.query.filter_by(id=address.city_id).first()
  state = State.query.filter_by(id=address.state_id).first()
  country = Country.query.filter_by(id=address.country_id).first()
  
  
  return {
      "id": agency.id,
        "name": agency.name,
        "icon": agency.icon_url,
        "is_subscribed": agency.subscription_tier,
        "monthly_qr_limit": agency.monthly_qr_limit,
        "address": {
          "city": {
            "id":city.id,
            "name":city.name,
          },
          "state": {
            "id":state.id,
            "name":state.name,
          },
          "country": {
            "id":country.id,
            "name":country.name,
          },
          "street_address":address.street_address
          },
        # "products":[
        #   {
        #     get_product_details(product)
        #   } for product in agency.products
        # ],
        # "qr_codes":[
        #   {
        #     get_qr_details(qr_code)
        #   } for qr_code in agency.qr_codes
        # ],
        "created_at": agency.created_at.isoformat(),
        "updated_at": agency.updated_at.isoformat(),
      }