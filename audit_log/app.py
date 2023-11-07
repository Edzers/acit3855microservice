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

app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'

with open('./log_conf.yml', 'r') as file:
    config = yaml.safe_load(file)

with open('./app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

logging.config.dictConfig(config)
logger = logging.getLogger('basicLogger')


def get_card_input_event(index):
    """Get card_input event in History."""
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    # Here we reset the offset on start so that we retrieve
    # messages at the beginning of the message queue.
    # To prevent the for loop from blocking, we set the timeout to
    # 1000ms. There is a risk that this loop never stops if the
    # index is large and messages are constantly being received!
    consumer = topic.get_simple_consumer(
        reset_offset_on_start=True,
        consumer_timeout_ms=1000
    )
    logger.info("Retrieving card_input at index %d", index)
    
    try:
        current_index = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg.get('type') == 'card_input' and current_index == index:
                # Found the event at the index you want
                # return the event and a 200 status code
                return msg, 200
            if msg.get('type') == 'card_input':
                # Increment the index for card_input events only
                current_index += 1
    except Exception as e:
        logger.error("No more messages found or an error occurred: %s", str(e))
        logger.error("Could not find card_input at index %d", index)
        return {"message": "Not Found"}, 404  # Ensure two values are returned
    

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
    event, status_code = get_rate_seller_event(index)
    return jsonify(event), status_code


app.add_api('openapi.yml', arguments={'title': 'Audit API'})

if __name__ == "__main__":
    app.run(port=8110)  