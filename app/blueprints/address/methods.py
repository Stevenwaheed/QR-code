from app.blueprints.address.models import Address, City, Country, State
from db.database import db


def seed_countries():
    countries_data = [
        {"name": "United States", "iso_code": "US"},
        {"name": "Canada", "iso_code": "CA"},
        {"name": "India", "iso_code": "IN"},
    ]
    for country_data in countries_data:
        country = Country.query.filter_by(name=country_data["name"]).first()
        if not country:
            country = Country(**country_data)
            db.session.add(country)
    db.session.commit()
    print("Countries seeded successfully.")


def seed_states():
    states_data = [
        # States for United States
        {"name": "California", "country_name": "United States"},
        {"name": "Texas", "country_name": "United States"},
        # States for Canada
        {"name": "Ontario", "country_name": "Canada"},
        {"name": "Quebec", "country_name": "Canada"},
        # States for India
        {"name": "Maharashtra", "country_name": "India"},
        {"name": "Karnataka", "country_name": "India"},
    ]
    for state_data in states_data:
        country = Country.query.filter_by(name=state_data["country_name"]).first()
        if country:
            state = State.query.filter_by(
                name=state_data["name"], country_id=country.id
            ).first()
            if not state:
                state = State(name=state_data["name"], country_id=country.id)
                db.session.add(state)
    db.session.commit()
    print("States seeded successfully.")


def seed_cities():
    cities_data = [
        # Cities for California
        {
            "name": "Los Angeles",
            "state_name": "California",
            "postal_code_prefix": "900",
        },
        {
            "name": "San Francisco",
            "state_name": "California",
            "postal_code_prefix": "941",
        },
        # Cities for Ontario
        {"name": "Toronto", "state_name": "Ontario", "postal_code_prefix": "M5"},
        {"name": "Ottawa", "state_name": "Ontario", "postal_code_prefix": "K1"},
        # Cities for Maharashtra
        {"name": "Mumbai", "state_name": "Maharashtra", "postal_code_prefix": "400"},
        {"name": "Pune", "state_name": "Maharashtra", "postal_code_prefix": "411"},
    ]
    for city_data in cities_data:
        state = State.query.filter_by(name=city_data["state_name"]).first()
        if state:
            city = City.query.filter_by(
                name=city_data["name"], state_id=state.id
            ).first()
            if not city:
                city = City(
                    name=city_data["name"],
                    state_id=state.id,
                    postal_code_prefix=city_data["postal_code_prefix"],
                )
                db.session.add(city)
    db.session.commit()
    print("Cities seeded successfully.")





def get_address_details(user_id, is_primary=False):
    addresses = Address.query.filter_by(user_id=user_id, is_primary=is_primary).all()
    addresses_list = []
    for address in addresses:
        
        country = Country.query.filter_by(id=address.country_id).first()
        if country is None:
            return {"message": "country not found"}, 404

        city = City.query.filter_by(id=address.city_id).first()
        if city is None:
            return {"message": "city not found"}, 404

        state = State.query.filter_by(id=address.state_id).first()
        if state is None:
            return {"message": "state not found"}, 404
        
        
        
        addresses_list.append(
            {
                "id": city.id,
                "name": city.name,
                "state": {
                    "id": city.state_id,
                    "name": city.state.name,
                },
                "country": {
                    "id": city.state.country_id,
                    "name": city.state.country.name,
                },
                "street_address":address.street_address,
                "postal_code_prefix": city.postal_code_prefix,
                "lat": address.lat,
                "lan": address.lan,
                "is_primary":address.is_primary
            }
        )
        
        
    return addresses_list
        
        
        
    
    
    