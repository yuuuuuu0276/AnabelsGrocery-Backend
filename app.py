import json

from db import db
from flask import Flask, request
from db import Inventory
from db import Category
from db import Menu
from db import Order
from db import Orderitem
from db import Asset

import os
import datetime

# define db filename
db_filename = "todo.db"
app = Flask(__name__) #instiation of an instance of flask

# setup config
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_filename}" #specify the variations we are using
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  #has event listener feature to track the files modified
app.config["SQLALCHEMY_ECHO"] = True  #what to know what our python code would translate to sql code

# initialize app
db.init_app(app)
with app.app_context():
    db.create_all() # create all our tables


# generalized response formats
def success_response(data, code=200):
    return json.dumps(data), code


def failure_response(message, code=404):
    return json.dumps({"error": message}), code


# -- TASK ROUTES ------------------------------------------------------

@app.route("/")
def greet_user():
    return "Hello" + os.environ.get("NAME")


@app.route("/inventories/")
def get_inventories():
    """
    Endpoint for getting all inventories
    """
    inventories = []
    for inventory in Inventory.query.all():  
        inventories.append(inventory.serialize_for_render()) 

    return success_response({"inventories": inventories})


@app.route("/test/inventories/")
def test_get_inventories():
    """
    Endpoint for getting all inventories
    """
    inventories = []
    for inventory in Inventory.query.all():  
        inventories.append(inventory.serialize_all()) 

    return success_response({"inventories": inventories})


@app.route("/inventories/", methods=["POST"])
def create_inventory():
    """
    Endpoint for creating a new task
    """
    body = json.loads(request.data)  
    new_inventory= Inventory(
        image = body.get("image"),
        name = body.get("name"),
        description = body.get("description"),
        price = body.get("price")     
    )

    db.session.add(new_inventory)
    db.session.commit()
    return success_response(new_inventory.serialize_for_render(), 201)


@app.route("/inventories/<int:inventory_id>/")
def get_inventory_by_id(inventory_id):
    """
    Endpoint for getting an inventory by id
    """
    inventory = Inventory.query.filter_by(id = inventory_id).first()
    if inventory is None:
        return failure_response(f"Task not found {inventory_id}!")
    return success_response(inventory.serialize_for_render())


# -- CATEGORY ROUTES---------------------------------------------------

@app.route("/inventories/<int:inventory_id>/category/", methods=["POST"])
def assign_category(inventory_id):
    """
    Endpoint for assigning a category
    to an inventory by id
    """
    inventory = Inventory.query.filter_by(id = inventory_id).first()
    if inventory is None:
        return failure_response("Inventory not found!")
    
    body = json.loads(request.data)
    name = body.get("name")
    description = body.get("description")

    category = Category.query.filter_by(name = name).first()
    if category is None:
        category = Category(name = name, description= description)
    inventory.categories.append(category)
    db.session.commit()
    return success_response(category.serialize())


@app.route("/categories/", methods=["GET"])
def get_all_categories():
    """
    Endpoint for getting all inventories
    """
    categories = []
    for category in Category.query.all(): 
        categories.append(category.serialize()) 
    return success_response({"categories": categories})


@app.route("/categories/<int:category_id>/", methods=["GET"])
def get_category(category_id):
    """
    Endpoint for getting a category by id
    """
    category = Category.query.filter_by(id = category_id).first()
    if category is None:
        return failure_response("Category not found!")
    return success_response(category.serialize())


@app.route("/categories/m/", methods=["GET"])
def get_categories():
    """
    Endpoint for getting multiple categories by ids
    """
    length :int = len(request.args)
    print(length)
    category_id_list =[]
    for i in range(length):
        category_id_list.append(request.args[f"c{i}"])

    response = []
    for category_id in category_id_list:
      category = Category.query.filter_by(id = category_id).first()
      if category is None:
        return failure_response("Category not found!")
      response.append(category.serialize())
      
    return success_response({"categories": response })

# -- MENU ROUTES---------------------------------------------------

@app.route("/menus/", methods=["GET"])
def get_menus():
    """
    Endpoint for getting all menus
    """
    menus = []
    for menu in Menu.query.all(): 
        menus.append(menu.serialize()) 
    return success_response({"menus": menus})


@app.route("/menus/", methods=["POST"])
def create_menu():
    """
    Endpoint for creating a new menu
    """
    body = json.loads(request.data)  

    image_data = body.get("image_data")
    if image_data is None:
        return failure_response("Not Base64 URL")
    
    image = Asset(image_data=image_data)
    db.session.add(image)
    db.session.commit()
    
    new_menu= Menu(
        name = body.get("name"),
        description = body.get("description"), 
        instruction = body.get("instruction"),
        image_id = image.id
    )

    db.session.add(new_menu)
    db.session.commit()
    return success_response(new_menu.serialize(), 201)


@app.route("/menus/<int:menu_id>/")
def get_menu_by_id(menu_id):
    """
    Endpoint for getting a menu by id
    """
    menu = Menu.query.filter_by(id = menu_id).first()
    if menu is None:
        return failure_response(f"Menu not found {menu_id}!")
    return success_response(menu.serialize())


@app.route("/menus/<int:menu_id>/", methods=["DELETE"])
def delete_menu(menu_id):
    """
    Endpoint for delting a menu
    """
    menu = Menu.query.filter_by(id = menu_id).first()
    if menu is None:
        return failure_response("menu not found!")
    db.session.delete(menu)
    db.session.commit()
    return success_response(menu.serialize())


# -- ORDER ROUTES---------------------------------------------------

@app.route("/orders/", methods=["GET"])
def get_orders():
    """
    Endpoint for getting all orders
    """
    orders = []
    for order in Order.query.all(): 
        orders.append(order.simple_serialize()) 
    return success_response({"orders": orders})

# @app.route("/orders/", methods=["POST"])
# def create_order():
#     """
#     Endpoint for creating a new order
#     """
#     body = json.loads(request.data)  
#     new_order= Order(
#         total_price = body.get("total_price", 0),     
#         valid = body.get("total_price", False)
#     )

#     new_order = Order()

#     db.session.add(new_order)
#     db.session.commit()

#     #inventory.type = json
#     inventory_list = body.get("inventories")

#     try:
#       for inventory in inventory_list:
#         print(new_order.id)
#         simlpe_create_orderitem(new_order.id, inventory) 
#     except Exception as e:
#         return failure_response(f"{e}")

#     db.session.commit()

#     return success_response(new_order.serialize(), 201)


@app.route("/orders/", methods=["POST"])
def create_order():
    """
    Endpoint for creating a new order
    """
    body = json.loads(request.data)  
    new_order= Order(
        total_price = body.get("total_price", 0),     
        valid = body.get("total_price", False)
    )

    new_order = Order()

    db.session.add(new_order)
    db.session.commit()

    #inventory.type = json
    inventory_list = body.get("inventories")

    try:
      for inventory in inventory_list:
        simlpe_create_orderitem(new_order.id, inventory) 
    except Exception as e:
        return failure_response(f"{e}")

    db.session.commit()

    new_order.time_created = datetime.datetime.now()
    # if the order is created after 19 
    if new_order.time_created.hour > 19:
      pick_up_time = new_order.time_created + datetime.timedelta(days = 1)
      pick_up_time = pick_up_time.replace(hour =  18, minute= 59, second= 59)
    else:
      pick_up_time = new_order.time_created + datetime.timedelta(hours = 2)
      if  pick_up_time.hour > 19:
        pick_up_time = pick_up_time.replace(hour =  18, minute= 59, second= 59)

    new_order.pick_up_by = pick_up_time 
    new_order.valid = True

    db.session.commit()

    return success_response(new_order.simple_serialize(), 201)


@app.route("/orders/<int:order_id>/", methods=["GET"])
def get_order_by_id(order_id):
    """
    Endpoint for getting an order by id
    """
    order = Order.query.filter_by(id = order_id).first()
    if order_id is None:
        return failure_response(f"Task not found {order_id}!")
    return success_response(order.simple_serialize())


@app.route("/orders/<int:order_id>/", methods=["POST"])
def add_orderitem_to_order(order_id):
    """
   Endpoint for adding one orderitem to an existing order
    """

    body = json.loads(request.data)
    inventory_id = body.get("inventory_id")
    num_sel = body.get("num_sel")
    
    orderitem = Orderitem.query.filter_by(order_id = order_id, inventory_id = inventory_id ).first()

    try:
      if orderitem is None:
          orderitem = create_orderitem(inventory_id, num_sel, order_id)
      else:
          return failure_response("order item already exists! Use update order item instead")
      
    except Exception as e:
        return failure_response(f"{e}")
        
    return success_response(orderitem.serialize())


@app.route("/orders/submit/<int:order_id>/", methods=["POST"])
def submit_order(order_id):
    """
    Endpoint for submitting all orderitems with pickup information 
    """
    order = Order.query.filter_by(id = order_id).first()
    if order is None:
        return failure_response("order not found!")

    body = json.loads(request.data)  
    order.user_name =  body.get("user_name")
    order.time_created = datetime.datetime.now()
    # if the order is created after 19 
    if order.time_created.hour > 19:
      pick_up_time = order.time_created + datetime.timedelta(days = 1)
      pick_up_time = pick_up_time.replace(hour =  18, minute= 59, second= 59)
    else:
      pick_up_time = order.time_created + datetime.timedelta(hours = 2)
      if  pick_up_time.hour > 19:
        pick_up_time = pick_up_time.replace(hour =  18, minute= 59, second= 59)

    order.pick_up_by = pick_up_time 
    order.valid = True

    db.session.commit()

    return success_response(order.serialize())


@app.route("/orders/<int:order_id>/", methods=["DELETE"])
def delete_order(order_id):
    """
    Endpoint for delting an order
    """
    order = Order.query.filter_by(id = order_id).first()
    if order is None:
        return failure_response("Order not found!")
    db.session.delete(order)
    db.session.commit()
    return success_response(order.serialize())


# -- ORDERITEM ROUTES---------------------------------------------------

@app.route("/orderitems/", methods=["GET"])
def get_orderitems():
    """
    Endpoint for getting all orderitems
    """
    orderitems = []
    for orderitem in Orderitem.query.all(): 
        orderitems.append(orderitem.serialize()) 
    return success_response({"orderitems": orderitems})


def simlpe_create_orderitem(order_id, inventory_json):
    """
    Return the total price to the orderitem
    """
    inventory_id = inventory_json.get("inventory_id")
    num_sel =  inventory_json.get("num_sel")

    orderitem = create_orderitem(inventory_id, num_sel, order_id)

def create_orderitem(inventory_id, num_sel, order_id):
    """
    Create an orderitem from inventory_id, num_sel, and order_id
    Return the Oderitem object
    """

    order = Order.query.filter_by(id = order_id ).first()
    if order is None:
        raise Exception("Order not found!")

    inventory = Inventory.query.filter_by(id = inventory_id).first()
    if inventory is None:
        raise Exception("Inventory not found!")

    orderitem = Orderitem(
        inventory_id = inventory_id,
        num_sel =  num_sel,
        order_id = order_id
    )

    price = inventory.price * num_sel
    order.total_price += price

    order.order_items.append(orderitem)
    inventory.order_items.append(orderitem)

    db.session.add(orderitem)
    db.session.commit()

    print("orderitem type in create order item", type(orderitem))

    return orderitem


@app.route("/orderitems/<int:order_id>/<int:inventory_id>/increase/", methods=["POST"])
def increase_orderitem(order_id, inventory_id):
  """
  Endpoint for increasing the number of an inventory in an order by 1
  """
  return update_orderitem(order_id, inventory_id, 1)


@app.route("/orderitems/<int:order_id>/<int:inventory_id>/decrease/", methods=["POST"])
def decrease_orderitem(order_id, inventory_id):
  """
  Endpoint for decreasing the number of an inventory in an order by 1
  """
  return update_orderitem(order_id, inventory_id, -1)


def update_orderitem(order_id, inventory_id, num_sel_diff):
    """
    Update the  the number of an inventory in an order by num_sel_diff
    """
    order = Order.query.filter_by(id = order_id).first()
    if order is None:
        return failure_response("Order not found!")
    
    inventory = Inventory.query.filter_by(id = inventory_id).first()
    if inventory is None:
        return failure_response("Inventory not found!")

    orderitem = Orderitem.query.filter_by(order_id = order_id, inventory_id = inventory_id ).first()
    if orderitem is None:
        return failure_response("Order not found!")

    orderitem.num_sel += num_sel_diff
    price_diff = num_sel_diff * inventory.price
    order.total_price += price_diff
    db.session.commit()

    if orderitem.num_sel == 0:
      delete_orderitem(order_id, inventory_id)

    db.session.commit()

    return success_response(order.serialize())

    
@app.route("/orderitems/<int:order_id>/<int:inventory_id>/", methods=["DELETE"])
def delete_orderitem(order_id, inventory_id):
    """
    Endpoint for deletinf an orderitem
    if order.order_items is empty, delte the order
    """
    order = Order.query.filter_by(id = order_id).first()
    if order is None:
        return failure_response("Order not found!")

    orderitem = Orderitem.query.filter_by(order_id = order_id, inventory_id = inventory_id ).first()
    if orderitem is None:
        return failure_response("Order not found!")
    
    if orderitem.num_sel > 0:
        return failure_response("Can't delte orderitem since the number selected is larger than 0")

    db.session.delete(orderitem)
    db.session.commit()
    #check if the order_items of order is empty: if empty delte the order
    if len(order.order_items) == 0:
        delete_order(order_id)

    return success_response(order.serialize())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    app.run(host="0.0.0.0", port=8002, debug=True)

