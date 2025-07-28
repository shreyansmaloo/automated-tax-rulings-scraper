import os
from ftplib import FTP
from dotenv import load_dotenv

load_dotenv()

FTP_HOST = os.getenv("FTP_HOST")
FTP_PORT = int(os.getenv("FTP_PORT", 21))
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
LOCAL_DIR = os.getenv("LOCAL_DIR", "./downloads")
REMOTE_DIR = os.getenv("REMOTE_DIR")

def upload_and_cleanup():
    ftp = FTP()
    ftp.connect(FTP_HOST, FTP_PORT)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.cwd(REMOTE_DIR)

    for filename in os.listdir(LOCAL_DIR):
        local_path = os.path.join(LOCAL_DIR, filename)
        if os.path.isfile(local_path):
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {filename}", f)
            print(f"Uploaded: {filename}")
            os.remove(local_path)
            print(f"Deleted local: {filename}")

    ftp.quit()
    print("All eligible files uploaded and deleted locally.")
