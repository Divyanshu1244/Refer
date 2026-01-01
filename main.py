import os
import asyncio
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.enums import ChatMemberStatus

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "PASTE_BOT_TOKEN"
API_ID = int(os.getenv("API_ID") or 36030323)
API_HASH = os.getenv("API_HASH") or "PASTE_API_HASH"

MONGO_URL = os.getenv("MONGO_URL") or "PASTE_MONGO_URL"

# 🔒 SINGLE FORCE SUB (PRIVATE)
FORCE_CHANNEL_ID = -1003582278269
FORCE_INVITE_LINK = "https://t.me/+hpOS9fIEJRkzN2U1"

SUPPORT_ID = "@YourSupportUsername"
UPDATE_CHANNEL = "https://t.me/KHELO_INDIANS"

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
            [KeyboardButton("📍 My Position"), KeyboardButton("📊 Leaderboard")],
            [KeyboardButton("🆘 Support"), KeyboardButton("📜 Rules")]
        ],
        resize_keyboard=True
    )

# ================= FORCE SUB CHECK =================
async def is_joined(user_id: int) -> bool:
    try:
        member = await app.get_chat_member(FORCE_CHANNEL_ID, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        )
    except:
        return False

def force_button():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Join Channel", url=FORCE_INVITE_LINK)],
            [InlineKeyboardButton("🔄 Joined", callback_data="joined")]
        ]
    )

# ================= START =================
@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    uid = message.from_user.id
    name = message.from_user.first_name or "User"
    args = message.command

    user = users.find_one({"user_id": uid})

    if user and user.get("banned"):
        await message.reply("❌ You are banned.")
        return

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
            "name": name,
            "referred_by": ref_id,
            "referrals": 0,
            "banned": False
        })

        if ref_id:
            referrer = users.find_one({"user_id": ref_id})
            if referrer:
                users.update_one({"user_id": ref_id}, {"$inc": {"referrals": 1}})
                try:
                    await app.send_message(
                        ref_id,
                        f"🎉 New Referral!\n👤 {name}\n📊 Total: {referrer.get('referrals',0)+1}"
                    )
                except:
                    pass

    # 🔒 Force Sub
    if not await is_joined(uid):
        await message.reply(
            "⚠️ Pehle channel join karo\nJoin ke baad **Joined** button dabao",
            reply_markup=force_button()
        )
        return

    await message.reply(
        "🔥 Referral Tournament Live!\n\n"
        "👥 Refer friends & win rewards",
        reply_markup=main_menu()
    )

# ================= JOINED CALLBACK =================
@app.on_callback_query(filters.regex("^joined$"))
async def joined(_, query):
    if not await is_joined(query.from_user.id):
        await query.answer("❌ Abhi channel join nahi hua", show_alert=True)
        return

    await query.message.delete()
    fake = query.message
    fake.from_user = query.from_user
    fake.command = ["start"]
    await start(_, fake)

# ================= MENU HANDLER =================
@app.on_message(filters.text & filters.private & ~filters.command)
async def menu(_, message):
    uid = message.from_user.id
    text = message.text

    if not await is_joined(uid):
        await message.reply(
            "⚠️ Channel join karo pehle",
            reply_markup=force_button()
        )
        return

    user = users.find_one({"user_id": uid})

    if text == "🔗 My referrals":
        me = await app.get_me()
        link = f"https://t.me/{me.username}?start={uid}"
        await message.reply(
            f"🔗 Your Link:\n{link}\n\n👥 Referrals: {user.get('referrals',0)}"
        )

    elif text == "📊 Leaderboard":
        rows = users.find({"referrals": {"$gt": 0}}).sort("referrals", -1).limit(20)
        msg = "🏆 LEADERBOARD\n\n"
        for i, u in enumerate(rows, 1):
            msg += f"{i}. {u['name']} — {u['referrals']}\n"
        await message.reply(msg)

    elif text == "📢 Updates":
        await message.reply(f"📢 {UPDATE_CHANNEL}")

    elif text == "📜 Rules":
        await message.reply(
            "📜 RULES\n\n"
            "• Fake IDs not allowed\n"
            "• Force join mandatory\n"
            "• One user = one account"
        )

    elif text == "🆘 Support":
        await message.reply(f"🆘 {SUPPORT_ID}")

# ================= ADMIN =================
@app.on_message(filters.command("total") & filters.private)
async def total(_, message):
    if message.from_user.id in ADMIN_IDS:
        await message.reply(f"👥 Total Users: {users.count_documents({})}")

print("🤖 Bot Started Successfully")
app.run()
