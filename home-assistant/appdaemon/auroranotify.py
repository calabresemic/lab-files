import mqttapi as mqtt
import json
import urllib.request
import datetime

class AuroraNotify(mqtt.Mqtt):

    def initialize(self):
        #args
        self.longitude = int(self.args.get("longitude"))
        self.latitude = int(self.args.get("latitude"))
        self.interval = int(self.args.get("interval, 900"))

        self.APIUrl = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
        self.longitude = self.longitude % 360 # Convert -180 to 180 to 360 longitudinal values
        self.run_every(self.get_forecast_results, "now", self.interval)
        self.log("AuroraNotify.initialize() complete")

    def utc_to_local(self, utc_str):
        corrected_iso = utc_str.replace("Z", "+00:00")
        utc_dt = datetime.datetime.fromisoformat(corrected_iso)
        return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    def get_forecast_results(self, kwargs):
        forecast_dict = {}

        try:
            with urllib.request.urlopen(self.APIUrl) as resp:
                forecast_data = json.load(resp)

            # Gather reported times
            observation_time = self.utc_to_local(forecast_data["Observation Time"])
            forecast_time = self.utc_to_local(forecast_data["Forecast Time"])

            # Convert data to dictionary
            for forecast_item in forecast_data["coordinates"]:
                forecast_dict[forecast_item[0], forecast_item[1]] = int(forecast_item[2])

            # Visibility based on matching lat and long to dict, return unknown if unable to match
            visibility = forecast_dict.get((int(self.longitude), int(self.latitude)), "Unknown")
            self.log(f"visibility: {visibility}") # Write to console for troubleshooting

        finally:
            self.mqtt_publish("house/aurora/visibility", visibility, retain = True)
            # TO DO: Update to json format to include forcast and observation times