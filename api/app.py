from fastapi import FastAPI
from pydantic import BaseModel
from tools.router import ToolRouter

app = FastAPI()
router = ToolRouter()

class MessageRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: MessageRequest):
    result = router.handle(request.message)
    return result