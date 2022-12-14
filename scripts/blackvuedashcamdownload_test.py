# Stripped down version of the AppDaemon script that I'm using for testing.

from smb.SMBConnection import SMBConnection
import requests
import re
import datetime
import io
import locale

class BlackVueDashCamDownload():

  def initialize(self):
    self.event_to_listen_for = self.args.get("event_to_listen_for", "dashcam_connected")
    self.smb_server_name = self.args.get("smb_server_name")
    self.smb_server_address = self.args.get("smb_server_address", self.smb_server_name)
    self.smb_server_port = self.args.get("smb_server_port", 139)
    self.smb_timeout = self.args.get("smb_timeout", 30)
    self.smb_use_ntlm_v2 = self.args.get("smb_use_ntlm_v2", True)
    self.smb_sign_options = self.args.get("smb_sign_options", 2)
    self.smb_is_direct_tcp = self.args.get("smb_is_direct_tcp", False)
    self.smb_username = self.args.get("smb_username")
    self.smb_password = self.args.get("smb_password")
    self.smb_share = self.args.get("smb_share")
    self.smb_path = self.args.get("smb_path", "/").replace("\\","/")

    self.dashcam_ip = self.args.get("dashcam_ip")
    self.download_videosonly = self.args.get("download_videosonly", True)
    self.rear_camera = self.args.get("rear_camera", False)
    self.days_to_keep = self.args.get("days_to_keep", 30)
    self.notify_title = self.args.get("notify_title")

    self.listen_event(self.download_from_dashcam, self.event_to_listen_for)
    self.log(f"Listening for {self.event_to_listen_for} event")
    self.log("DashCamDownload.initialize() complete")

  def download_from_dashcam(self, event, data, kwargs):
    self.log(f"Starting DashCam Download for Camera: {self.dashcam_ip}")
    self.notify(f"Starting DashCam Download for Camera: {self.dashcam_ip}", title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])

    try:
      url = f"http://{self.dashcam_ip}/blackvue_vod.cgi"
      r = requests.get(url)
      files_on_camera = {}
      existing_files = {}
      files_to_download = []
      files_downloaded = 0
      bytes_to_download = 0
      bytes_downloaded = 0

      if r.status_code == 200:
        content = r.text.replace("n:/Record/","").replace("F.mp4","").replace("R.mp4","").replace(",s:1000000","") # get a list of base filenames from the result
        file_list = content.split("\r\n")
        file_list.pop(0) # remove first line: "v:1.00"

        for f in file_list:
          filename = f.strip()

          if filename == "":
            continue
          elif re.match(r"^(?=.*_P).*$",filename):
            continue
          else:
            pass

          files_on_camera[f"{filename}F.mp4"] = True
          if not self.download_videosonly:
            files_on_camera[f"{filename}F.thm"] = True

          if self.rear_camera:
            files_on_camera[f"{filename}R.mp4"] = True

            if not self.download_videosonly:
              files_on_camera[f"{filename}R.thm"] = True

          if not self.download_videosonly:
            files_on_camera[f"{filename}.gps"] = True
            files_on_camera[f"{filename}.3gf"] = True

        self.log("Initiating connection to SMB server.")
        conn = SMBConnection(self.smb_username, self.smb_password, "hassio.home.domain", self.smb_server_name, use_ntlm_v2=True, is_direct_tcp=True )
        connected = conn.connect(self.smb_server_address, port=445)

        if not connected:
          self.error(f"Unable to connect to {self.smb_server_address}, port = {self.smb_server_port}")
          self.notify(f"Unable to connect to {self.smb_server_address}, port = {self.smb_server_port}", title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])
          return

        self.log(f"Connected to //{self.smb_server_address}/{self.smb_share}")
        self.notify(f"Connected to //{self.smb_server_address}/{self.smb_share}", title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])

        results = conn.listPath(self.smb_share, self.smb_path)
        self.log(f"Found {len(results)} existing files on //{self.smb_server_address}/{self.smb_share}/{self.smb_path}")

        now = datetime.datetime.now()
        epoch = datetime.datetime.utcfromtimestamp(0)
        now_seconds = (now - epoch).total_seconds()

        for r in results:
          if not r.isDirectory:
            age = ((now_seconds - r.last_write_time)/86400)

            if age > self.days_to_keep and not r.filename in files_on_camera:
              conn.deleteFiles(self.smb_share, f"{self.smb_path}/{r.filename}")
            else:
              existing_files[r.filename] = r.file_size

        i = 0
        total = len(files_on_camera)
        self.log(f"Found {total} files on camera to process.")
        for c in files_on_camera:
          i = i + 1
          percent = int((i / total) * 100)
          url = f"http://{self.dashcam_ip}/Record/{c}"
          download = True
          size_on_camera = 0

          if i % 100 == 0:
            self.log(f"Preprocessing: {percent}% complete, {i} of {total}: {c}")

          h = requests.head(url)
          if h.status_code == 204:
            download = False

          if download:
            if 'Content-Length' in h.headers:
              size_on_camera = float(h.headers['Content-Length'])

            if c in existing_files:
                if size_on_camera != existing_files[c]:
                  self.log(f"Redownloading {c}, file size mismatch.  On Camera: {size_on_camera}, On Disk: {existing_files[c]}")
                else:
                  download = False

          if download:
            files_to_download.append(c)
            bytes_to_download = bytes_to_download + size_on_camera

      megabytes = bytes_to_download / 1024.0 / 1024.0
      gigabytes = megabytes / 1024.0
      megabytesstring = locale.format("%.0f", megabytes, grouping=True)
      gigabytesstring = locale.format("%.4f", gigabytes, grouping=True)
      self.log(f"need to download {len(files_to_download):n} files, {gigabytesstring} GB")

      percent = 0
      total = len(files_to_download)
      i = 0
      for f in files_to_download:
        i = i + 1
        url = f"http://{self.dashcam_ip}/Record/{f}"
        d = requests.get(url, timeout = 3)

        if d.status_code == 200:
          conn.storeFile(self.smb_share, f"{self.smb_path}{f}", io.BytesIO(d.content))
          self.log(f"Downloaded new DashCam file {url} to //{self.smb_server_address}/{self.smb_share}/{self.smb_path}{f}, {d.headers['Content-Length']} bytes")
          bytes_downloaded = bytes_downloaded + float(d.headers['Content-Length'])
          files_downloaded = files_downloaded + 1
        else:
          self.log(f"Unable to download DashCam file {url}, response code: {d.status_code}")

        if bytes_to_download > 0:
          percent = int((bytes_downloaded / bytes_to_download) * 100)

        megabytes = bytes_downloaded / 1024.0 / 1024.0
        bytesstring = locale.format("%.0f", megabytes, grouping=True)

        self.log(f"Downloading: {percent}% complete, file {i} of {total}, {bytesstring} MB of {megabytesstring} MB completed")

      megabytes = bytes_downloaded / 1024.0 / 1024.0
      bytesstring = locale.format("%.0f", megabytes, grouping=True)
      self.log(f"Dashcam Completely Copied Successfully, {files_downloaded:n} files, {bytesstring} MB downloaded")
      self.notify(f"Dashcam Completely Copied Successfully, {files_downloaded:n} files, {bytesstring} MB downloaded", title = self.notify_title, name = "home_assistant", target = ["928048749324959824"])

    finally:
      if conn:
        conn.close()

      self.log("Completed.")