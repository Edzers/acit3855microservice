from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import uuid

class add_card(Base):
    __tablename__ = "CardDB"
    
    card_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # Set as CHAR(36) and primary key
    brand = Column(String(255))
    condition = Column(String(255)) 
    date_added = Column(String(255))
    price = Column(Integer)
    seller_id = Column(String(255))
    website = Column(String(255))
        
    def __init__(self, brand, condition, date_added, price, seller_id, website, card_id=None):
        self.brand = brand
        self.condition = condition
        self.date_added = date_added
        self.price = price
        self.seller_id = seller_id
        self.website = website
        if card_id is None:
            self.card_id = str(uuid.uuid4())  # Generate a new UUID if none is provided
        else:
            self.card_id = card_id 

    def to_dict(self):
        return {
            'card_id': self.card_id,
            'brand': self.brand,
            'condition': self.condition,
            'date_added': self.date_added,
            'price': self.price,
            'seller_id': self.seller_id,
            'website': self.website
        }

    @classmethod
    def create_from_msg(cls, msg):
        return cls(
            brand=msg.get('brand', ''),
            condition=msg.get('condition', ''),
            date_added=msg.get('date_added', ''),
            price=msg.get('price', 0),
            seller_id=msg.get('seller_id', ''),
            website=msg.get('website', ''),
            card_id=msg.get('card_id', None)  
        )