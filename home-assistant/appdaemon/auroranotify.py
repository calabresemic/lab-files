import hassapi as hass
import json
import urllib.request
import datetime

class AuroraNotify(hass.Hass):

    def initialize(self):
        self.longitude = int(self.args.get("longitude"))
        self.latitude = int(self.args.get("latitude"))
        self.APIUrl = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"

        # Convert -180 to 180 to 360 longitudinal values
        self.longitude = self.longitude % 360
        self.run_every(self.get_forecast_results, datetime.datetime.now(), 30*60)
        self.log("AuroraNotify.initialize() complete")

    def get_forecast_results(self, kwargs):
        forecast_dict = {}

        try:
            with urllib.request.urlopen(self.APIUrl) as resp:
                forecast_data = json.load(resp)

            for forecast_item in forecast_data["coordinates"]:
                forecast_dict[forecast_item[0], forecast_item[1]] = forecast_item[2]

            visibility = forecast_dict.get((int(self.longitude), int(self.latitude)),0)
            self.log(f"visibility: {visibility}")

        finally:
            self.set_value("input_number.aurora_visibility", int(visibility))