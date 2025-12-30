import os
import asyncio
from datetime import datetime
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "8231560346:AAEYH6--lmZyOc3vyb2ju-tPkhDJf05rrvU"
API_ID = int(os.getenv("API_ID") or 36030323)
API_HASH = os.getenv("API_HASH") or "1d8fc7e8552f7141d5071f184af921e7"

MONGO_URL = os.getenv("MONGO_URL") or "mongodb+srv://sanjublogscom_db_user:Mahakal456@cluster0.cwi48dt.mongodb.net/?appName=Cluster0"

FORCE_CHANNEL = "@tushar900075"
SUPPORT_ID = "@YourSupportUsername"
UPDATE_CHANNEL = "@YourUpdateChannel"
# =========================================

# ================= BOT =================
app = Client(
    "referral_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

BOT_USERNAME = None  # cache

# ================= MONGODB =================
mongo = MongoClient(MONGO_URL)
db = mongo["referralbot"]
users = db["users"]

# ================= MENU =================
def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔗 Refer & Win")],
            [KeyboardButton("📊 Leaderboard")],
            [KeyboardButton("📜 Rules")],
            [KeyboardButton("📢 Updates")],
            [KeyboardButton("🆘 Support")]
        ],
        resize_keyboard=True
    )

# ================= FORCE JOIN (ONLY /start) =================
async def is_joined(user_id):
    try:
        m = await app.get_chat_member(FORCE_CHANNEL, user_id)
        return m.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False

# ================= START =================
@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    global BOT_USERNAME

    if BOT_USERNAME is None:
        BOT_USERNAME = (await app.get_me()).username

    uid = message.from_user.id
    args = message.command

    # instant reply (user feels fast)
    await message.reply("⏳ Loading...")

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
            "referred_by": ref_id,
            "referrals": 0,
            "joined_confirmed": 0
        })

    # force join check ONLY here
    if not await is_joined(uid):
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "📢 Join Channel",
                url=f"https://t.me/{FORCE_CHANNEL[1:]}"
            )]]
        )
        await message.reply(
            "⚠️ Pehle channel join karo.\nJoin ke baad /start dabao.",
            reply_markup=btn
        )
        return

    user = users.find_one({"user_id": uid})

    if user["joined_confirmed"] == 0:
        users.update_one(
            {"user_id": uid},
            {"$set": {"joined_confirmed": 1}}
        )

        if user["referred_by"] != 0:
            users.update_one(
                {"user_id": user["referred_by"]},
                {"$inc": {"referrals": 1}}
            )

            try:
                new_user = message.from_user
                display = f"@{new_user.username}" if new_user.username else (new_user.first_name or "New User")

                ref_user = users.find_one({"user_id": user["referred_by"]})
                total = ref_user.get("referrals", 0)

                await app.send_message(
                    user["referred_by"],
                    f"➕ New Referral ({display})\n\nTotal Referrals = {total}"
                )
            except:
                pass

    await message.reply(
        "🏆 Referral Tournament Active\n\nChoose option below 👇",
        reply_markup=main_menu()
    )

# ================= MENU HANDLER =================
@app.on_message(filters.text & filters.private)
async def menu(_, message):
    uid = message.from_user.id
    text = message.text

    # NO force join check here (important)

    if text == "🔗 Refer & Win":
        user = users.find_one({"user_id": uid})

        if not user:
            users.insert_one({
                "user_id": uid,
                "referred_by": 0,
                "referrals": 0,
                "joined_confirmed": 1
            })
            count = 0
        else:
            count = user.get("referrals", 0)

        link = f"https://t.me/{BOT_USERNAME}?start={uid}"

        await message.reply(
            f"🔗 Your Referral Link:\n{link}\n\n👥 Referrals: {count}"
        )

    elif text == "📊 Leaderboard":
        rows = users.find().sort("referrals", -1).limit(30)

        msg = "🏆 TOP 30 LEADERBOARD\n\n"
        i = 1
        for u in rows:
            msg += f"{i}. User {u['user_id']} — {u.get('referrals', 0)}\n"
            i += 1

        await message.reply(msg)

    elif text == "📜 Rules":
        await message.reply(
            "📜 RULES\n\n"
            "• Fake accounts not allowed\n"
            "• Force join mandatory\n"
            "• One user = one account\n"
            "• Final decision by system"
        )

    elif text == "📢 Updates":
        await message.reply(f"📢 Updates: {UPDATE_CHANNEL}")

    elif text == "🆘 Support":
        await message.reply(f"🆘 Support: {SUPPORT_ID}")

# ================= RUN =================
print("🤖 Bot Started")
app.run()
