from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from datetime import datetime
import connexion
from connexion import NoContent
import logging.config
import yaml
import os
import json

# Load configurations based on the environment
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

# Initialize Flask app for Connexion
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("cardapi.yaml")  
flask_app = app.app

# Initialize the health status dictionary
health_status = {
    "receiver": "Down",
    "storage": "Down",
    "processing": "Down",
    "audit": "Down",
    "last_update": datetime.utcnow().isoformat()
}

# Function to check the health of other services and update the status
def check_health():
    for service_name, service_url in app_config['services'].items():
        try:
            response = requests.get(service_url, timeout=app_config['scheduler']['timeout_sec'])
            health_status[service_name] = "Running" if response.status_code == 200 else "Down"
        except requests.exceptions.RequestException:
            health_status[service_name] = "Down"
    health_status["last_update"] = datetime.utcnow().isoformat()
    # Save the health status to a JSON file
    with open(app_config['datastore']['filename'], 'w') as f:
        json.dump(health_status, f)
    logger.info(f"Updated health status: {health_status}")

# Endpoint to get the health status of services
@app.route('/health', methods=['GET'])
def get_health():
    try:
        with open(app_config['datastore']['filename'], 'r') as f:
            current_health_status = json.load(f)
        return jsonify(current_health_status)
    except FileNotFoundError:
        logger.error("Health status file not found.")
        return jsonify(health_status)  # Return the in-memory status if file not found

# Initialize the scheduler to run the health check periodically
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_health, trigger="interval", seconds=app_config['scheduler']['period_sec'])
scheduler.start()

# Main entry point for the application
if __name__ == "__main__":
    # Run the health check once before starting to populate the status immediately
    check_health()
    # Run the Flask app
    flask_app.run(port=8120, use_reloader=False)
