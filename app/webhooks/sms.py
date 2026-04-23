from fastapi import FastAPI, HTTPException, Request
from agent.orchestrator import process_reply

app = FastAPI()


@app.post("/webhooks/africastalking/sms")
async def handle_sms(request: Request):
    form = await request.form()

    from_number = form.get("from")
    message_raw = form.get("text")

    if not from_number or not message_raw:
        raise HTTPException(status_code=400, detail="Invalid payload")

    if not isinstance(message_raw, str):
        raise HTTPException(status_code=400, detail="Invalid message type")

    message = message_raw

    print("=== INBOUND SMS ===")
    print(from_number, message)

    try:
        result = process_reply(
            company_name="Ramp",
            reply_text=message,
            recipient="amaremek@gmail.com",
        )
        print("Processed reply:", result.get("analysis"))
    except Exception as e:
        print("Error processing SMS reply:", str(e))
        raise HTTPException(status_code=500, detail="Processing failed")

    return {"status": "processed"}
