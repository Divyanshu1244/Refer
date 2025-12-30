from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from pymongo import MongoClient
import os

# ================= CONFIG =================
BOT_TOKEN = "8231560346:AAEYH6--lmZyOc3vyb2ju-tPkhDJf05rrvU"
API_ID = 36030323
API_HASH = "1d8fc7e8552f7141d5071f184af921e7"

FORCE_CHANNEL = "@tushar900075"
SUPPORT_ID = "@YourSupportUsername"
UPDATE_CHANNEL = "@YourUpdateChannel"

TOURNAMENT_END = datetime(2025, 1, 10)

# MongoDB URL (Railway variable recommended)
MONGO_URL = os.getenv("MONGO_URL") or "mongodb+srv://sanjublogscom_db_user:Mahakal456@cluster0.cwi48dt.mongodb.net/?appName=Cluster0"
# =========================================

# ================= BOT =================
app = Client(
    "referral_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

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

# ================= FORCE JOIN =================
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
@app.on_message(filters.command("start"))
async def start(_, message):
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
            "referred_by": ref_id,
            "referrals": 0,
            "joined_confirmed": 0
        })

    # force join
    if not await is_joined(uid):
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "📢 Join Channel",
                url=f"https://t.me/{FORCE_CHANNEL[1:]}"
            )]]
        )
        await message.reply(
            "⚠️ Pehle channel join karo.\nJoin ke baad /start dubara dabao.",
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
                total = ref_user["referrals"]

                await app.send_message(
                    user["referred_by"],
                    f"➕ New Referral ({display})\n\n"
                    f"Total Referrals = {total}"
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
    me = await app.get_me()

    if not await is_joined(uid):
        await message.reply("⚠️ Channel join required.")
        return

    if text == "🔗 Refer & Win":
        link = f"https://t.me/{me.username}?start={uid}"
        user = users.find_one({"user_id": uid})
        count = user["referrals"]

        await message.reply(
            f"🔗 Your Referral Link:\n{link}\n\n👥 Referrals: {count}"
        )

    elif text == "📊 Leaderboard":
        rows = users.find().sort("referrals", -1).limit(30)

        msg = "🏆 TOP 30 LEADERBOARD\n\n"
        i = 1
        for u in rows:
            msg += f"{i}. User {u['user_id']} — {u['referrals']}\n"
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
