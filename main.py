import sqlite3
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus

# ================= CONFIG =================
BOT_TOKEN = "8231560346:AAEYH6--lmZyOc3vyb2ju-tPkhDJf05rrvU"
API_ID = 36030323
API_HASH = "1d8fc7e8552f7141d5071f184af921e7"

FORCE_CHANNEL = "@tushar900075"
SUPPORT_ID = "@YourSupportUsername"
UPDATE_CHANNEL = "@YourUpdateChannel"

TOURNAMENT_END = datetime(2025, 1, 10)  # change date
# =========================================

app = Client(
    "referral_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= DATABASE =================
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referred_by INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    joined_confirmed INTEGER DEFAULT 0
)
""")
conn.commit()

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

    # register user
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    user = cur.fetchone()

    ref_id = 0
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == uid:
                ref_id = 0
        except:
            ref_id = 0

    if not user:
        cur.execute(
            "INSERT INTO users (user_id, referred_by) VALUES (?,?)",
            (uid, ref_id)
        )
        conn.commit()

    # force join
    if not await is_joined(uid):
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL[1:]}")]]
        )
        await message.reply(
            "⚠️ Pehle channel join karo.\nJoin ke baad /start dubara dabao.",
            reply_markup=btn
        )
        return

    # confirm join & referral
cur.execute(
    "SELECT joined_confirmed, referred_by FROM users WHERE user_id=?",
    (uid,)
)
joined, referred_by = cur.fetchone()

if joined == 0:
    # mark joined
    cur.execute(
        "UPDATE users SET joined_confirmed=1 WHERE user_id=?",
        (uid,)
    )

    if referred_by != 0:
        # increment referral
        cur.execute(
            "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
            (referred_by,)
        )

        # -------- LOGGER MESSAGE --------
        try:
            new_user = message.from_user

            if new_user.username:
                display = f"@{new_user.username}"
            else:
                display = new_user.first_name or "New User"

            cur.execute(
                "SELECT referrals FROM users WHERE user_id=?",
                (referred_by,)
            )
            total = cur.fetchone()[0]

            await app.send_message(
                referred_by,
                f"➕ New Referral ({display})\n\n"
                f"Total Referrals = {total}"
            )
        except:
            pass

    conn.commit()

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
        cur.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
        count = cur.fetchone()[0]

        await message.reply(
            f"🔗 Your Referral Link:\n{link}\n\n👥 Referrals: {count}"
        )

    elif text == "📊 Leaderboard":
        cur.execute(
            "SELECT user_id, referrals FROM users ORDER BY referrals DESC LIMIT 30"
        )
        rows = cur.fetchall()

        if not rows:
            await message.reply("No data yet.")
            return

        msg = "🏆 TOP 30 LEADERBOARD\n\n"
        i = 1
        for u, r in rows:
            msg += f"{i}. User {u} — {r}\n"
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
