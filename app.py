import re
import aiohttp
import time
import py_mini_racer
import base64
import uvicorn
import websockets
import json
import asyncio
import random
import itertools

from argparse import ArgumentParser
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

class App(FastAPI):

    def __init__(self) -> None:
        super().__init__(title="Kahoot API", openapi_url=None)
        self.add_middleware(CORSMiddleware, allow_origins=["*"])
        self.semaphore = asyncio.Semaphore(10)

    async def connect(self, pin: int, name: str, number: int, namerator: bool = False) -> None:
        try:
            async with self.semaphore:
                async with aiohttp.ClientSession() as session:
                    if namerator:
                        async with session.get("https://apis.kahoot.it/") as response:
                            name = (await response.json(content_type=None))["name"]
                    async with session.get(f"https://play.kahoot.it/reserve/session/{pin}/?{int(time.time() * 1000)}") as response:
                        sessionToken = response.headers["x-kahoot-session-token"]
                        challenge = (await response.json())["challenge"]
                text = re.split("[{};]", challenge.replace("\t", "").encode("ascii", "ignore").decode())
                solChars = [ord(s) for s in py_mini_racer.MiniRacer().eval("".join([text[1] + "{", text[2] + ";", "return message.replace(/./g, function(char, position) {", text[7] + ";})};", text[0]]))]
                sessChars = [ord(s) for s in base64.b64decode(sessionToken).decode()]
                sessionID = "".join([chr(sessChars[i] ^ solChars[i % len(solChars)]) for i in range(len(sessChars))])
                ws = await websockets.connect(f"wss://play.kahoot.it/cometd/{pin}/{sessionID}", open_timeout=None, ping_timeout=None, close_timeout=None)
                await ws.send(json.dumps([{"channel": "/meta/handshake"}]))
                clientID = json.loads(await ws.recv())[0]["clientId"]
                await ws.send(json.dumps([
                    {
                        "channel": "/service/controller",
                        "data": {
                            "type": "login",
                            "gameid": pin,
                            "name": name,
                        },
                        "clientId": clientID,
                    }
                ]))
                await ws.send(json.dumps([
                    {
                        "channel": "/service/controller",
                        "data": {
                            "type": "message",
                            "gameid": pin,
                            "id": 16,
                        },
                        "clientId": clientID,
                    }
                ]))
            while True:
                message = json.loads(await ws.recv())[0]
                if message.get("data", {}).get("id", None) == 2:
                    question = json.loads(message["data"]["content"])
                    if question["type"] == "quiz":
                        await asyncio.sleep(number / 100)
                        await ws.send(json.dumps([
                            {
                                "channel": "/service/controller",
                                "data": {
                                    "type": "message",
                                    "gameid": pin,
                                    "id": 45,
                                    "content": json.dumps({"type": "quiz", "choice": random.randint(0, question["numberOfChoices"] - 1), "questionIndex": question["gameBlockIndex"]})
                                },
                                "clientId": clientID,
                            }
                        ]))
                    elif question["type"] == "multiple_select_quiz":
                        await asyncio.sleep(number / 100)
                        await ws.send(json.dumps([
                            {
                                "channel": "/service/controller",
                                "data": {
                                    "type": "message",
                                    "gameid": pin,
                                    "id": 45,
                                    "content": json.dumps({"type": "multiple_select_quiz", "choice": [random.randint(0, question["numberOfChoices"] - 1)], "questionIndex": question["gameBlockIndex"]})
                                },
                                "clientId": clientID,
                            }
                        ]))
                elif message.get("data", {}).get("id", None) in [10, 13] or message.get("data", {}).get("reason", None) == "disconnect":
                    await ws.close()
        except websockets.ConnectionClosed:
            return
        except:
            if "ws" in locals().keys():
                await ws.close()

app = App()        

@app.post("/flood", response_class=JSONResponse)
async def flood(pin: int = Form(0), naming: str = Form(""), name: str = Form(""), amount: int = Form(0)) -> JSONResponse:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://play.kahoot.it/reserve/session/{pin}/?{int(time.time() * 1000)}") as response:
            if "x-kahoot-session-token" not in response.headers:
                return JSONResponse({"message": "Invalid PIN specified.", "type": "error"}, 400)
    if len(name) < 2 or len(name) > 15:
        return JSONResponse({"message": "Invalid name specified.", "type": "error"}, 400)
    if amount < 1 or amount > 2000:
        return JSONResponse({"message": "Invalid amount specified.", "type": "error"}, 400)
    if naming == "enumerated":
        await asyncio.gather(*[app.connect(pin, f"{name[:15-len(str(i))]}{i}", i) for i in range(amount)])
    elif naming == "capitalized":
        names = list(map(''.join, itertools.product(*zip(name.upper(), name.lower()))))
        await asyncio.gather(*[app.connect(pin, names[i], i) for i in range(amount)])
    elif naming == "random":
        await asyncio.gather(*[app.connect(pin, str(i), i, True) for i in range(amount)])
    else:
        return JSONResponse({"message": "Invalid naming method specified.", "type": "error"}, 400)
    return {"message": "Game finished.", "type": "success"}

if __name__ == "__main__":
    argparser = ArgumentParser()
    argparser.add_argument("--port", "-p", type=int, default=80)
    args = argparser.parse_args()
    uvicorn.run("app:app", host="0.0.0.0", port=args.port)