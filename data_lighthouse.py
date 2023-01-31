import os
import pexpect

PSW = os.environ["PSW"]


class lightHouse:

    def __init__(self):
        self.light = "lighthouse-web3"

    def send_data_lh(self, path: str):
        s_data = pexpect.spawn(f"{self.light} upload-encrypted {path}", timeout=80)
        s_data.expect("Y/n")
        s_data.sendline("Y")
        s_data.expect("Enter your password:")
        s_data.sendline(f"{PSW}")
        s_data.expect("File Uploaded, visit following url to view content!")
        log = s_data.buffer.decode("utf-8").split()

        logs = []
        for line in log:
            logs.append(line)

        index_data = {"url": logs[1],
                      "CID": logs[3]}

        return index_data
