"""
ApexTrade Telegram Bot — ربات رسمی اپکس‌ترید
Powered by: FastAPI + Groq + Supabase
Deploy: Railway.app
"""

import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from keyboards import main_menu
from crypto_service import get_coin_price, format_coin_message
from db_service import upsert_user, log_message
from groq_service import get_ai_response

# ========== کلاینت تلگرام (درون main.py) ==========
class TelegramClient:
    def __init__(self):
        self.api = f"https://api.telegram.org/bot{settings.BOT_TOKEN}"

    async def _post(self, method: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self.api}/{method}", json=data)
            return r.json()

    async def send_message(self, chat_id, text, reply_markup=None, parse_mode="HTML", reply_to_message_id=None, disable_web_page_preview=True):
        data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": disable_web_page_preview}
        if reply_markup: data["reply_markup"] = reply_markup
        if reply_to_message_id: data["reply_to_message_id"] = reply_to_message_id
        return await self._post("sendMessage", data)

    async def edit_message(self, chat_id, message_id, text, reply_markup=None):
        data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
        if reply_markup: data["reply_markup"] = reply_markup
        return await self._post("editMessageText", data)

    async def answer_callback(self, callback_query_id, text="", show_alert=False):
        return await self._post("answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text, "show_alert": show_alert})

    async def send_chat_action(self, chat_id, action="typing"):
        return await self._post("sendChatAction", {"chat_id": chat_id, "action": action})

    async def set_webhook(self, url):
        return await self._post("setWebhook", {"url": url, "allowed_updates": ["message", "callback_query"], "drop_pending_updates": True})

    async def set_my_commands(self, commands):
        return await self._post("setMyCommands", {"commands": commands})

app = FastAPI(title="ApexTrade Bot", version="2.0.0")
telegram = TelegramClient()

# ========== مدیریت آپدیت‌های تلگرام ==========
async def handle_update(update: dict):
    try:
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            user = message.get("from", {})
            text = message.get("text", "")

            await upsert_user({"id": user.get("id"), "username": user.get("username"), "first_name": user.get("first_name"), "last_name": user.get("last_name")})
            await log_message(user.get("id"), "text")

            if text == "/start":
                await telegram.send_message(chat_id, "👋 به ربات ApexTrade خوش آمدید!\nلطفاً از منوی زیر استفاده کنید:", reply_markup=main_menu())
            elif text == "/help":
                await telegram.send_message(chat_id, "📖 راهنما:\nاز دکمه‌های منو برای دسترسی به امکانات استفاده کنید.", reply_markup=main_menu())
            elif text == "/price":
                coin_data = await get_coin_price("btc")
                if coin_data:
                    await telegram.send_message(chat_id, format_coin_message(coin_data), reply_markup=main_menu())
                else:
                    await telegram.send_message(chat_id, "⚠️ در دریافت قیمت مشکل پیش آمد.", reply_markup=main_menu())
            else:
                await telegram.send_chat_action(chat_id, "typing")
                reply = await get_ai_response(text, [], user.get("first_name", "کاربر"))
                await telegram.send_message(chat_id, reply, reply_markup=main_menu())

        elif "callback_query" in update:
            query = update["callback_query"]
            chat_id = query["message"]["chat"]["id"]
            message_id = query["message"]["message_id"]
            data = query.get("data")
            await telegram.answer_callback(query["id"])
            if data == "back_main":
                await telegram.edit_message(chat_id, message_id, "منوی اصلی:", reply_markup=main_menu())
            else:
                await telegram.answer_callback(query["id"], "این دکمه هنوز فعال نشده است.", show_alert=False)

    except Exception as e:
        print(f"خطا در handle_update: {e}")

# ========== FastAPI ==========
@app.on_event("startup")
async def startup():
    webhook_url = f"{settings.WEBHOOK_URL}/webhook/{settings.WEBHOOK_SECRET}"
    result = await telegram.set_webhook(webhook_url)
    print(f"✅ Webhook set: {result}")
    await telegram.set_my_commands([
        {"command": "start", "description": "🚀 شروع"},
        {"command": "help", "description": "📖 راهنما"},
        {"command": "price", "description": "💰 قیمت لحظه‌ای"},
        {"command": "ask", "description": "🤖 سوال از هوش مصنوعی"},
    ])

@app.get("/")
async def root():
    return {"status": "🟢 ApexTrade Bot is running", "version": "2.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook/{secret}")
async def webhook(secret: str, request: Request):
    if secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        update = await request.json()
        asyncio.create_task(handle_update(update))
        return JSONResponse({"ok": True})
    except Exception as e:
        print(f"Webhook error: {e}")
        return JSONResponse({"ok": False})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
