# Stripped down version of the AppDaemon script that I'm using for testing.

import requests
import datetime
from bs4 import BeautifulSoup

class JberConditions():

    def initialize(self):
        self.URL = 'https://www.jber.jb.mil/'
        # self.run_every(self.get_jber_conditions, datetime.datetime.now(), 30*60)
        # self.log("JberConditions.initialize() complete.")
        print("JberConditions.initialize() complete.")
        self.get_jber_conditions(self)

    def get_jber_conditions(self, **kwargs):
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
            elif 'MISSION ESSENTIAL ONLY' in result:
                reporting = 'Mission Essential Only'
            else:
                reporting = 'Unknown'

        finally:
            # Update HA entities
            # self.mqtt_publish("jber/road_conditions", road_condition, retain = True)
            # self.mqtt_publish("jber/reporting", reporting, retain = True)
            print("Road Conditions are:", road_condition)
            print("Reporting is:", reporting)

conditions  = JberConditions
conditions.initialize(conditions)