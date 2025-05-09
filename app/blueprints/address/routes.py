import json
from app.blueprints.address.methods import seed_cities, seed_countries, seed_states
from flask import Blueprint, request, jsonify
from .models import Address, Country, State, City
from db.database import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)

address_pg = Blueprint("address", __name__)


@address_pg.route("/v1/address-seed", methods=["GET"])
def seed_address_data():
    seed_countries()
    seed_states()
    seed_cities()

    return "seeded successfully"


@address_pg.route("/v1/country", methods=["POST"])
def add_country():
    """
    Add a new country to the database.

    ---
    tags:
      - Country
    summary: Add a new country
    description: Endpoint to add a new country. The request should include the country's name and optionally the ISO code.
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            properties:
                name:
                    type: string
                    description: The name of the country.
                    example: France
                iso_code:
                    type: string
                    description: The ISO code of the country (optional).
                    example: FR
    responses:
      201:
        description: Country added successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Country added successfully
                country:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The unique ID of the country.
                      example: 1
                    name:
                      type: string
                      description: The name of the country.
                      example: France
                    iso_code:
                      type: string
                      description: The ISO code of the country.
                      example: FR
      400:
        description: Bad request, such as missing 'name' field or database integrity issues.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Country name is required
      409:
        description: Conflict error, such as when the country already exists.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Country already exists
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
    """
    data = request.json
    if "name" not in data:
        return {"message": "Country name is required"}, 400

    try:
        # Check if country already exists
        existing_country = Country.query.filter_by(name=data["name"]).first()
        if existing_country:
            return {"message": "Country already exists"}, 409

        # Create new country
        new_country = Country(name=data["name"], iso_code=data.get("iso_code"))

        db.session.add(new_country)
        db.session.commit()

        return (
            jsonify(
                {
                    "id": new_country.id,
                    "name": new_country.name,
                    "iso_code": new_country.iso_code,
                    # "created_at": new_country.created_at,
                    # "updated_at": new_country.updated_at,
                }
            ),
            201,
        )

    except IntegrityError:
        db.session.rollback()
        return {
            "message": "Failed to add country due to a database integrity error"
        }, 400
    except Exception as e:
        db.session.rollback()
        return {"message": f"An error occurred: {str(e)}"}, 500


@address_pg.route("/v1/country", methods=["GET"])
def list_countries():
    """
    List all countries
    ---
    tags:
      - country
    summary: List all countries
    description: Returns a list of all countries in the database
    operationId: listCountries
    responses:
      200:
        description: Successful operation
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: Unique identifier for the country
              name:
                type: string
                description: Country name
              iso_code:
                type: string
                description: ISO code for the country
      500:
        description: Server error
        schema:
          type: object
          properties:
            message:
              type: string
              description: Error message
    """
    countries = Country.query.all()

    try:
        return (
            jsonify(
                [
                    {
                        "id": country.id,
                        "name": country.name,
                        "iso_code": country.iso_code,
                        # "created_at": country.created_at,
                        # "updated_at": country.updated_at,
                    }
                    for country in countries
                ]
            ),
            200,
        )
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500


@address_pg.route("/v1/country/<int:country_id>", methods=["GET"])
def get_country_details(country_id):
    """
    Get country details by ID.

    ---
    tags:
      - Country
    summary: Retrieve country details
    description: Fetches detailed information about a country, including its states, by the country ID.
    security:
      - BearerAuth: []
    parameters:
      - name: country_id
        in: path
        required: true
        description: The ID of the country to retrieve.
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: Country details retrieved successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                country:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The unique ID of the country.
                      example: 1
                    name:
                      type: string
                      description: The name of the country.
                      example: France
                    iso_code:
                      type: string
                      description: The ISO code of the country.
                      example: FR
                    state:
                      type: array
                      description: List of states belonging to the country.
                      items:
                        type: object
                        properties:
                          id:
                            type: integer
                            description: The unique ID of the state.
                            example: 101
                          name:
                            type: string
                            description: The name of the state.
                            example: Île-de-France
      404:
        description: Country not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: country not found
      401:
        description: Unauthorized, JWT token is missing or invalid.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Missing Authorization Header
    """
    country = Country.query.filter_by(id=country_id).first()
    if country is None:
        return {"message": "country not found"}, 404
    return (
        jsonify(
            {
                "id": country.id,
                "name": country.name,
                "iso_code": country.iso_code,
                # "created_at": country.created_at,
                # "updated_at": country.updated_at,
                "state": [
                    {"id": state.id, "name": state.name} for state in country.states
                ],
            }
        ),
        200,
    )


@address_pg.route("/v1/country/<int:country_id>", methods=["PATCH"])
def update_country(country_id):
  """
  Update a country by ID
  ---
  tags:
    - country
  summary: Update an existing country
  description: Update a country's name and/or ISO code by ID
  operationId: updateCountry
  parameters:
    - name: country_id
      in: path
      description: ID of the country to update
      required: true
      type: integer
      format: int64
    - name: body
      in: body
      description: Country object with updated fields
      required: true
      schema:
        type: object
        properties:
          name:
            type: string
            description: Updated country name
          iso_code:
            type: string
            description: Updated ISO code
  responses:
    200:
      description: Successfully updated country
      schema:
        type: object
        properties:
          id:
            type: integer
            description: Country ID
          name:
            type: string
            description: Country name
          iso_code:
            type: string
            description: ISO code for the country
    400:
      description: Bad request - No data provided or database integrity error
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    404:
      description: Country not found
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    409:
      description: Conflict - Country name already exists
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
  data = request.json

  if not data:
      return {"message": "No update data provided"}, 400

  country = Country.query.filter_by(id=country_id).first()
  if country is None:
      return {"message": "country not found"}, 404

  try:
      # Update name if provided
      if "name" in data:
          # Check if new name already exists
          existing_country = Country.query.filter(
              Country.name == data["name"], Country.id != country_id
          ).first()

          if existing_country:
              return {"message": "Country name already exists"}, 409

          country.name = data["name"]

      # Update iso_code if provided
      if "iso_code" in data:
          country.iso_code = data["iso_code"]

      db.session.commit()

      return (
          jsonify(
              {
                  "id": country.id,
                  "name": country.name,
                  "iso_code": country.iso_code,
                  # "created_at": country.created_at,
                  # "updated_at": country.updated_at,
              }
          ),
          200,
      )

  except IntegrityError:
      db.session.rollback()
      return {
          "message": "Failed to update country due to a database integrity error"
      }, 400
  except Exception as e:
      db.session.rollback()
      return {"message": f"An error occurred: {str(e)}"}, 500


@address_pg.route("/v1/state", methods=["POST"])
def add_state():
    """
    Add a new state.

    ---
    tags:
      - State
    summary: Add a new state to a country
    description: Adds a new state to the specified country. The state must have a unique name within that country.
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            required:
              - name
              - country_id
            properties:
              name:
                type: string
                description: The name of the state.
                example: California
              country_id:
                type: integer
                description: The ID of the country to which the state belongs.
                example: 1
    responses:
      201:
        description: State added successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Success message.
                  example: "State added successfully"
                state:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The unique ID of the state.
                      example: 101
                    name:
                      type: string
                      description: The name of the state.
                      example: "California"
                    country_id:
                      type: integer
                      description: The ID of the country the state belongs to.
                      example: 1
      400:
        description: Invalid request due to missing fields or database integrity issues.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Name and country_id are required
      404:
        description: The specified country was not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Invalid country_id"
      409:
        description: The state already exists in the specified country.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "State already exists in this country"
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "An error occurred"
    """
    data = request.json

    # Validate required fields
    if not all(key in data for key in ["name", "country_id"]):
        return {"message": "Name and country_id are required"}, 400

    try:
        # Verify country exists
        country = Country.query.filter_by(id=data["country_id"]).first()
        if not country:
            return {"message": "Invalid country_id"}, 404

        # Check if state already exists in this country
        existing_state = State.query.filter_by(
            name=data["name"], country_id=data["country_id"]
        ).first()

        if existing_state:
            return {"message": "State already exists in this country"}, 409

        # Create new state
        new_state = State(name=data["name"], country_id=data["country_id"])

        db.session.add(new_state)
        db.session.commit()

        return (
            jsonify(
                {
                    "id": new_state.id,
                    "name": new_state.name,
                    "country_id": new_state.country_id,
                    # "created_at": new_state.created_at,
                    # "updated_at": new_state.updated_at,
                }
            ),
            201,
        )

    except IntegrityError:
        db.session.rollback()
        return {"message": "Failed to add state due to a database integrity error"}, 400
    except Exception as e:
        db.session.rollback()
        return {"message": f"An error occurred: {str(e)}"}, 500


@address_pg.route("/v1/state/country/<int:country_id>", methods=["GET"])
def list_states(country_id):
    """
    Get a list of states in a specific country.

    ---
    tags:
      - State
    summary: Retrieve a list of states for a specific country
    description: Fetches all states for the given `country_id`, including the state's ID, name, and associated country information.
    parameters:
      - name: country_id
        in: path
        required: true
        description: The ID of the country for which the states are being retrieved.
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: List of states for the specified country retrieved successfully.
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: The unique ID of the state.
                    example: 101
                  name:
                    type: string
                    description: The name of the state.
                    example: "California"
                  country:
                    type: object
                    properties:
                      id:
                        type: integer
                        description: The unique ID of the country.
                        example: 1
                      name:
                        type: string
                        description: The name of the country.
                        example: "United States"
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "An error occurred: <details>"
    """
    states = State.query.filter_by(country_id=country_id).all()

    try:
        return (
            jsonify(
                [
                    {
                        "id": state.id,
                        "name": state.name,
                        "country": {
                            "id": state.country_id,
                            "name": state.country.name,
                            # "created_at": state.country.created_at,
                            # "updated_at": state.country.updated_at,
                        },
                        # "created_at": state.created_at,
                        # "updated_at": state.updated_at,
                    }
                    for state in states
                ]
            ),
            200,
        )
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500


@address_pg.route("/v1/state/<int:state_id>", methods=["GET"])
def get_state_details(state_id):
    """
    Get state details by ID.

    ---
    tags:
      - State
    summary: Retrieve state details
    description: Fetches detailed information about a state, including its associated country and cities, by the state ID.
    parameters:
      - name: state_id
        in: path
        required: true
        description: The ID of the state to retrieve.
        schema:
          type: integer
          example: 101
    responses:
      200:
        description: State details retrieved successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                state:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The unique ID of the state.
                      example: 101
                    name:
                      type: string
                      description: The name of the state.
                      example: California
                    country:
                      type: object
                      description: Details of the country to which the state belongs.
                      properties:
                        id:
                          type: integer
                          description: The unique ID of the country.
                          example: 1
                        name:
                          type: string
                          description: The name of the country.
                          example: USA
                    city:
                      type: array
                      description: List of cities belonging to the state.
                      items:
                        type: object
                        properties:
                          id:
                            type: integer
                            description: The unique ID of the city.
                            example: 201
                          name:
                            type: string
                            description: The name of the city.
                            example: Los Angeles
                          postal_code_prefix:
                            type: string
                            description: The postal code prefix of the city.
                            example: 900
      404:
        description: State not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: state not found
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
    """
    state = State.query.filter_by(id=state_id).first()
    if state is None:
        return {"message": "state not found"}, 404
    return (
        jsonify(
            {
                "id": state.id,
                "name": state.name,
                "country": {
                    "id": state.country_id,
                    "name": state.country.name,
                    # "created_at": state.country.created_at,
                    # "updated_at": state.country.updated_at,
                },
                # "created_at": state.created_at,
                # "updated_at": state.updated_at,
                "city": [
                    {
                        "id": city.id,
                        "name": city.name,
                        "postal_code_prefix": city.postal_code_prefix,
                        # "created_at": city.created_at,
                        # "updated_at": city.updated_at,
                    }
                    for city in state.cities
                ],
            }
        ),
        200,
    )


@address_pg.route("/v1/state/<int:state_id>", methods=["PATCH"])
def update_state(state_id):
  """
  Update a state by ID
  ---
  tags:
    - state
  summary: Update an existing state
  description: Update a state's name and/or country by ID
  operationId: updateState
  parameters:
    - name: state_id
      in: path
      description: ID of the state to update
      required: true
      type: integer
      format: int64
    - name: body
      in: body
      description: State object with updated fields
      required: true
      schema:
        type: object
        properties:
          name:
            type: string
            description: Updated state name
          country_id:
            type: integer
            description: ID of the country this state belongs to
  responses:
    200:
      description: Successfully updated state
      schema:
        type: object
        properties:
          id:
            type: integer
            description: State ID
          name:
            type: string
            description: State name
    400:
      description: Bad request - No data provided or database integrity error
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    404:
      description: State not found or invalid country_id
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    409:
      description: Conflict - State name already exists in this country
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
  data = request.json

  if not data:
      return {"message": "No update data provided"}, 400

  state = State.query.filter_by(id=state_id).first()
  if state is None:
      return {"message": "state not found"}, 404

  try:
      # Update name if provided
      if "name" in data:
          # Check if new name already exists in the same country
          existing_state = State.query.filter(
              State.name == data["name"],
              State.country_id == state.country_id,
              State.id != state_id,
          ).first()

          if existing_state:
              return {"message": "State name already exists in this country"}, 409

          state.name = data["name"]

      # Update country_id if provided
      if "country_id" in data:
          # Verify new country exists
          country = Country.query.get(data["country_id"])
          if not country:
              return {"message": "Invalid country_id"}, 404

          state.country_id = data["country_id"]

      db.session.commit()

      return (
          jsonify(
              {
                  "id": state.id,
                  "name": state.name,
                  # "created_at": state.created_at,
                  # "updated_at": state.updated_at,
              }
          ),
          200,
      )

  except IntegrityError:
      db.session.rollback()
      return {
          "message": "Failed to update state due to a database integrity error"
      }, 400
  except Exception as e:
      db.session.rollback()
      return {"message": f"An error occurred: {str(e)}"}, 500


@address_pg.route("/v1/city", methods=["POST"])
def add_city():
    """
    Add a new city to a state.

    ---
    tags:
      - City
    summary: Add a new city
    description: Endpoint to add a new city to a specific state. The request must include the city's name and the state ID.
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            required:
              - name
              - state_id
            properties:
              name:
                type: string
                description: The name of the city.
                example: Los Angeles
              state_id:
                type: integer
                description: The ID of the state to which the city belongs.
                example: 101
              postal_code_prefix:
                type: string
                description: The postal code prefix of the city (optional).
                example: 900
    responses:
      201:
        description: City added successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: City added successfully
                city:
                  type: object
                  properties:
                    id:
                      type: integer
                      description: The unique ID of the city.
                      example: 201
                    name:
                      type: string
                      description: The name of the city.
                      example: Los Angeles
                    postal_code_prefix:
                      type: string
                      description: The postal code prefix of the city.
                      example: 900
      400:
        description: Bad request, such as missing required fields or a database integrity error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Name and state_id are required
      404:
        description: Invalid state ID.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: Invalid state_id
      409:
        description: Conflict error, such as when the city already exists in the specified state.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: City already exists in this state
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
    """
    data = request.json

    # Validate required fields
    if not all(key in data for key in ["name", "state_id"]):
        return {"message": "Name and state_id are required"}, 400

    try:
      # Verify state exists
      state = State.query.get(data["state_id"])
      if not state:
          return {"message": "Invalid state_id"}, 404

      # Check if city already exists in this state
      existing_city = City.query.filter_by(
          name=data["name"], state_id=data["state_id"]
      ).first()

      if existing_city:
          return {"message": "City already exists in this state"}, 409

      # Create new city
      new_city = City(
          name=data["name"],
          state_id=data["state_id"],
          postal_code_prefix=data.get("postal_code_prefix"),
      )

      db.session.add(new_city)
      db.session.commit()

      return (
          jsonify(
              {
                  "id": new_city.id,
                  "name": new_city.name,
                  "postal_code_prefix": new_city.postal_code_prefix,
                  "created_at": new_city.created_at,
                  "updated_at": new_city.updated_at,
              }
          ),
          201,
      )

    except IntegrityError:
        db.session.rollback()
        return {"message": "Failed to add city due to a database integrity error"}, 400
    except Exception as e:
        db.session.rollback()
        return {"message": f"An error occurred: {str(e)}"}, 500


@address_pg.route("/v1/city/state/<int:state_id>", methods=["GET"])
def list_cities(state_id):
    """
    List all cities for a specific state.

    ---
    tags:
      - City
    summary: Get list of cities by state
    description: Fetches a list of all cities belonging to a specified state, identified by its ID.
    parameters:
      - name: state_id
        in: path
        required: true
        description: The ID of the state for which to list cities.
        schema:
          type: integer
          example: 101
    responses:
      200:
        description: List of cities retrieved successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                city:
                  type: array
                  description: List of cities for the specified state.
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        description: The unique ID of the city.
                        example: 201
                      name:
                        type: string
                        description: The name of the city.
                        example: Los Angeles
                      state:
                        type: object
                        description: Details of the state to which the city belongs.
                        properties:
                          id:
                            type: integer
                            description: The unique ID of the state.
                            example: 101
                          name:
                            type: string
                            description: The name of the state.
                            example: California
                      country:
                        type: object
                        description: Details of the country to which the state belongs.
                        properties:
                          id:
                            type: integer
                            description: The unique ID of the country.
                            example: 1
                          name:
                            type: string
                            description: The name of the country.
                            example: USA
                      postal_code_prefix:
                        type: string
                        description: The postal code prefix of the city.
                        example: 900
      404:
        description: State not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: State not found
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string

    """
    cities = City.query.filter_by(state_id=state_id).all()

    return (
        jsonify(
            [
                {
                    "id": city.id,
                    "name": city.name,
                    # "created_at": city.created_at,
                    # "updated_at": city.updated_at,
                    "state": {
                        "id": city.state_id,
                        "name": city.state.name,
                        # "created_at": city.state.created_at,
                        # "updated_at": city.state.updated_at,
                    },
                    "country": {
                        "id": city.state.country_id,
                        "name": city.state.country.name,
                        # "created_at": city.state.country.created_at,
                        # "updated_at": city.state.country.updated_at,
                    },
                    "postal_code_prefix": city.postal_code_prefix,
                }
                for city in cities
            ]
        ),
        200,
    )


@address_pg.route("/v1/city/<int:city_id>", methods=["GET"])
def get_city_details(city_id):
    """
    Get details of a specific city.

    ---
    tags:
      - City
    summary: Retrieve city details
    description: Fetches detailed information about a city, including its state and country, by the city ID.
    parameters:
      - name: city_id
        in: path
        required: true
        description: The ID of the city to retrieve.
        schema:
          type: integer
          example: 201
    responses:
      200:
        description: City details retrieved successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                city:
                  type: object
                  description: Detailed information about the city.
                  properties:
                    id:
                      type: integer
                      description: The unique ID of the city.
                      example: 201
                    name:
                      type: string
                      description: The name of the city.
                      example: Los Angeles
                    state:
                      type: object
                      description: Details of the state to which the city belongs.
                      properties:
                        id:
                          type: integer
                          description: The unique ID of the state.
                          example: 101
                        name:
                          type: string
                          description: The name of the state.
                          example: California
                    country:
                      type: object
                      description: Details of the country to which the state belongs.
                      properties:
                        id:
                          type: integer
                          description: The unique ID of the country.
                          example: 1
                        name:
                          type: string
                          description: The name of the country.
                          example: USA
                    postal_code_prefix:
                      type: string
                      description: The postal code prefix of the city.
                      example: 900
      404:
        description: City not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: city not found
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
    """
    city = City.query.filter_by(id=city_id).first()
    if city is None:
        return {"message": "city not found"}, 404
    return (
        jsonify(
            {
                "id": city.id,
                "name": city.name,
                "state": {
                    "id": city.state_id,
                    "name": city.state.name,
                    # "created_at": city.state.created_at,
                    # "updated_at": city.state.updated_at,
                },
                "country": {
                    "id": city.state.country_id,
                    "name": city.state.country.name,
                    # "created_at": city.state.country.created_at,
                    # "updated_at": city.state.country.updated_at,
                },
                "postal_code_prefix": city.postal_code_prefix,
                # "created_at": city.created_at,
                # "updated_at": city.updated_at,
            }
        ),
        200,
    )


@address_pg.route("/v1/city/<int:city_id>", methods=["PATCH"])
def update_city(city_id):
  """
  Update a city by ID
  ---
  tags:
    - city
  summary: Update an existing city
  description: Update a city's name, state, and/or postal code prefix by ID
  operationId: updateCity
  parameters:
    - name: city_id
      in: path
      description: ID of the city to update
      required: true
      type: integer
      format: int64
    - name: body
      in: body
      description: City object with updated fields
      required: true
      schema:
        type: object
        properties:
          name:
            type: string
            description: Updated city name
          state_id:
            type: integer
            description: ID of the state this city belongs to
          postal_code_prefix:
            type: string
            description: Updated postal code prefix for the city
  responses:
    200:
      description: Successfully updated city
      schema:
        type: object
        properties:
          id:
            type: integer
            description: City ID
          name:
            type: string
            description: City name
          postal_code_prefix:
            type: string
            description: Postal code prefix for the city
    400:
      description: Bad request - No data provided or database integrity error
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    404:
      description: City not found or invalid state_id
      schema:
        type: object
        properties:
          message:
            type: string
            description: Error message
    409:
      description: Conflict - City name already exists in this state
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
  data = request.json

  if not data:
      return {"message": "No update data provided"}, 400

  city = City.query.filter_by(id=city_id).first()
  if city is None:
      return {"message": "city not found"}, 404

  try:
      # Update name if provided
      if "name" in data:
          # Check if new name already exists in the same state
          existing_city = City.query.filter(
              City.name == data["name"],
              City.state_id == city.state_id,
              City.id != city_id,
          ).first()

          if existing_city:
              return {"message": "City name already exists in this state"}, 409

          city.name = data["name"]

      # Update state_id if provided
      if "state_id" in data:
          # Verify new state exists
          state = State.query.get(data["state_id"])
          if not state:
              return {"message": "Invalid state_id"}, 404

          city.state_id = data["state_id"]

      # Update postal_code_prefix if provided
      if "postal_code_prefix" in data:
          city.postal_code_prefix = data["postal_code_prefix"]

      db.session.commit()

      return (
          jsonify(
              {
                  "id": city.id,
                  "name": city.name,
                  "postal_code_prefix": city.postal_code_prefix,
                  # "created_at": city.created_at,
                  # "updated_at": city.updated_at,
              }
          ),
          200,
      )

  except IntegrityError:
      db.session.rollback()
      return {
          "message": "Failed to update city due to a database integrity error"
      }, 400
  except Exception as e:
      db.session.rollback()
      return {"message": f"An error occurred: {str(e)}"}, 500




@address_pg.route('/v1/address', methods=['POST'])
@jwt_required()
def create_address():
    """
    Create a new address
    ---
    tags:
      - Address
    security:
      - bearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            properties:
              street_address:
                type: string
                description: Street address of the user
              city_id:
                type: integer
                description: ID of the city
              state_id:
                type: integer
                description: ID of the state
              country_id:
                type: integer
                description: ID of the country
              postal_code:
                type: string
                description: Postal code (optional)
              lat:
                type: number
                description: Latitude (optional)
              lan:
                type: number
                description: Longitude (optional)
              is_primary:
                type: boolean
                description: Whether the address is primary (default is false)
    responses:
      201:
        description: Address created successfully
      400:
        description: Invalid input
      500:
        description: Internal server error
    """
    payload = get_jwt_identity()
    payload = json.loads(payload)
    data = request.json
    
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    
    required_fields = [
      'street_address',
      'city_id',
      'state_id',
      'country_id',
    ]
    
    for field in required_fields:
      if field not in data:
        return {"message": f"{field} is required"}, 400
    
    try:
      postal_code = data['postal_code']
    except Exception as e:
      postal_code = None
    
    try:
      lat = data['lat']
      lan = data['lan']
    except Exception as e:
      lan = lat = None
    
      
    try:
      city = City.query.filter_by(id=data['city_id']).first()
      country = Country.query.filter_by(id=data['country_id']).first()
      state = State.query.filter_by(id=data['state_id']).first()
      new_address = Address(
          user_id=payload['user_id'],
          lat=lat,
          lan=lan,
          street_address=data['street_address'],
          city_id=data['city_id'],
          state_id=data['state_id'],
          country_id=data['country_id'],
          postal_code=postal_code,
          is_primary=data.get('is_primary', False)
      )
      
      db.session.add(new_address)
      db.session.commit()
      
      return jsonify({"message": "Address created successfully"
                      , "address":{
                          "id": new_address.id,
                          "city": {
                            "id": city.id,
                            "name": city.name,
                          },
                          "state": {
                            "id": state.id,
                            "name": state.name,
                          },
                          "country": {
                            "id": country.id,
                            "name": country.name,
                          },
                          "lat": new_address.lat,
                          "lan": new_address.lan,
                          "street_address": new_address.street_address,
                          "is_primary":new_address.is_primary
                          }
                      }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
      
      
      





@address_pg.route('/v1/address', methods=['GET'])
@jwt_required()
def get_address():
  """
    Get all addresses for the logged-in user.
    ---
    tags:
    - Address
    security:
      - bearerAuth: []
    summary: Get Addresses
    description: Retrieves a list of addresses associated with the authenticated user.
    responses:
      200:
        description: A list of addresses.
        content:
          application/json:
            schema:
              type: object
              properties:
                address:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        description: The address ID.
                      city:
                        type: object
                        properties:
                          id:
                            type: integer
                            description: The city ID.
                          name:
                            type: string
                            description: The city name.
                      state:
                        type: object
                        properties:
                          id:
                            type: integer
                            description: The state ID.
                          name:
                            type: string
                            description: The state name.
                      country:
                        type: object
                        properties:
                          id:
                            type: integer
                            description: The country ID.
                          name:
                            type: string
                            description: The country name.
                      lat:
                        type: number
                        format: float
                        description: The latitude of the address.
                      lan:
                        type: number
                        format: float
                        description: The longitude of the address.
                      street_address:
                        type: string
                        description: The street address.
      401:
        description: Unauthorized - Missing or invalid JWT.
  """
  payload = get_jwt_identity()
  payload = json.loads(payload)
  addresses = Address.query.filter_by(user_id=payload['user_id']).all()
  
  addresses_list = []
  for address in addresses:
    city = City.query.filter_by(id=address.city_id).first()
    country = Country.query.filter_by(id=address.country_id).first()
    state = State.query.filter_by(id=address.state_id).first()
    
    addresses_list.append(
      {
        "id": address.id,
        "city": {
          "id": city.id,
          "name": city.name,
        },
        "state": {
          "id": state.id,
          "name": state.name,
        },
        "country": {
          "id": country.id,
          "name": country.name,
        },
        "lat": address.lat,
        "lan": address.lan,
        "street_address": address.street_address,
        "is_primary":address.is_primary
      }
    )
    
  return {"address":addresses_list}, 200



