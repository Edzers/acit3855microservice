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
from sqlalchemy import and_
import time
import os

# Check environment and load configurations
if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)
    
DB_ENGINE = create_engine(app_config['datastore']['url'], echo=True)
hostname, port = DB_ENGINE.url.host, DB_ENGINE.url.port
logger.info(f'MySQL database hostname: {hostname}, port: {port}')
# DB_ENGINE = create_engine("mysql+mysqlconnector://root:password@localhost:3306/Cardapp", echo=True)
DB_SESSION = sessionmaker(bind=DB_ENGINE)   
app = connexion.FlaskApp(__name__, specification_dir='')


# Global variable for KafkaClient
kafka_client = None

def create_kafka_client():
    global kafka_client
    max_retries = app_config['kafka']['max_retries']
    retry_sleep = app_config['kafka']['retry_sleep']
    retry_count = 0

    while retry_count < max_retries:
        try:
            logger.info(f"Trying to connect to Kafka (Attempt {retry_count + 1}/{max_retries})...")
            hostname = "%s:%d" % (app_config['events']['hostname'], app_config['events']['port'])
            kafka_client = KafkaClient(hosts=hostname)
            logger.info("Connected to Kafka.")
            break  # Break the loop if connection is successful
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(retry_sleep)
            else:
                logger.error("Max retries reached. Unable to connect to Kafka.")
                raise Exception("Kafka connection failed after max retries")

def process_messages():
    global kafka_client
    try:
        topic = kafka_client.topics[str.encode(app_config['events']['topic'])]
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
                # Process the message here
            else:
                logger.warning("Received None message")
    except Exception as e:
        logger.error(f"Error in process_messages: {str(e)}", exc_info=True)



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
    """Gets card input events between the specified start and end timestamps."""
    start_timestamp = request.args.get('start_timestamp')
    end_timestamp = request.args.get('end_timestamp')
    session = DB_SESSION()
    results_list = []
    try:
        start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        card_events = session.query(add_card).filter(
            and_(add_card.date_added >= start_timestamp_datetime,
                 add_card.date_added < end_timestamp_datetime))

        for event in card_events:
            results_list.append(event.to_dict())
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to retrieve card input events: {e}", exc_info=True)
        return {"message": str(e)}, 400
    finally:
        session.close()

    logger.info(f"Query for card input events between {start_timestamp} and {end_timestamp} returns {len(results_list)} results")
    return jsonify(results_list), 200

@app.route('/cards/events/rate-seller', methods=['GET'])
def get_seller_rating_events():
    """Gets seller rating events between the specified start and end timestamps."""
    start_timestamp = request.args.get('start_timestamp')
    end_timestamp = request.args.get('end_timestamp')
    session = DB_SESSION()
    results_list = []
    try:
        start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        rating_events = session.query(SellerRating).filter(
            and_(SellerRating.date_rated >= start_timestamp_datetime,
                 SellerRating.date_rated < end_timestamp_datetime))

        for event in rating_events:
            results_list.append(event.to_dict())
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to retrieve seller rating events: {e}", exc_info=True)
        return {"message": str(e)}, 400
    finally:
        session.close()

    logger.info(f"Query for seller rating events between {start_timestamp} and {end_timestamp} returns {len(results_list)} results")
    return jsonify(results_list), 200

Base.metadata.create_all(DB_ENGINE)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.daemon = True
    t1.start()
    create_kafka_client()
    app.run(port = '8090')