from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import datetime
import connexion
from connexion import NoContent
import logging
import yaml
import os
import json 

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

# Function to save the health status to a JSON file
def save_health_status():
    with open('health_status.json', 'w') as f:
        json.dump(health_status, f)

# Modified check_health function to call save_health_status
def check_health():
    services = app_config['services']
    for service_name, service_url in services.items():
        try:
            response = requests.get(service_url, timeout=app_config['scheduler']['timeout_sec'])
            health_status[service_name] = "Running" if response.status_code == 200 else "Down"
        except requests.exceptions.RequestException:
            health_status[service_name] = "Down"
    health_status["last_update"] = datetime.utcnow().isoformat()
    save_health_status()  # Save status to JSON file

# Modified get_health endpoint to read from the JSON file
@app.route('/health', methods=['GET'])
def get_health():
    try:
        with open('health_status.json', 'r') as f:
            saved_health_status = json.load(f)
        return jsonify(saved_health_status)
    except FileNotFoundError:
        logger.error("Health status file not found.")
        return jsonify(health_status)  # Return the in-memory status if file not found

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_health, trigger="interval", seconds=20)
scheduler.start()


if __name__ == "__main__":
    # Load the health status from the file on startup if available
    try:
        with open('health_status.json', 'r') as f:
            health_status = json.load(f)
    except FileNotFoundError:
        logger.error("Health status file not found. Starting with default statuses.")
    app.run(port=8120)

