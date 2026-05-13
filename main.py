"""
ApexTrade Telegram Bot — ربات رسمی اپکس‌ترید
Powered by: FastAPI + Groq + Supabase
Deploy: Railway.app
"""

import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from telegram import TelegramClient
from keyboards import main_menu
from crypto_service import get_coin_price, format_coin_message
from db_service import upsert_user, log_message
from groq_service import get_ai_response

app = FastAPI(title="ApexTrade Bot", version="2.0.0")
telegram = TelegramClient()

# ========== مدیریت آپدیت‌های تلگرام ==========
async def handle_update(update: dict):
    """مسیریابی و پردازش تمام آپدیت‌های تلگرام"""
    try:
        # پیام متنی
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            user = message.get("from", {})
            text = message.get("text", "")

            # ذخیره کاربر در دیتابیس
            await upsert_user({
                "id": user.get("id"),
                "username": user.get("username"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
            })
            await log_message(user.get("id"), "text")

            # پاسخ به کامندها
            if text == "/start":
                await telegram.send_message(chat_id, "👋 به ربات ApexTrade خوش آمدید!\nلطفاً از منوی زیر استفاده کنید:", reply_markup=main_menu())
            elif text == "/help":
                await telegram.send_message(chat_id, "📖 راهنما:\nاز دکمه‌های منو برای دسترسی به امکانات استفاده کنید.", reply_markup=main_menu())
            elif text == "/price":
                coin_data = await get_coin_price("btc")
                if coin_data:
                    msg = format_coin_message(coin_data)
                    await telegram.send_message(chat_id, msg, reply_markup=main_menu())
                else:
                    await telegram.send_message(chat_id, "⚠️ در دریافت قیمت مشکل پیش آمد. لطفاً دقایقی دیگر تلاش کنید.", reply_markup=main_menu())
            else:
                # پاسخ هوشمند با هوش مصنوعی
                await telegram.send_chat_action(chat_id, "typing")
                reply = await get_ai_response(text, [], user.get("first_name", "کاربر"))
                await telegram.send_message(chat_id, reply, reply_markup=main_menu())

        # دکمه‌های اینلاین (callback_query)
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


# ========== راه‌اندازی FastAPI ==========
@app.on_event("startup")
async def startup():
    """ثبت وب‌هوک در استارت‌آپ"""
    webhook_url = f"{settings.WEBHOOK_URL}/webhook/{settings.WEBHOOK_SECRET}"
    result = await telegram.set_webhook(webhook_url)
    print(f"✅ Webhook set: {result}")
    # تنظیم منوی کامندهای ربات
    await telegram.set_my_commands([
        {"command": "start",   "description": "🚀 شروع / خوش آمدید"},
        {"command": "help",    "description": "📖 راهنما و امکانات"},
        {"command": "price",   "description": "💰 قیمت لحظه‌ای کریپتو"},
        {"command": "market",  "description": "📊 نمای کلی بازار"},
        {"command": "course",  "description": "🎓 دوره‌های ApexTrade"},
        {"command": "ask",     "description": "🤖 سوال از هوش مصنوعی"},
        {"command": "news",    "description": "📰 آخرین اخبار کریپتو"},
        {"command": "calc",    "description": "🧮 حساب‌گر P&L و ریسک"},
        {"command": "admin",   "description": "⚙️ پنل مدیریت (ادمین)"},
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
