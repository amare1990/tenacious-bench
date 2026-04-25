from fastapi import FastAPI

from app.webhooks.email import router as email_router
from app.webhooks.sms import router as sms_router  # assuming sms.py exposes a router

app = FastAPI(title="Conversion Engine API")

# Register webhook routes
app.include_router(email_router)
app.include_router(sms_router)


@app.get("/")
def healthcheck():
    return {"status": "ok"}
