# Stripped down version of the AppDaemon script that I'm using for testing.

from smb.SMBConnection import SMBConnection
import requests
import re
import io

class BlackVueDashCamDownload():

    def initialize(self):
        # SMB args
        self.smb_server_name = 'truenas.home.domain'
        self.smb_timeout = 30
        self.smb_username = 'michael'
        self.smb_password = 'Grammar1!@'
        self.smb_share = 'blackvue'
        self.smb_path = "Audi/"

        # Other args
        self.dashcam_ip = 'audi-blackvue'
        self.rear_camera = True
        self.video_only = False
        self.days_to_keep = 7

        # Start listening for events
        #self.listen_event(self.download_from_dashcam, self.event_to_listen_for)
        print("DashCamDownload.initialize() complete.")
        self.download_from_dashcam(self)

    def download_from_dashcam(self, **kwargs):
        print(f"Starting DashCam Download for Camera: {self.dashcam_ip}.")

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
                # Clean up results
                trimmed_results = vid_list.text.replace('n:/Record/','').replace('F.mp4,s:1000000','').replace('R.mp4,s:1000000','')
                split_results = trimmed_results.split() # Convert results to list
                split_results.pop(0) # Remove first line

                for filename in split_results:
                    if pattern.match(filename):
                        # Remove parking files
                        continue
                    else:
                        # Continue with good results
                        files_on_camera[f"{filename}F.mp4"] = True

                        if self.video_only == False:
                            files_on_camera[f"{filename}F.thm"] = True
                            files_on_camera[f"{filename}.gps"] = True
                            files_on_camera[f"{filename}.3gf"] = True

                        if self.rear_camera == True:
                            files_on_camera[f"{filename}R.mp4"] = True

                            if self.video_only == False:
                                files_on_camera[f"{filename}R.thm"] = True

                print(f'Found {len(files_on_camera)} files on camera.')

                # Initiate SMB Connection
                with SMBConnection(self.smb_username, self.smb_password, 'hassio.home.domain', self.smb_server_name, use_ntlm_v2=True, is_direct_tcp=True) as conn:
                    connected = conn.connect(self.smb_server_name, port=445)

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
                                    conn.storeFile(self.smb_share, f"{self.smb_path}{file}", io.BytesIO(download.content))
                                    print(f'Downloaded file {url} to //{self.smb_server_name}/{self.smb_share}/{self.smb_path}{file}')
                                    downloaded_files += 1
                                
                                else:
                                    print(f'Unable to download dashcam file {url}, response code: {download.status_code}')

                    else:
                        print('Failed to connect to SMB server.')

            else:
                print(f'Connecting to camera threw error: {vid_list.status_code}')

        finally:
            print(f'Downloaded {downloaded_files} files.')

dashcam = BlackVueDashCamDownload
dashcam.initialize(dashcam)