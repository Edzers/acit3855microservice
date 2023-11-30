from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime
import uuid 

class SellerRating(Base):
    __tablename__ = "SellerDB"
    
    rating_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # Set as CHAR(36) and primary key
    seller_id = Column(String(255))
    user_id = Column(String(255))
    rating = Column(Integer)
    comment = Column(String(255))
    date_rated = Column(String(255))
        
    def __init__(self, seller_id, user_id, rating, comment, date_rated):
        self.seller_id = seller_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment
        self.date_rated = date_rated

    def to_dict(self):
        return {
            'rating_id': str(self.rating_id),  # Convert UUID to string when outputting as a dictionary
            'seller_id': self.seller_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'date_rated': self.date_rated
        }

    @classmethod
    def create_from_msg(cls, msg):
        return cls(
            seller_id=msg.get('seller_id', ''),
            user_id=msg.get('user_id', ''),
            rating=msg.get('rating', 0),
            comment=msg.get('comment', ''),
            date_rated=msg.get('date_rated', ''),
            rating_id=msg.get('rating_id', None)  
        )