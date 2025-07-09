#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from flask_restful import Api
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

# ✅ GET /restaurants
@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([r.to_dict(only=('id', 'name', 'address')) for r in restaurants]), 200

# ✅ GET /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["GET"])
def show_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    return jsonify(restaurant.to_dict(rules=(
        'id',
        'name',
        'address',
        'restaurant_pizzas.id',
        'restaurant_pizzas.price',
        'restaurant_pizzas.pizza_id',
        'restaurant_pizzas.restaurant_id',
        'restaurant_pizzas.pizza.id',
        'restaurant_pizzas.pizza.name',
        'restaurant_pizzas.pizza.ingredients',
    ))), 200

# ✅ DELETE /restaurants/<int:id>
@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    db.session.delete(restaurant)
    db.session.commit()
    return jsonify({}), 204

# ✅ GET /pizzas
@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([p.to_dict(only=('id', 'name', 'ingredients')) for p in pizzas]), 200

# ✅ POST /restaurant_pizzas
@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    if not data:
        return jsonify({"errors": ["Missing JSON data"]}), 400

    price = data.get("price")
    pizza_id = data.get("pizza_id")
    restaurant_id = data.get("restaurant_id")

    if not all([price, pizza_id, restaurant_id]):
        return jsonify({"errors": ["Missing required fields"]}), 400

    try:
        new_rp = RestaurantPizza(
            price=data['price'],
            pizza_id=data['pizza_id'],
            restaurant_id=data['restaurant_id']
        )
        db.session.add(new_rp)
        db.session.commit()

        # Optional: Return the associated pizza details
        pizza = Pizza.query.get(data['pizza_id'])
        return jsonify({
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients,
            "price": new_rp.price
        }), 201

    except Exception as e:
        return jsonify({"errors": ["validation errors"]}), 400
    
    # ✅ POST /pizzas
@app.route("/pizzas", methods=["POST"])
def create_pizza():
    data = request.get_json()

    name = data.get("name")
    ingredients = data.get("ingredients")

    errors = {}

    if not name or not isinstance(name, str):
        errors["name"] = "Name is required and must be a string."

    if not ingredients or not isinstance(ingredients, str):
        errors["ingredients"] = "Ingredients are required and must be a string."

    if errors:
        return jsonify({"errors": errors}), 422

    try:
        new_pizza = Pizza(name=name, ingredients=ingredients)
        db.session.add(new_pizza)
        db.session.commit()
        return jsonify(new_pizza.to_dict(only=("id", "name", "ingredients"))), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 500


if __name__ == "__main__":
    app.run(port=5555, debug=True)
