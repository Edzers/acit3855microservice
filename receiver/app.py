import connexion
import yaml
import logging.config
from flask import jsonify, request
import datetime
import json
from pykafka import KafkaClient

app = connexion.FlaskApp(__name__, specification_dir='')

with open('./app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('./log_conf.yml', 'r') as file:
    config = yaml.safe_load(file)
    
logging.config.dictConfig(config)
logger = logging.getLogger('basicLogger')

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
