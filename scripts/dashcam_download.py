from smb.SMBConnection import SMBConnection
import requests
import re
import datetime
import io
import locale

smb_server_name = 'truenas.home.domain'
smb_server_address = '192.168.0.4'
smb_timeout = 30
smb_username = 'michael'
smb_password = 'Grammar1!@'
smb_share = 'blackvue'
smb_path = 'Audi/'
dashcam_ip = '10.10.200.44'
download_videosonly = True
rear_camera = True
days_to_keep = 30

# Declare vars
pattern = re.compile('^.*_P.*$') # Regex to identify "parking" videos
files_on_camera = {}
existing_files = {}
files_to_download = []
files_downloaded = 0
bytes_to_download = 0
bytes_downloaded = 0

try:
    # Retrieve list of files
    url = f'http://{dashcam_ip}/blackvue_vod.cgi'
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
                files_on_camera[f"{filename}F.thm"] = True
                files_on_camera[f"{filename}R.mp4"] = True
                files_on_camera[f"{filename}R.thm"] = True
                files_on_camera[f"{filename}.gps"] = True
                files_on_camera[f"{filename}.3gf"] = True

        print('Files on camera:', len(files_on_camera))

        # Initiate SMB Connection
        with SMBConnection(smb_username, smb_password, 'hassio.home.domain', smb_server_name, use_ntlm_v2=True, is_direct_tcp=True) as conn:
            connected = conn.connect(smb_server_address, port=445)

            # Get delete date and files on share
            today = datetime.datetime.today()
            delete_before = (today - datetime.timedelta(days = days_to_keep)).timestamp()
            files_in_share = conn.listPath(smb_share, smb_path)

            # Delete old files on share and get dictionary of existing files
            for f in files_in_share:
                if not f.isDirectory:
                    # Check file age
                    if delete_before > f.last_write_time:
                        conn.deleteFiles(smb_share, f'{smb_path}/{f.filename}')
                    else:
                        existing_files[f.filename] = f.file_size

            # Confirm files are available on camera
            i = 0
            total = len(files_on_camera)
            for c in files_on_camera:
                i += 1
                percent = int((i / total) * 100)
                url = f"http://{dashcam_ip}/Record/{c}"
                download = True
                size_on_camera = 0

                if i % 100 == 0:
                    print(f"Preprocessing: {percent}% complete, {i} of {total}: {c}")

                # Check if url is valid
                h = requests.head(url)
                if h.status_code == 200:
                    if 'Content-Length' in h.headers:
                        size_on_camera = float(h.headers['Content-Length'])

                    if c in existing_files:
                        if size_on_camera != existing_files[c]:
                            print(f"Redownloading {c}, file size mismatch.  On Camera: {size_on_camera}, On Disk: {existing_files[c]}")
                        else:
                            download = False
                else:
                    download = False

                if download:
                    files_to_download.append(c)
                    bytes_to_download = bytes_to_download + size_on_camera

            # Do some math to get total amount to download
            megabytes = bytes_to_download / 1024.0 / 1024.0
            gigabytes = megabytes / 1024.0
            megabytesstring = locale.format("%.0f", megabytes, grouping=True)
            gigabytesstring = locale.format("%.4f", gigabytes, grouping=True)
            print(f"need to download {len(files_to_download):n} files, {gigabytesstring} GB")

            percent = 0
            total = len(files_to_download)
            i = 0
            for f in files_to_download:
                i += 1
                url = f"http://{dashcam_ip}/Record/{f}"
                d = requests.get(url, timeout = 3)

                if d.status_code == 200:
                    conn.storeFile(smb_share, f"{smb_path}{f}", io.BytesIO(d.content))
                    print(f"Downloaded new DashCam file {url} to //{smb_server_address}/{smb_share}/{smb_path}{f}, {d.headers['Content-Length']} bytes")
                    bytes_downloaded = bytes_downloaded + float(d.headers['Content-Length'])
                    files_downloaded = files_downloaded + 1
                else:
                    print(f"Unable to download DashCam file {url}, response code: {d.status_code}")

                if bytes_to_download > 0:
                    percent = int((bytes_downloaded / bytes_to_download) * 100)

                megabytes = bytes_downloaded / 1024.0 / 1024.0
                bytesstring = locale.format("%.0f", megabytes, grouping=True)

                print(f"Downloading: {percent}% complete, file {i} of {total}, {bytesstring} MB of {megabytesstring} MB completed")

            megabytes = bytes_downloaded / 1024.0 / 1024.0
            bytesstring = locale.format("%.0f", megabytes, grouping=True)
    
finally:
    print('Transfer complete')