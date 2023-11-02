import connexion
from connexion import NoContent
import json
from datetime import datetime
from flask import jsonify, Response 
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging.config
import yaml
from card_database import add_card
from rate_seller_database import SellerRating
from sqlalchemy.sql import func
import logging
import requests
import os


#DB_ENGINE = create_engine("mysql+mysqlconnector://root:password@localhost:3306/Cardapp", echo=True)
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())
 
with open('./log_conf.yml', 'r') as file:
    config = yaml.safe_load(file)
logging.config.dictConfig(config)
logger = logging.getLogger('basicLogger')
DB_ENGINE = create_engine(app_config['database']['url'], echo=True)
DB_SESSION = sessionmaker(bind=DB_ENGINE)

app = connexion.FlaskApp(__name__, specification_dir='')

def calculate_num_card_events(session):
    try:
        num_card_events = session.query(add_card).count()
        return num_card_events
    except Exception as e:
        logger.error(f"Error counting card events: {str(e)}")
        raise

def calculate_num_seller_rating_events(session):
    try:
        num_seller_rating_events = session.query(SellerRating).count()
        return num_seller_rating_events
    except Exception as e:
        logger.error(f"Error counting seller rating events: {str(e)}")
        raise


def calculate_max_card_price(session):
    try:
        max_price = session.query(func.max(add_card.price)).scalar()
        return float(max_price) if max_price is not None else 0.0
    except Exception as e:
        logger.error(f"Error calculating maximum card price: {str(e)}")
        raise


def calculate_max_seller_rating(session):
    try:
        #'rating' is the column name and 'SellerRating' is the table name
        max_rating = session.query(func.max(SellerRating.rating)).scalar()
        return float(max_rating) if max_rating is not None else 0.0
    except Exception as e:
        logger.error(f"Error calculating maximum seller rating: {str(e)}")
        raise

def populate_stats():
    logger.info("Start Periodic Processing")

    stats_file = app_config['datastore']['filename']
    # Read the current statistics from the JSON file
    try:
        with open(stats_file, 'r') as file:
            stats = json.load(file)
    except FileNotFoundError:   
        # If file not found, populate with entries
        stats = {
            "num_card_events": 0,
            "num_seller_rating_events": 0,
            "max_card_price": 0.0,
            "max_seller_rating": 0.0,
            "last_updated": datetime.utcnow().isoformat()
        }

    # Query the database to get the total number of events for each table
    session = DB_SESSION()
    try:
        total_card_events = calculate_num_card_events(session)
        total_seller_rating_events = calculate_num_seller_rating_events(session)
        max_card_price = calculate_max_card_price(session)
        max_seller_rating = calculate_max_seller_rating(session)
    except Exception as e:
        logger.error(f"Error retrieving stats from database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

    updated_stats = {
        "num_card_events": total_card_events,
        "num_seller_rating_events": total_seller_rating_events,
        "max_card_price": max_card_price,
        "max_seller_rating": max_seller_rating,
        "last_updated": datetime.utcnow().isoformat()
    }

    # Write the updated statistics to the JSON file
    with open(stats_file, 'w') as file:
        json.dump(updated_stats, file)

    logger.debug(f"Updated statistics: {updated_stats}")
    logger.info("Periodic processing has ended")

def get_stats():
    """Handle GET request for /events/stats."""
    logger.info("Request for statistics started")

    try: 
        with open(app_config['datastore']['filename'], 'r') as file:
            stats_file = json.load(file)
    except:
        return Response("Statistics do not exist", 404)

    stats_response = {
        "num_card_events": stats_file["num_card_events"],
        "num_seller_rating_events": stats_file["num_seller_rating_events"],
        "max_card_price": stats_file["max_card_price"],
        "max_seller_rating": stats_file["max_seller_rating"]
    }

    logger.debug(f"Statistics: {stats_response}")

    logger.info("Request for statistics completed")

    return Response(json.dumps(stats_response), 200)

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,'interval',seconds=app_config['scheduler']['period_sec'])
    sched.start()

# Add API endpoints
app.add_api("./cardapiget.yaml")

if __name__ == "__main__":
    # Initialize scheduler and run the application
    init_scheduler()
    app.run(port=8100, use_reloader=False)
