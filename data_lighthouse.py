import os
import pexpect

PSW = os.environ["PSW"]


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
        log = s_data.buffer.decode("utf-8").split()

        logs = []
        for line in log:
            logs.append(line.replace("\u001b[32m\u001b[39m\u001b[36m", ""))

        if len(logs) == 4:
            index_data = {"url": logs[2],
                          "CID": logs[3]}
        else:
            index_data = {"url": logs[2],
                          "CID": None}

        return index_data
