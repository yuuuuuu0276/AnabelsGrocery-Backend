from flask_sqlalchemy import SQLAlchemy
import base64
import boto3
import datetime
import io
from io import BytesIO
from mimetypes import guess_extension, guess_type
import os
from PIL import Image
import random
import re
import string

db = SQLAlchemy()

inventory_category_association_table = db.Table(
  "association_category",
  db.Column("inventory_id", db.Integer, db.ForeignKey("inventory.id")),
  db.Column("category_id", db.Integer, db.ForeignKey("category.id"))
)

inventory_order_menu_association_table = db.Table(
  "association_menu",
  db.Column("inventory_id", db.Integer, db.ForeignKey("inventory.id")),
  db.Column("menu_id", db.Integer, db.ForeignKey("menu.id")) 
)

class Inventory (db.Model):
  """
  Inventory Model
  """

  __tablename__ = "inventory"
  id = db.Column(db.Integer, primary_key = True, autoincrement = True) 
  image = db.Column(db.String, nullable = False)
  name = db.Column(db.String, nullable = False)
  description = db.Column(db.String, nullable = False)
  price = db.Column(db.Float, nullable = False)
  # many to many (name + 's' represents for many to many field name), could be null
  categories = db.relationship("Category", secondary = inventory_category_association_table, back_populates = "inventories") 
  menus = db.relationship("Menu", secondary = inventory_order_menu_association_table, back_populates = "inventories")
  # orderitems
  order_items = db.relationship("Orderitem", cascade = "delete")

  def __init__(self, **kwargs):
    """
    Initializes an Inventory object
    """
    self.image =  kwargs.get("image", "") 
    self.name = kwargs.get("name", "") 
    self.description = kwargs.get("description", "") 
    self.price = kwargs.get("price", "") 
  
  def serialize_all(self):
    """
    Serializes a Inventory object
    """

    return {
      "id": self.id,
      "image": self.image,
      "name": self.name,
      "description": self.description,
      "price": self.price,
      "category": [c.simple_serialize() for c in self.categories],
      "menus": [m.simple_serialize() for m in self.menus],
      "order_items": [oi.simple_serialize() for oi in self.order_items]
    }
  
  def serialize_for_render(self):
     """
     Serializes necessary info for front end to render
     """
     try:
        selectedNum = self.order_items[0].num_sel
     except Exception as e:
        selectedNum = 0

     try:
        category = self.categories[0].id
     except Exception as e:
        category = 0


     return {
      "id": self.id,
      "image": self.image,
      "name": self.name,
      "description": self.description,
      "price": self.price,
      "category": category,
      "selectedNum":selectedNum
    }
  

  
  def serialize_for_category(self):
    """
    Serializes a Inventory object
    """

    return {
      "id": self.id,
      "image": self.image,
      "name": self.name,
      "description": self.description,
      "price": self.price
    }


class Category(db.Model):
  """
  Category model
  """

  __tablename__ = "category"
  id = db.Column(db.Integer, primary_key = True, autoincrement = True)
  name = db.Column(db.String, nullable = False)
  description = db.Column(db.String, nullable = False)
  inventories = db.relationship("Inventory", secondary = inventory_category_association_table, back_populates ="categories")


  def __init__(self, **kwargs):
    """
    Initialize a Category object
    """

    self.name = kwargs.get("name")
    self.description = kwargs.get("description", "")
   

  def serialize(self):
    """
    serialize
    """

    return{"id": self.id,
          "name": self.name,
          "description": self.description, 
          "inventories": [i.serialize_for_category() for i in self.inventories]
           }
  
  def simple_serialize(self):
    return{"id": self.id, 
           "description": self.description, 
           "name": self.name
           }
  

class Menu(db.Model):
  """
  Menu model
  """

  __tablename__ = "menu"
  id = db.Column(db.Integer, primary_key = True, autoincrement = True) 
  name = db.Column(db.String, nullable = False)
  description = db.Column(db.String, nullable = False)
  instruction = db.Column(db.String, nullable = False)
  inventories = db.relationship("Inventory", secondary = inventory_order_menu_association_table, back_populates ="menus")
  #----------
  # images = db.relationship("Asset", cascade = "delete")
  image_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)


  def __init__(self, **kwargs):
    """
    Initialize a Category object
    """
    self.name = kwargs.get("name", "")
    self.description = kwargs.get("description", "")
    self.instruction = kwargs.get("instruction", "")
    self.image_id = kwargs.get("image_id", "")
    

  def serialize(self):
    """
    serialize
    """
    asset = Asset.query.filter_by(id = self.image_id).first()

    return{"id": self.id, 
           "name": self.name,
            "description": self.description, 
           "inventories": [t.serialize() for t in self.inventories],
           "image": asset.serialize()
           }
  
  
  def simple_serialize(self):
    return{"id": self.id,  
           "name": self.name, 
           "description": self.description
           }
  
class Order(db.Model):
  """
  Order model
  """

  __tablename__ = "order"
  id = db.Column(db.Integer, primary_key = True, autoincrement = True) 
  time_created = db.Column(db.DateTime)
  pick_up_by  = db.Column(db.DateTime)
  total_price = db.Column(db.Float, nullable = False)
  valid = db.Column(db.Boolean, nullable = False)
  # one to many
  order_items = db.relationship("Orderitem", cascade = "delete")


  
  def __init__(self, **kwargs):
    """
    Initialize a Category object
    """
    
    self.total_price = kwargs.get("total_price", 0)
    self.valid = kwargs.get("valid", False)
    

  def serialize(self):
    """
    serialize
    """
    return{"id": self.id, 
           "time_created": str(self.time_created),
           "pick_up_by": str(self.pick_up_by),
           "total_price": self.total_price,
           "valid": self.valid,
           "order_items": [oi.serialize() for oi in self.order_items]
           }
  
  def simple_serialize(self):
    return{
          "id": self.id, 
          "time_created": str(self.time_created),
           "pick_up_by": str(self.pick_up_by),
           "total_price": self.total_price,
           "valid": self.valid,
           "order_items": [oi.serialize_for_order() for oi in self.order_items]
           }
  
class Orderitem(db.Model):
  """
  Orderitem model
  """
  __tablename__ = "orderitem"
  id = db.Column(db.Integer, primary_key = True, autoincrement = True) 
  num_sel = db.Column(db.Integer,  nullable = False)
  inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable = False)
  order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable = False)

  def __init__(self, **kwargs):
    """
    Initialize an Orderitem object
    """
    self.inventory_id = kwargs.get("inventroy_id", "")
    self.num_sel = kwargs.get("num_sel", "")
    self.order_id = kwargs.get("order_id", "")
  
  def serialize(self):
    """
    Serialize
    """
    return{
      "id": self.id, 
      "num_sel": self.num_sel,
      "inventory_id": self.inventory_id,
      "num_sel": self.num_sel
    }
  
  def serialize_for_order(self):
    """
    Serialize
    """
    inventory = Inventory.query.filter_by(id = self.inventory_id).first()

    return{

      "image": inventory.image,
      "name": inventory.name,
      "selectedNum":self.num_sel
    }
  
  

EXTENSIONS = ["png","gif","jpg","jpeg"]
BASE_DIR = os.getcwd()
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com"

class Asset(db.Model):
    """
    Asset Model
    Has a one-to-one relationship with Event table
    """
    __tablename__ = "assets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_url = db.Column(db.String, nullable=True)
    salt =  db.Column(db.String, nullable=False)
    extension =  db.Column(db.String, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable = False)

    # menu_id = db.Column(db.Integer, db.ForeignKey("menu.id"), nullable = False)

    def __init__(self,**kwargs):
        """
        Initializes an Asset object/entry
        """
        self.create(kwargs.get("image_data"))

    def serialize(self):
        """
        Serializes and Asset object
        """

        return{
            "url": f"{self.base_url}/{self.salt}.{self.extension}",
            "created_at": str(self.created_at)
        }

    def create(self, image_data):
        """
        Given an image in base64 form, it
        1. Rejects the image is the filetype is not supported file type
        2. Generates a random string for the image file name
        3. Decodes the image and attempts to upload it to AWS
        """
        try:
            ext = guess_extension(guess_type(image_data)[0])[1:]

            #only accepts supported file types
            if ext not in EXTENSIONS:
                raise Exception(f"Unsupported file type: {ext}")


            #generate random strong name for file
            salt = "".join(
                random.SystemRandom().choice(
                    string.ascii_uppercase+ string.digits
                )
                for _ in range(16)
            )

            #decode the image and upload to aws
            #remove header of base64 string
            img_str = re.sub("^data:image/.+;base64,", "", image_data)
            img_data = base64.b64decode(img_str)
            img = Image.open(BytesIO(img_data))

            self.base_url = S3_BASE_URL
            self.salt = salt
            self.extension = ext
            self.width = img.width
            self.height = img.height
            self.created_at = datetime.datetime.now()

            img_filename = f"{self.salt}.{self.extension}"
            self.upload(img, img_filename)

        except Exception as e:
            print(f"Error when creating image: {e}")

    def upload(self, img, img_filename):
        """
        Attempt to upload the image to the specified S3 bucket
        """
        try:
            # save image temporarily on server
            img_temploc = f"{BASE_DIR}/{img_filename}"
            img.save(img_temploc)
            
            # upload image to S3
            s3_client = boto3.client("s3")
            s3_client.upload_file(img_temploc, S3_BUCKET_NAME, img_filename)

            # make s3 image url is public
            s3_resource = boto3.resource("s3")
            object_acl = s3_resource.ObjectAcl(S3_BUCKET_NAME, img_filename)
            object_acl.put(ACL="public-read")

            # removes image from server
            os.remove(img_temploc)


        except Exception as e:
            print(f"Error when uploading image: {e}")
            
#-------------------------------------------------------------------------------



    

