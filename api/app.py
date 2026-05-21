from fastapi import FastAPI, Request
from pydantic import BaseModel
from tools.router import ToolRouter
from db.controller.userController import check_if_user_exist, create_user_from_whatsapp

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

    if data["event"] == "message_received":
        phone = data["sender"]["attendee_specifics"]["phone_number"]
        name = data["sender"]["attendee_name"]
        message = data["message"]

        exist, user_id = check_if_user_exist(phone)
        if not exist:
            user_id = create_user_from_whatsapp(phone, name)

        result = router.handle(message, str(user_id))
        print(f"MESSAGE: {message}")
        print(f"RESULT: {result}")
        return {"status": "received", "response": result}

    return {"status": "received"}

@app.post("/chat")
def chat(request: MessageRequest):
    result = router.handle(request.message)
    return result