# Stripped down version of the AppDaemon script that I'm using for testing.

import json
import urllib.request
import datetime

class AuroraNotify():

    def initialize(self):
        # args
        self.longitude = float(-149.48)
        self.latitude = float(61.56)
        self.interval = int(900)

        self.APIUrl = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
        self.longitude = self.longitude % 360 # Convert -180 to 180 to 360 longitudinal values
        print("AuroraNotify.initialize() complete")
        self.get_forecast_results(self)

    def utc_to_local(self, utc_str):
        corrected_iso = utc_str.replace("Z", "+00:00")
        utc_dt = datetime.datetime.fromisoformat(corrected_iso)
        return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    def get_forecast_results(self, **kwargs):
        forecast_dict = {}

        try:
            with urllib.request.urlopen(self.APIUrl) as resp:
                forecast_data = json.load(resp)

            observation_time = self.utc_to_local(self, forecast_data["Observation Time"])
            forecast_time = self.utc_to_local(self, forecast_data["Forecast Time"])

            for forecast_item in forecast_data["coordinates"]:
                forecast_dict[forecast_item[0], forecast_item[1]] = int(forecast_item[2])

            visibility = forecast_dict.get((int(self.longitude), int(self.latitude)), "Unknown")

        finally:
            print(f"Aurora Visibility is: {int(visibility)}")
            print(f"Observation Time: {observation_time}")
            print(f"Forecast Time: {forecast_time}")

notify = AuroraNotify
notify.initialize(notify)