import os
import sys
import asyncio
import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.enums import ChatMemberStatus

# ================= GLOBAL =================
BROADCAST_MODE = {}

# ================= LOGGER =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

ref_logger = logging.getLogger("REFERRAL")
ref_logger.setLevel(logging.INFO)
# ========================================

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "PASTE_BOT_TOKEN"
API_ID = int(os.getenv("API_ID") or 123456)
API_HASH = os.getenv("API_HASH") or "PASTE_API_HASH"

MONGO_URL = os.getenv("MONGO_URL") or "PASTE_MONGO_URL"

FORCE_CHANNEL_1 = "@payalgamingviralvideo123"
FORCE_CHANNEL_2 = "@payalgamingviralvideo123"

SUPPORT_ID = "@YourSupportUsername"
UPDATE_CHANNEL = "@YourUpdateChannel"

ADMIN_IDS = [6335046711]
# ========================================

# ================= BOT ====================
app = Client(
    "referral_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= DATABASE ===============
mongo = MongoClient(MONGO_URL)
db = mongo["referralbot"]
users = db["users"]

# ================= MENU ===================
def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔗 My referrals"), KeyboardButton("📢 Updates")],
            [KeyboardButton("📜 Rules"), KeyboardButton("🆘 Support")],
            [KeyboardButton("📊 Leaderboard")]
        ],
        resize_keyboard=True
    )

# ================= FORCE JOIN =============
async def is_joined(user_id):
    try:
        ok = (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
        m1 = await app.get_chat_member(FORCE_CHANNEL_1, user_id)
        m2 = await app.get_chat_member(FORCE_CHANNEL_2, user_id)
        return m1.status in ok and m2.status in ok
    except:
        return False

def force_buttons():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Join Channel 1", url=f"https://t.me/{FORCE_CHANNEL_1[1:]}")],
            [InlineKeyboardButton("✅ Join Channel 2", url=f"https://t.me/{FORCE_CHANNEL_2[1:]}")],
            [InlineKeyboardButton("🔄 Joined", callback_data="joined")]
        ]
    )

# ================= HELPERS ================
async def delete_later(msg, sec):
    await asyncio.sleep(sec)
    try:
        await msg.delete()
    except:
        pass

# ================= START ==================
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    uid = message.from_user.id
    args = message.command

    user = users.find_one({"user_id": uid})

    ref_id = 0
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == uid:
                ref_id = 0
        except:
            ref_id = 0

    if not user:
        users.insert_one({
            "user_id": uid,
            "name": message.from_user.first_name or "User",
            "referred_by": ref_id,
            "referrals": 0,
            "joined_confirmed": 0,
            "banned": 0
        })

    if not await is_joined(uid):
        await message.reply(
            "⚠️ Pehle dono channels join karo",
            reply_markup=force_buttons()
        )
        return

    users.update_one(
        {"user_id": uid},
        {"$set": {"joined_confirmed": 1}}
    )

    await message.reply_photo(
        photo="start.png",
        caption="🔥 Referral Tournament Live 🔥",
        reply_markup=main_menu()
    )

# ================= JOINED =================
@app.on_callback_query(filters.regex("^joined$"))
async def joined(client, query):
    uid = query.from_user.id

    if not await is_joined(uid):
        await query.answer("❌ Abhi join nahi hua", show_alert=True)
        return

    user = users.find_one({"user_id": uid})
    if not user or user.get("joined_confirmed") == 1:
        return

    users.update_one({"user_id": uid}, {"$set": {"joined_confirmed": 1}})

    if user.get("referred_by"):
        users.update_one(
            {"user_id": user["referred_by"]},
            {"$inc": {"referrals": 1}}
        )
        ref_logger.info(f"REF | {user['referred_by']} <- {uid}")

    await query.message.delete()
    await start_cmd(client, query.message)

# ================= MENU ===================
@app.on_message(filters.text & filters.private & ~filters.command)
async def menu(client, message):
    uid = message.from_user.id
    text = message.text
    u = users.find_one({"user_id": uid})

    if u.get("banned") == 1:
        return

    if text == "🔗 My referrals":
        me = await client.get_me()
        link = f"https://t.me/{me.username}?start={uid}"
        await message.reply(
            f"🔗 Your Referral Link:\n{link}\n\n👥 Referrals: {u.get('referrals',0)}"
        )

    elif text == "📊 Leaderboard":
        rows = users.find({"banned": 0}).sort("referrals", -1).limit(30)
        msg = "🏆 TOP LEADERBOARD\n\n"
        for i, x in enumerate(rows, 1):
            msg += f"{i}. {x.get('name')} — {x.get('referrals')}\n"
        await message.reply(msg)

    elif text == "📜 Rules":
        await message.reply("• Fake accounts not allowed\n• Force join mandatory")

    elif text == "📢 Updates":
        await message.reply(f"📢 {UPDATE_CHANNEL}")

    elif text == "🆘 Support":
        await message.reply(f"🆘 {SUPPORT_ID}")

# ================= BROADCAST ==============
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_start(client, message):
    if message.from_user.id not in ADMIN_IDS:
        return
    BROADCAST_MODE[message.from_user.id] = True
    await message.reply("📢 Send message to broadcast")

@app.on_message(filters.private & ~filters.command)
async def broadcast_sender(client, message):
    uid = message.from_user.id

    if uid not in ADMIN_IDS:
        return
    if BROADCAST_MODE.get(uid) is not True:
        return

    BROADCAST_MODE.pop(uid, None)

    sent = 0
    failed = 0

    await message.reply("🚀 Broadcasting...")

    async for u in users.find({}, {"user_id": 1}):
        try:
            await message.copy(u["user_id"])
            sent += 1
            await asyncio.sleep(0.5)
        except:
            failed += 1

    await message.reply(f"✅ Done\nSent: {sent}\nFailed: {failed}")

# ================= ADMIN ==================
@app.on_message(filters.command("total") & filters.private)
async def total(_, message):
    if message.from_user.id in ADMIN_IDS:
        await message.reply(f"👥 Total Users: {users.count_documents({})}")

@app.on_message(filters.command("resetlb") & filters.private)
async def reset_lb(_, message):
    if message.from_user.id in ADMIN_IDS:
        users.update_many({}, {"$set": {"referrals": 0}})
        await message.reply("✅ Leaderboard reset")

# ================= RUN ====================
print("🤖 Bot Started Successfully")
app.run()
