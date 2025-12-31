import os
import asyncio
import logging
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus

# ================= LOGGER =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)
ref_logger = logging.getLogger("REFERRAL")
# =========================================

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8231560346:AAEYH6--lmZyOc3vyb2ju-tPkhDJf05rrvU"
API_ID = int(os.getenv("API_ID") or 36030323)
API_HASH = os.getenv("API_HASH") or "1d8fc7e8552f7141d5071f184af921e7"

MONGO_URL = os.getenv("MONGO_URL") or "mongodb+srv://sanjublogscom_db_user:Mahakal456@cluster0.cwi48dt.mongodb.net/?appName=Cluster0"

FORCE_CHANNEL_1 = "@payalgamingviralvideo123"
FORCE_CHANNEL_2 = "@payalgamingviralvideo123"

SUPPORT_ID = "@YourSupportUsername"
UPDATE_CHANNEL = "@YourUpdateChannel"

ADMIN_IDS = [6335046711]
# =========================================

app = Client(
    "referral_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

mongo = MongoClient(MONGO_URL)
db = mongo["referralbot"]
users = db["users"]

# ================= MENU =================
def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔗 My referrals"), KeyboardButton("📢 Updates")],
            [KeyboardButton("📜 Rules"), KeyboardButton("🆘 Support")],
            [KeyboardButton("📊 Leaderboard")]
        ],
        resize_keyboard=True
    )

# ================= FORCE JOIN =================
async def is_joined(user_id):
    try:
        ok = (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
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

# ================= START HANDLER =================
async def start_handler(client, message):
    uid = message.from_user.id
    args = message.command if hasattr(message, "command") else []

    loading = await message.reply("⏳ Loading...")
    asyncio.create_task(delete_later(loading, 5))

    user = users.find_one({"user_id": uid})

    ref_id = 0
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == uid:
                ref_id = 0
        except:
            ref_id = 0

    name = message.from_user.first_name or "User"

    if not user:
        users.insert_one({
            "user_id": uid,
            "name": name,
            "referred_by": ref_id,
            "referrals": 0,
            "joined_confirmed": 0
        })

    if not await is_joined(uid):
        await message.reply(
            "⚠️ Pehle dono channels join karo.\nJoin ke baad Joined button dabao.",
            reply_markup=force_buttons()
        )
        return

    users.update_one(
        {"user_id": uid},
        {"$set": {"joined_confirmed": 1, "name": name}}
    )

    await message.reply_photo(
        photo="start.png",
        caption=(
            "🔥 *Referral Tournament Live!* 🔥\n\n"
            "👥 Refer friends & win rewards\n"
            "👇 Options niche diye gaye hain"
        ),
        reply_markup=main_menu()
    )

# helper
async def delete_later(msg, sec):
    await asyncio.sleep(sec)
    try:
        await msg.delete()
    except:
        pass

# ================= /START =================
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await start_handler(client, message)

# ================= JOINED BUTTON =================
@app.on_callback_query(filters.regex("^joined$"))
async def joined(client, query):
    uid = query.from_user.id

    if not await is_joined(uid):
        await query.answer("❌ Abhi dono channels join nahi hue", show_alert=True)
        return

    user = users.find_one({"user_id": uid})
    if user and user.get("joined_confirmed", 0) == 0:
        users.update_one({"user_id": uid}, {"$set": {"joined_confirmed": 1}})

        if user.get("referred_by", 0):
            referrer = user["referred_by"]

            users.update_one(
                {"user_id": referrer},
                {"$inc": {"referrals": 1}}
            )

            # ✅ REFERRAL LOGGER
            ref_logger.info(
                f"REF | {referrer} <- {uid} | Total +1"
            )

    try:
        await query.message.delete()
    except:
        pass

    fake = query.message
    fake.command = ["start"]
    await start_handler(client, fake)

# ================= MENU HANDLER =================
@app.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def menu(client, message):
    uid = message.from_user.id
    text = message.text

    if not await is_joined(uid):
        await message.reply(
            "⚠️ Pehle dono channels join karo.\nJoin ke baad Joined button dabao.",
            reply_markup=force_buttons()
        )
        return

    if text == "🔗 My referrals":
        me = await client.get_me()
        link = f"https://t.me/{me.username}?start={uid}"
        u = users.find_one({"user_id": uid})
        await message.reply(f"🔗 Your Referral Link:\n{link}\n\n👥 Referrals: {u.get('referrals',0)}")

    elif text == "📊 Leaderboard":
        rows = users.find().sort("referrals", -1).limit(30)
        msg = "🏆 TOP LEADERBOARD\n\n"
        for i, u in enumerate(rows, 1):
            msg += f"{i}. {u.get('name','User')} — {u.get('referrals',0)}\n"
        await message.reply(msg)

    elif text == "📜 Rules":
        await message.reply("📜 RULES\n\n• Fake accounts not allowed\n• Force join mandatory\n• One user = one account")

    elif text == "📢 Updates":
        await message.reply(f"📢 Updates: {UPDATE_CHANNEL}")

    elif text == "🆘 Support":
        await message.reply(f"🆘 Support: {SUPPORT_ID}")

# ================= ADMIN =================
@app.on_message(filters.command("total") & filters.private)
async def total(_, message):
    if message.from_user.id in ADMIN_IDS:
        await message.reply(f"👥 Total Users: {users.count_documents({})}")

print("🤖 Bot Started Successfully")
app.run()
