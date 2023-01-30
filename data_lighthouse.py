import subprocess


class lightHouse:

    def __init__(self):
        self.light = "lighthouse-web3"

    def send_data_lh(self, path: str):
        data = subprocess.run([self.light, "upload-encrypted", f"{path}"],
                              capture_output=True,
                              encoding='UTF-8')

        return data
