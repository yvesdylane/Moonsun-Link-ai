from fastapi import FastAPI, Request
from pydantic import BaseModel
from tools.router import ToolRouter

app = FastAPI()
router = ToolRouter()

class MessageRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Server working. Wellcome to moonsu"}

@app.post("/whatsapp")
async def webhook(request: Request):
    data = await request.json()
    if data["event"] == "message_received" :
        print(data["account_info"]["phone_number"])

    return {"status": "received"}

@app.post("/chat")
def chat(request: MessageRequest):
    result = router.handle(request.message)
    return result