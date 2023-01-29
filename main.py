import os
import pyodbc
import uvicorn
import subprocess
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

app = FastAPI()

TOKEN = os.environ["TOKEN"]
PK = os.environ["PK"]
PSW = os.environ["PSW"]


@app.get("/send_data/")
async def send_data(user: str, bpm: float, spo2: int):
    print("Hello FileCoin")
    print(f"{user}, {bpm}, {spo2}")


@app.get("/import_wallet/")
async def import_wallet(token: str):
    if token == TOKEN:
        new_wallet = subprocess.run(["lighthouse-web3", "import-wallet", "--key", f"{PK}"],
                                    input=b"{PSW}")
    else:
        print("Bad token")
        new_wallet = None

    subprocess.run(["lighthouse-web3", "wallet"])

    return new_wallet


@app.get("/get_wallet/")
async def get_wallet():
    wallet = subprocess.run(["lighthouse-web3", "wallet"], capture_output=True, encoding='UTF-8')
    wallet = str(wallet.stdout).replace("\xa0", "")
    wallet = wallet.split("\n")
    actual_wallet = wallet[0].split(":")[1]
    net = wallet[1].split(":")[1]

    json_resp = jsonable_encoder({"Wallet": actual_wallet,
                                  "net": net})

    return JSONResponse(content=json_resp)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)
