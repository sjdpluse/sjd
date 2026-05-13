import asyncio
from telegram import TelegramClient
from config import settings
from keyboards import main_menu
from crypto_service import get_coin_price, format_coin_message
from db_service import upsert_user, log_message
from groq_service import get_ai_response

telegram = TelegramClient()

async def handle_update(update: dict):
    """مدیریت تمام آپدیت‌های تلگرام"""
    try:
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

            # پاسخ به دستورات
            if text == "/start":
                await telegram.send_message(
                    chat_id,
                    "سلام 👋 به ربات ApexTrade خوش آمدید.\nلطفاً از منوی زیر استفاده کنید:",
                    reply_markup=main_menu()
                )
            elif text == "/help":
                await telegram.send_message(chat_id, "راهنما: از دکمه‌های منو استفاده کنید.", reply_markup=main_menu())
            elif text == "/price":
                # مثال: نمایش قیمت بیت‌کوین
                coin_data = await get_coin_price("btc")
                if coin_data:
                    msg = format_coin_message(coin_data)
                    await telegram.send_message(chat_id, msg)
                else:
                    await telegram.send_message(chat_id, "⚠️ خطا در دریافت قیمت.")
            else:
                # پاسخ هوشمند با هوش مصنوعی (اختیاری)
                await telegram.send_chat_action(chat_id, "typing")
                reply = await get_ai_response(text, [], user.get("first_name", "کاربر"))
                await telegram.send_message(chat_id, reply, reply_markup=main_menu())

        elif "callback_query" in update:
            # مدیریت دکمه‌ها (می‌توانید بعداً کامل کنید)
            query = update["callback_query"]
            chat_id = query["message"]["chat"]["id"]
            data = query.get("data")
            await telegram.answer_callback(query["id"])

            if data == "back_main":
                await telegram.edit_message(chat_id, query["message"]["message_id"],
                                            "منوی اصلی:", reply_markup=main_menu())
            # سایر کیبوردها...

    except Exception as e:
        print(f"Error in handle_update: {e}")