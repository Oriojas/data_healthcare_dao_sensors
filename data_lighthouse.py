import os
import time
import pexpect

PSW = os.environ["PSW"]
FOLDER_D = os.environ["FOLDER_D"]


class lightHouse:

    def __init__(self):
        self.light = "lighthouse-web3"

    def send_data_lh(self, path: str):
        s_data = pexpect.spawn(f"{self.light} upload-encrypted {path}", timeout=100)
        s_data.expect("Y/n")
        s_data.sendline("Y")
        s_data.expect("Enter your password:")
        s_data.sendline(f"{PSW}")
        s_data.expect("File Uploaded, visit following url to view content!")
        time.sleep(10)
        log = s_data.buffer.decode("utf-8").split()

        logs = []
        for line in log:
            logs.append(line.replace("\u001b[32m\u001b[39m\u001b[36m", ""))

        print(logs)

        if len(logs) == 4:
            index_data = {"url": logs[2].replace("\u001b[39m", ""),
                          "CID": logs[-1]}
        else:
            index_data = {"url": logs[2].replace("\u001b[39m", ""),
                          "CID": None}

        return index_data

    def download_data_lh(self, cid: str):
        d_data = pexpect.spawn(f"{self.light} decrypt-file {cid}",
                               cwd=FOLDER_D,
                               timeout=100)
        d_data.expect("Enter your password:")
        d_data.sendline(f"{PSW}")
        d_data.expect("Decrypted")
        time.sleep(10)
        log = d_data.before.decode("utf-8")

        print(f"{log}")

        return log.replace("\u001b[92m", "")
