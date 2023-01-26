import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/send_data/")
async def send_data(user: str, bpm: float, spo2: int):
    print("Hello FileCoin")
    print(f"{user}, {bpm}, {spo2}")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)