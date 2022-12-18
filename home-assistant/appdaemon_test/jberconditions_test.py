# Stripped down version of the AppDaemon script that I'm using for testing.

import requests
import re
from bs4 import BeautifulSoup

class JberConditions():

    def initialize(self):
        # args
        self.interval = int(900)

        self.URL = 'https://www.jber.jb.mil/'
        print("JberConditions.initialize() complete.")
        self.get_jber_conditions(self)

    def get_jber_conditions(self, **kwargs):
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
            print(f"Road Conditions are: {road_condition}")
            print(f"Reporting is: {reporting}")
            print('end')

conditions  = JberConditions
conditions.initialize(conditions)