import os
import pyodbc
import uvicorn
import pexpect
import subprocess
import pandas as pd
from fastapi import FastAPI
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

app = FastAPI()

TOKEN = os.environ["TOKEN"]
PK = os.environ["PK"]
PSW = os.environ["PSW"]


@app.get("/send_data/")
async def send_data(user: str, bpm: float, spo2: int):
    df_sensor = pd.read_csv('temp_data/temp_data.csv', index_col=0)

    date_c = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    data = {'BPM': bpm,
            "SPO2": spo2,
            'DATE_C': date_c,
            'USER': user}

    df_sensor = df_sensor.append(data, ignore_index=True)

    df_sensor.to_csv('temp_data/temp_data.csv')

    json_resp = jsonable_encoder(data)

    return JSONResponse(content=json_resp)



@app.get("/import_wallet/")
async def import_wallet(token: str):
    if token == TOKEN:
        new_wallet = pexpect.spawn(f"lighthouse-web3 import-wallet --key {PK}")
        new_wallet.expect("Set a password for your wallet:")
        new_wallet.sendline(f"{PSW}")
        new_wallet.expect("Public Key:")
        log = new_wallet.buffer.decode("utf-8").split()

        logs = []
        for line in log:
            logs.append(line)
    else:
        print("Bad token")
        logs = [None]

    return logs[0]


@app.get("/get_wallet/")
async def get_wallet():
    wallet = subprocess.run(["lighthouse-web3", "wallet"],
                            capture_output=True,
                            encoding='UTF-8')
    wallet = str(wallet.stdout).replace("\xa0", "")
    wallet = wallet.split("\n")
    actual_wallet = wallet[0].split(":")[1]
    net = wallet[1].split(":")[1]

    json_resp = jsonable_encoder({"Wallet": actual_wallet,
                                  "net": net})

    return JSONResponse(content=json_resp)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)
