from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import datetime
import connexion
from connexion import NoContent
import logging
import yaml
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

app = Flask(__name__)
health_status = {
    "receiver": "Down",
    "storage": "Down",
    "processing": "Down",
    "audit": "Down",
    "last_update": ""
}

def check_health():
    services = {"receiver": "http://localhost:8080/health", "storage": "http://localhost:8090/health","processing": "http://localhost:8100/health", "audit": "http://localhost:8110/health"}
    for service_name, service_url in services.items():
        try:
            response = requests.get(service_url, timeout=5)
            health_status[service_name] = "Running" if response.status_code == 200 else "Down"
        except requests.exceptions.RequestException:
            health_status[service_name] = "Down"
    health_status["last_update"] = datetime.utcnow().isoformat()

@app.route('/health', methods=['GET'])
def get_health():
    return jsonify(health_status)

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_health, trigger="interval", seconds=20)
scheduler.start()

if __name__ == "__main__":
    app.run(port=8120)
