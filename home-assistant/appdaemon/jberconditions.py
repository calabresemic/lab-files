import mqttapi as mqtt
import requests
import re
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
            # Regex pattern to find conditions... 
            # Might need to adjust if they change their website
            pattern = "<b.*?>.*?(.+)<\/b.*?>"

            # Get the website data
            raw_html = requests.get(self.URL).text
            data = BeautifulSoup(raw_html, 'html.parser')
            result = str(data.find("div", id="dnn_ctr24928_HtmlModule_lblContent"))
            match_results = re.findall(pattern, result, re.IGNORECASE)

            # Manually declaring these here in case the text needs processing later.
            road_condition = match_results[0]
            reporting = match_results[1]

        finally:
            # Update HA entities
            self.mqtt_publish("jber/road_conditions", road_condition, retain = True)
            self.mqtt_publish("jber/reporting", reporting, retain = True)
