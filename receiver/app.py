import connexion
import yaml
import logging.config
from flask import jsonify, request
import datetime
import json
from pykafka import KafkaClient
import os

app = connexion.FlaskApp(__name__, specification_dir='')

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

producer = None

def kafka_logging():
    global producer
    if producer is None:
        client = KafkaClient(hosts=f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}')
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        producer = topic.get_sync_producer()
    return producer

@app.route('/cards/input-card', methods=['POST'])
def add_card_database(): 
    body = request.json
    producer = kafka_logging()
    msg = {
        "type": "card_input",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    logger.info('Input info sent to Kafka')
    return jsonify(status=201, content="Event Produced")

@app.route('/cards/rate-seller', methods=['POST'])
def rate_seller(): 
    body = request.json
    producer = kafka_logging()
    msg = {
        "type": "rate_seller",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    logger.info('Rating info sent to Kafka')
    return jsonify(status=201, content="Event Produced")

app.add_api("cardapi.yaml")

if __name__ == "__main__":
    app.run(port=8080)
