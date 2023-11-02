import connexion
from connexion import NoContent
import json
import datetime
from flask import Flask,jsonify,request
from flask import Flask, render_template, request, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from card_database import add_card
from rate_seller_database import SellerRating
import logging.config
import requests
import yaml
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


# Logging conf
with open('./log_conf.yml', 'r') as file:
    config = yaml.safe_load(file)

with open('./app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

logging.config.dictConfig(config)
logger = logging.getLogger('basicLogger')

# Datastore conf
with open('app_conf.yml', 'r') as file:
    db_config = yaml.safe_load(file)
    
DB_ENGINE = create_engine(db_config['datastore']['url'], echo=True)
hostname, port = DB_ENGINE.url.host, DB_ENGINE.url.port
logger.info(f'MySQL database hostname: {hostname}, port: {port}')
# DB_ENGINE = create_engine("mysql+mysqlconnector://root:password@localhost:3306/Cardapp", echo=True)
DB_SESSION = sessionmaker(bind=DB_ENGINE)   
app = connexion.FlaskApp(__name__, specification_dir='')

def process_messages():
    try:
        logger.info("Connecting to Kafka...")
        hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
        client = KafkaClient(hosts=hostname)
        logger.info("Connected to Kafka.")
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                             reset_offset_on_start=False,
                                             auto_offset_reset=OffsetType.LATEST)
        logger.info(f"Consumer created. Listening for messages on topic: {app_config['events']['topic']}")
        
        # This is blocking - it will wait for a new message
        for msg in consumer:
            if msg is not None:
                msg_str = msg.value.decode('utf-8')
                msg = json.loads(msg_str)
                logger.info("Received message: %s" % msg)
                # rest of your code
            else:
                logger.warning("Received None message")
    except Exception as e:
        logger.error(f"Error in process_messages: {str(e)}", exc_info=True)


# def process_messages():
#     """ Process event messages """
#     hostname = "%s:%d" % (app_config["events"]["hostname"],
#     app_config["events"]["port"])
#     client = KafkaClient(hosts=hostname)
#     topic = client.topics[str.encode(app_config["events"]["topic"])]
#     consumer = topic.get_simple_consumer(consumer_group=b'event_group',
#     reset_offset_on_start=False,
#     auto_offset_reset=OffsetType.EARLIEST)
#     # This is blocking - it will wait for a new message
#     for msg in consumer:
#         msg_str = msg.value.decode('utf-8')
#         msg = json.loads(msg_str)
#         logger.info("Message: %s" % msg)
#         payload = msg["payload"]
#         session = DB_SESSION()  # Create a new session

#         if msg["type"] == "card_input": # Change this to your event type
#         # Store the event1 (i.e., the payload) to the DB
#             card_input = add_card(**payload)
#             session.add(card_input)
    
#         elif msg["type"] == "rate_seller":
#             rate_seller = SellerRating(**payload)
#             session.add(rate_seller)    

#         #troubleshooting
#         try:
#             session.commit()
#         except Exception as e:
#             logger.error(f"Failed to commit session: {e}", exc_info=True)
#             session.rollback()  
#         finally:
#             session.close()  

#         consumer.commit_offsets()

# @app.route('/cards/input-card', methods=['POST'])
# def report_card_database():
#     data = request.json
#     print(data)
#     session = DB_SESSION()
#     json_temp = data
#     times = datetime.datetime.now()
#     timestamp = {"received_timestamp":str(times)}
#     timestamp.update(json_temp)
#     rep_card = add_card(timestamp['received_timestamp'],
#                         timestamp['brand'],
#                         timestamp['card_id'],
#                         timestamp['condition'],
#                         timestamp['date_added'],
#                         timestamp['price'],
#                         timestamp['seller_id'],
#                         timestamp['website'])
    
#     session.add(rep_card)
#     session.commit()
#     session.close()
#     logger.info("Information stored in DB")
    
#     return Response("Done", status=201)


# @app.route('/cards/rate-seller', methods=['POST'])
# def rate_seller():
#     data = request.json
#     session = DB_SESSION()
#     json_temp = data
#     times = datetime.datetime.now()
#     timestamp = {"received_timestamp":str(times)}
#     timestamp.update(json_temp)
#     new_rating = SellerRating(timestamp['received_timestamp'],
#                           timestamp['seller_id'],
#                           timestamp['user_id'],
#                           timestamp['rating'],
#                           timestamp['comment'],
#                           timestamp['date_rated']
#     )
#     session.add(new_rating)
#     session.commit()
#     session.close()
#     logger.info("Seller rating stored in DB")

#     return Response("Done", status=201)

@app.route('/cards/events/input-card', methods=['GET'])
def get_card_input_events():
    """Gets new card input events after the specified timestamp."""
    timestamp = request.args.get('timestamp')
    session = DB_SESSION()
    results_list = []
    try:
        timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        card_events = session.query(add_card).filter(add_card.date_added >= timestamp_datetime)

        for event in card_events:
            results_list.append(event.to_dict())
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to retrieve card input events: {e}", exc_info=True)
        return {"message": str(e)}, 400
    finally:
        session.close()

    logger.info(f"Query for card input events after {timestamp} returns {len(results_list)} results")
    return jsonify(results_list), 200

        

@app.route('/cards/events/rate-seller', methods=['GET'])
def get_seller_rating_events():
    """Gets new seller rating events after the specified timestamp."""
    timestamp = request.args.get('timestamp')
    session = DB_SESSION()
    results_list = []
    try:
        timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        rating_events = session.query(SellerRating).filter(SellerRating.date_rated >= timestamp_datetime)

        for event in rating_events:
            results_list.append(event.to_dict())
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to retrieve seller rating events: {e}", exc_info=True)
        return {"message": str(e)}, 400
    finally:
        session.close()

    logger.info(f"Query for seller rating events after {timestamp} returns {len(results_list)} results")
    return jsonify(results_list), 200     

Base.metadata.create_all(DB_ENGINE)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.daemon = True
    t1.start()
    app.run(port = '8090')