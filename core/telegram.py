"""
کلاینت تلگرام — ارسال پیام، کیبورد، ویرایش و غیره
"""

import httpx
from config import settings

TAPI = settings.TELEGRAM_API


class TelegramClient:
    def __init__(self):
        self.api = TAPI

    async def _post(self, method: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self.api}/{method}", json=data)
            return r.json()

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict = None,
        parse_mode: str = "HTML",
        reply_to_message_id: int = None,
        disable_web_page_preview: bool = True,
    ) -> dict:
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        return await self._post("sendMessage", data)

    async def edit_message(
        self, chat_id, message_id: int, text: str, reply_markup: dict = None
    ) -> dict:
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        return await self._post("editMessageText", data)

    async def answer_callback(self, callback_query_id: str, text: str = "", show_alert: bool = False):
        return await self._post("answerCallbackQuery", {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        })

    async def send_chat_action(self, chat_id, action: str = "typing"):
        return await self._post("sendChatAction", {"chat_id": chat_id, "action": action})

    async def send_photo(self, chat_id, photo: str, caption: str = "", reply_markup: dict = None):
        data = {"chat_id": chat_id, "photo": photo, "caption": caption, "parse_mode": "HTML"}
        if reply_markup:
            data["reply_markup"] = reply_markup
        return await self._post("sendPhoto", data)

    async def set_webhook(self, url: str) -> dict:
        return await self._post("setWebhook", {
            "url": url,
            "allowed_updates": ["message", "callback_query", "my_chat_member"],
            "drop_pending_updates": True,
        })

    async def set_my_commands(self, commands: list[dict]) -> dict:
        return await self._post("setMyCommands", {"commands": commands})

    async def get_me(self) -> dict:
        return await self._post("getMe", {})

    async def copy_message(self, chat_id, from_chat_id, message_id: int) -> dict:
        return await self._post("copyMessage", {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
        })

    async def forward_message(self, chat_id, from_chat_id, message_id: int) -> dict:
        return await self._post("forwardMessage", {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
        })

    async def pin_message(self, chat_id, message_id: int) -> dict:
        return await self._post("pinChatMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
        })

    async def delete_message(self, chat_id, message_id: int) -> dict:
        return await self._post("deleteMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
        })

    async def get_chat_member_count(self, chat_id) -> int:
        r = await self._post("getChatMemberCount", {"chat_id": chat_id})
        return r.get("result", 0)
