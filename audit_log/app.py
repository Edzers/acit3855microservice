import connexion
from connexion import NoContent
import json
import datetime
from flask import Flask,jsonify,request
from flask import Flask, render_template, request, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging.config
import requests
import yaml
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
from flask_cors import CORS, cross_origin
import os

app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'

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


def get_card_input_event(index):
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True,
        consumer_timeout_ms=2000
    )
    logger.info("Retrieving card_input at index %d", index)
    
    current_index = 0
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        if msg.get('type') == 'card_input':
            if current_index == index:
                return msg, 200
            current_index += 1

    logger.error("Could not find card_input at index %d", index)
    return {"message": "Not Found"}, 404

# Test the function
# event, status_code = get_card_input_event(3)
# print(event)

def get_rate_seller_event(index):
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True,
        consumer_timeout_ms=1000
    )
    logger.info("Retrieving rate_seller at index %d", index)
    
    current_index = 0
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        if msg.get('type') == 'rate_seller':
            if current_index == index:
                return msg, 200
            current_index += 1

    logger.error("Could not find rate_seller at index %d", index)
    return {"message": "Not Found"}, 404

# Test the function
# try:
#     event, status_code = get_rate_seller_event(1)
#     print(event, status_code)
# except Exception as e:
#     print("An error occurred:", str(e))
    

@app.route('/card_input', methods=['GET'])
def get_card_input_event_route():
    index = int(request.args.get('index'))
    event, status_code = get_card_input_event(index)
    return jsonify(event), status_code

@app.route('/rate_seller', methods=['GET'])
def get_rate_seller_event_route():
    index = int(request.args.get('index'))
    try:
        event, status_code = get_rate_seller_event(index)
        return jsonify(event), status_code
    except Exception as e:
        logger.error("Unhandled exception: %s", str(e), exc_info=True)
        return jsonify({"message": "Internal Server Error"}), 500



app.add_api('openapi.yml', arguments={'title': 'Audit API'})

if __name__ == "__main__":
    app.run(port=8110)  