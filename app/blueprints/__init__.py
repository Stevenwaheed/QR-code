from .auth.routes import auth_pg
from .address.routes import address_pg
from .agency.routes import agency_bp




def register_routes(app):
	app.register_blueprint(auth_pg, url_prefix='/api')
	app.register_blueprint(address_pg, url_prefix='/api')
	app.register_blueprint(agency_bp, url_prefix='/api')
	# app.register_blueprint(auth_pg, url_prefix='/api')
 
 