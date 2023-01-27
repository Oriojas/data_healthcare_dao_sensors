import os
import pyodbc
import uvicorn
import subprocess
from fastapi import FastAPI

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
        wallet = subprocess.run(["lighthouse-web3", "import-wallet", "--key", f"{PK}"],
                                input=b"{PSW}")
    else:
        print("Bad token")
        wallet = None

    return wallet


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)
