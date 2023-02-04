import os
import time
import pyodbc
import uvicorn
import pexpect
import subprocess
import pandas as pd
import all_user_data as ALLUD
from fastapi import FastAPI
from datetime import datetime
import data_lighthouse as dlh
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

app = FastAPI()

TOKEN = os.environ["TOKEN"]
PK = os.environ["PK"]
PSW = os.environ["PSW"]
BATCH = os.environ["BATCH"]
SERVER = os.environ["SERVER"]
DRIVER = os.environ["DRIVER"]
DELAY = int(os.environ["DELAY"])
INSTANCE = os.environ["INSTANCE"]
DATABASE = os.environ["DATABASE"]
USERNAME = os.environ["USERNAME"]
FOLDER_D = os.environ["FOLDER_D"]


@app.get("/send_data/")
async def send_data(user: str, bpm: float, spo2: int):
    """
    This function send data to IPFS with AWS endpoint
    :param user: str, user identifier
    :param bpm: float, user data BPM
    :param spo2: int, user SpO2
    :return: json object
    """
    df_sensor = pd.read_csv('temp_data/temp_data.csv', index_col=0)

    date_c = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    date_n = datetime.today().strftime('%Y_%m_%d_%H_%M_%S')

    data = {'BPM': bpm,
            "SPO2": spo2,
            'DATE_C': date_c,
            'USER': user}

    df_data = pd.DataFrame([data])
    df_sensor = pd.concat([df_sensor, df_data], ignore_index=True, axis=0)

    df_ipfs_send = df_sensor[df_sensor["USER"] == user]

    if len(df_ipfs_send) >= int(BATCH):
        path_file = f"temp_data/{user}_{date_n}.csv"
        df_ipfs_send.to_csv(path_file)
        index_data = dlh.lightHouse().send_data_lh(path=path_file)
        os.remove(path_file)

        if index_data.get("url")[0] == " ":
            data["URL"] = index_data.get("url").split()[1]
        else:
            data["URL"] = index_data.get("url")

        if index_data.get("CID") is None:
            data["CID"] = data["URL"].replace("https://files.lighthouse.storage/viewFile/", "")
        else:
            data["CID"] = index_data.get("CID")

        BPM = data.get('BPM')
        SPO2 = data.get('SPO2')
        DATE_C = data.get('DATE_C')
        USER_DATA = data.get('USER')
        URL = data.get('URL')
        CID = data.get('CID')

        with pyodbc.connect(
                'DRIVER=' + DRIVER + ';SERVER=tcp:' + SERVER + ';PORT=1433;DATABASE=' + DATABASE + ';UID=' + USERNAME + ';PWD=' + PSW) as conn:
            with conn.cursor() as cursor:
                count = cursor.execute(
                    f"INSERT INTO {INSTANCE} (BPM, SPO2, DATE_C, USER_DATA, URL, CID) VALUES ({BPM}, {SPO2}, '{DATE_C}', '{USER_DATA}', '{URL}', '{CID}');").rowcount
                conn.commit()
                print(f'Rows inserted: {str(count)}')

        df_sensor = df_sensor.drop(list(df_ipfs_send.index), axis=0)
        df_sensor.to_csv('temp_data/temp_data.csv')

    else:
        df_sensor.to_csv('temp_data/temp_data.csv')

    json_resp = jsonable_encoder(data)

    return JSONResponse(content=json_resp)


@app.get("/get_user_data/")
async def get_user_data(user: str):
    """
    This function returns user data save in lighthouse
    :param user: str, user id
    :return: json object
    """
    with pyodbc.connect(
            'DRIVER=' + DRIVER + ';SERVER=tcp:' + SERVER + ';PORT=1433;DATABASE=' + DATABASE + ';UID=' + USERNAME + ';PWD=' + PSW) as conn:
        sql_query_u = f"SELECT * FROM healthcaredao.dbo.demograficos WHERE ID = '{user}';"
        df_user = pd.DataFrame(pd.read_sql(sql_query_u, conn))

        sql_query_d = f"SELECT * FROM healthcaredao.dbo.datasensor WHERE USER_DATA = '{user}';"
        df_user_data = pd.DataFrame(pd.read_sql(sql_query_d, conn))

    df_all = df_user.merge(df_user_data, how='cross')

    cid_list = list(df_all["CID"])

    files = []
    for cid in cid_list:
        file = dlh.lightHouse().download_data_lh(cid=cid)
        files.append(file)

    time.sleep(30)

    json_data = ALLUD.allUserData(folder=FOLDER_D).joint_data()
    json_user = dict(df_user)

    json_data_e = jsonable_encoder(json_data)
    json_user_e = jsonable_encoder(df_user.to_dict(orient="records"))

    return JSONResponse(content=json_data_e), JSONResponse(content=json_user_e)


@app.get("/import_wallet/")
async def import_wallet(token: str):
    """
    This function query used wallet
    :param token:
    :return:
    """
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
    """
    This function query wallet used
    :return: identifier wallet and blockchain network
    """
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


    #@app.get("/acc_data/")
    #def acc_data()


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)
