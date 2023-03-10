import os
import time
import json
import pyodbc
import uvicorn
import pexpect
import subprocess
import pandas as pd
import all_user_data as ALLUD
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import data_lighthouse as dlh
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

CONEXION_BD = 'DRIVER=' + DRIVER + ';SERVER=tcp:' + SERVER + ';PORT=1433;DATABASE=' + DATABASE + ';UID=' + USERNAME + ';PWD=' + PSW


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

        with pyodbc.connect(CONEXION_BD) as conn:
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
    with pyodbc.connect(CONEXION_BD) as conn:
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


class Proposal(BaseModel):
    ID: str
    DESCRIPCION: str
    REQUERIDO: float
    TITULO: str
    WALLET: str


@app.post("/proposal/")
async def create_proposal(proposal: Proposal):
    count = 0
    with pyodbc.connect(CONEXION_BD) as conn:
        with conn.cursor() as cursor:
            insert_proposal = f"INSERT INTO healthcaredao.dbo.propuestas (ID, DESCRIPCION, REQUERIDO, TITULO, WALLET) VALUES('{proposal.ID}', '{proposal.DESCRIPCION}', {proposal.REQUERIDO}, '{proposal.TITULO}', '{proposal.WALLET}');"
            count = cursor.execute(insert_proposal).rowcount
            conn.commit()

            print(f'Rows inserted: {str(count)}')

    return count


class Form(BaseModel):
    INSTITUCION: str
    WALLET: str
    NOMBRE_PROYECTO: str
    MIN_EDAD: int
    MAX_EDAD: int
    MIN_PESO: int
    MAX_PESO: int
    MIN_ESTATURA: int
    MAX_ESTATURA: int
    PAIS: str
    GENERO: str
    TIME_STAMP: int
    ID_QUERY: int


@app.post("/form/")
async def create_proposal(form: Form):
    count = 0
    with pyodbc.connect(CONEXION_BD) as conn:
        with conn.cursor() as cursor:
            insert_proposal = f"INSERT INTO healthcaredao.dbo.acc_data (INSTITUCION, WALLET, NOMBRE_PROYECTO, MIN_EDAD, MAX_EDAD, MIN_PESO, MAX_PESO, MIN_ESTATURA, MAX_ESTATURA, PAIS, GENERO, TIME_STAMP, ID_QUERY) VALUES('{form.INSTITUCION}', '{form.WALLET}', '{form.NOMBRE_PROYECTO}', {form.MIN_EDAD}, {form.MAX_EDAD}, {form.MIN_PESO}, {form.MAX_PESO}, {form.MIN_ESTATURA}, {form.MAX_ESTATURA}, '{form.PAIS}', '{form.GENERO}', '{form.TIME_STAMP}', {form.ID_QUERY});"
            count = cursor.execute(insert_proposal).rowcount
            conn.commit()

            print(f'Rows inserted: {str(count)}')

    return count


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


@app.get("/query_proposal/")
async def query_proposal(wallet: str):
    """
    This function download and decrypt data from users
    :param wallet: str, project wallet
    :return: json object with user data and data dencrypted
    """
    with pyodbc.connect(CONEXION_BD) as conn:
        query_user = f"SELECT TOP 1 * FROM healthcaredao.dbo.acc_data WHERE WALLET = '{wallet}' ORDER BY 'ID_QUERY' ;"
        df_user = pd.DataFrame(pd.read_sql(query_user, conn))

    time_stamp = datetime.timestamp(datetime.now())
    # df_user = df_user[df_user["TIME_STAMP"] <= time_stamp]

    MIN_EDAD = int(df_user["MIN_EDAD"].iloc[0])
    MAX_EDAD = int(df_user["MAX_EDAD"].iloc[0])
    MIN_PESO = int(df_user["MIN_PESO"].iloc[0])
    MAX_PESO = int(df_user["MAX_PESO"].iloc[0])
    MIN_ESTATURA = int(df_user["MIN_ESTATURA"].iloc[0])
    MAX_ESTATURA = int(df_user["MAX_ESTATURA"].iloc[0])
    PAIS = df_user["PAIS"].iloc[0]
    GENERO = df_user["GENERO"].iloc[0]

    with pyodbc.connect(CONEXION_BD) as conn:
        query_data = f"SELECT * FROM healthcaredao.dbo.demograficos WHERE EDAD >= {MIN_EDAD} AND EDAD <= {MAX_EDAD} AND ESTATURA >= {MIN_ESTATURA} AND ESTATURA <= {MAX_ESTATURA} AND PESO >= {MIN_PESO} AND PESO <= {MAX_PESO} AND LOCALIZACION = '{PAIS}' AND GENERO = '{GENERO}';"
        df_user_filter = pd.DataFrame(pd.read_sql(query_data, conn))

    tuple_w = tuple(df_user_filter["ID"])
    if len(tuple_w) == 1:
        str_w = str(tuple_w[0]).replace(",", "")
        str_w = f"= '{str_w}'"

    else:
        str_w = f"IN {str(tuple_w)}"

    dict_users = df_user.to_dict(orient='records')
    json_users = jsonable_encoder(dict_users)

    with pyodbc.connect(CONEXION_BD) as conn:
        query_data = f"SELECT * FROM healthcaredao.dbo.datasensor WHERE USER_DATA {str_w};"
        df_data_filter = pd.DataFrame(pd.read_sql(query_data, conn))

    list_cid = list(df_data_filter["CID"])

    files = []

    for cid in list_cid:
        try:
            file = dlh.lightHouse().download_data_lh(cid=cid)
            files.append(file)
        except:
            pass

    time.sleep(20)

    data = ALLUD.allUserData(folder=FOLDER_D).joint_data()

    json_data = json.loads(data)

    json_data["USER"] = dict(json_users[0])

    return [json_data]


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)
