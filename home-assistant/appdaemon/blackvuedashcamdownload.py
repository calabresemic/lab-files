import hassapi as hass
from smb.SMBConnection import SMBConnection
import requests
import re
import io

class BlackVueDashCamDownload(hass.Hass):

    def initialize(self):
        # SMB args
        self.smb_server_name = self.args.get("smb_server_name")
        self.smb_username = self.args.get("smb_username")
        self.smb_password = self.args.get("smb_password")
        self.smb_timeout = self.args.get("smb_timeout", 30)
        self.smb_share = self.args.get("smb_share")
        self.smb_path = self.args.get("smb_path", "/").replace("\\","/")

        # Other args
        self.event_to_listen_for = self.args.get("event_to_listen_for", "dashcam_connected")
        self.dashcam_ip = self.args.get("dashcam_ip")
        self.video_only = self.args.get("download_videosonly", False)
        self.rear_camera = self.args.get("rear_camera", True)
        self.days_to_keep = self.args.get("days_to_keep", 7)
        self.notify_title = self.args.get("notify_title")

        # Start listening to events
        self.listen_event(self.download_from_dashcam, self.event_to_listen_for)
        self.log(f"Listening for {self.event_to_listen_for} event")
        self.log("DashCamDownload.initialize() complete")

    def download_from_dashcam(self, event, data, kwargs):
        # Method to connect to camera and smb share and transfer files
        self.log(f"Starting DashCam Download for Camera: {self.dashcam_ip}")
        self.notify(f"Starting DashCam Download for Camera: {self.dashcam_ip}", title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])

        # Declare vars
        pattern = re.compile('^.*_P.*$') # Regex to identify "parking" videos
        files_on_camera = {}
        files_on_share = []
        downloaded_files = 0

        try:
            # Retrieve list of files
            url = f'http://{self.dashcam_ip}/blackvue_vod.cgi'
            vid_list = requests.get(url)

            if vid_list.status_code == 200: # Successfully retrieved results
                trimmed_results = vid_list.text.replace('n:/Record/','').replace('F.mp4,s:1000000','').replace('R.mp4,s:1000000','')
                split_results = trimmed_results.split() # Convert results to list
                split_results.pop(0) # Remove first line

                for filename in split_results:
                    if pattern.match(filename):
                        # Remove parking files, I have to leave parking recording
                        # on to keep the camera connected to wifi when at home
                        continue
                    else:
                        # Continue with good results
                        files_on_camera[f"{filename}F.mp4"] = True

                        if self.video_only == False:
                            # Downloads the accompanying metadata files for playback later
                            files_on_camera[f"{filename}F.thm"] = True
                            files_on_camera[f"{filename}.gps"] = True
                            files_on_camera[f"{filename}.3gf"] = True

                        if self.rear_camera == True:
                            # Download the rear camera video
                            files_on_camera[f"{filename}R.mp4"] = True

                            if self.video_only == False:
                                # Download the rear camera metadata
                                files_on_camera[f"{filename}R.thm"] = True

                self.log(f'Found {len(files_on_camera)} files on camera.')

                # Initiate SMB Connection
                with SMBConnection(self.smb_username, self.smb_password, 'hassio.home.domain', self.smb_server_name, use_ntlm_v2=True, is_direct_tcp=True) as conn:
                    connected = conn.connect(self.smb_server_name, port=445, timeout=self.smb_timeout)

                    if connected == True:
                        for list in conn.listPath(self.smb_share, self.smb_path):
                            files_on_share.append(list.filename)

                        for file in files_on_camera:
                            if file in files_on_share:
                                continue
                            else:
                                url = f'http://{self.dashcam_ip}/Record/{file}'
                                download = requests.get(url, timeout=3)

                                if download.status_code == 200:
                                    conn.storeFile(self.smb_share, f'{self.smb_path}{file}', io.BytesIO(download.content))
                                    self.log(f'Downloaded file {url} to //{self.smb_server_name}/{self.smb_share}/{self.smb_path}{file}')
                                    downloaded_files += 1
                                
                                else:
                                    self.error(f'Unable to download dashcam file {url}, response code: {download.status_code}')
                                    self.notify(f'Unable to download dashcam file {url}, response code: {download.status_code}', title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])

                        conn.close()

                    else:
                        self.error('Failed to connect to SMB server.')
                        self.notify('Failed to connect to SMB server.', title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])

            else:
                self.error(f'Connecting to camera threw error: {vid_list.status_code}')
                self.notify(f'Connecting to camera threw error: {vid_list.status_code}', title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])


        finally:
            self.log(f'Downloaded {downloaded_files} files.')
            self.notify(f'Downloaded {downloaded_files} files.', title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])