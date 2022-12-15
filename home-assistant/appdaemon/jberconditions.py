import mqttapi as mqtt
import requests
import datetime
from bs4 import BeautifulSoup

class JberConditions(mqtt.Mqtt):

    def initialize(self):
        # args
        self.interval = int(self.args.get("interval", 900))

        self.URL = 'https://www.jber.jb.mil/'
        self.run_every(self.get_jber_conditions, "now", self.interval)
        self.log("JberConditions.initialize() complete.")

    def get_jber_conditions(self, kwargs):
        try:
            # Get the website data
            raw_html = requests.get(self.URL).text
            data = BeautifulSoup(raw_html, 'html.parser')
            result = str(data.find("div", id="dnn_ctr24928_HtmlModule_lblContent"))

            # Process road conditions (poorly)
            if 'GREEN' in result:
                road_condition = 'Green'
            elif 'AMBER' in result:
                road_condition = 'Amber'
            elif 'RED' in result:
                road_condition = 'Red'
            elif 'BLACK' in result:
                road_condition = 'Black'
            else:
                road_condition = 'Unknown'

            # Process reporting status (also poorly)
            if 'NORMAL' in result:
                reporting = 'Normal'
            elif 'DELAYED REPORTING' in result:
                reporting = 'Delayed'
            elif ('MISSION ESSENTIAL ONLY' in result) or ('MISSION ESSENTIAL' in result):
                reporting = 'Mission Essential Only'
            else:
                reporting = 'Unknown'

        finally:
            # Update HA entities
            self.mqtt_publish("jber/road_conditions", road_condition, retain = True)
            self.mqtt_publish("jber/reporting", reporting, retain = True)
