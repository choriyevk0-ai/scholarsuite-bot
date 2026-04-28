import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)
import openai

# ─────────────────────────────────────────────
# CONFIG — Replace these with your real keys!
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ─────────────────────────────────────────────
# CONVERSATION STATES
# ─────────────────────────────────────────────
(
    NAME, COUNTRY, MAJOR, GPA, SAT,
    IELTS, ACTIVITIES, EXTRACURRICULARS,
    PORTFOLIO, BUDGET, SCHOLARSHIP, UNI_TYPE
) = range(12)


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 *Welcome to ScholarSuite Bot!*\n\n"
        "I'm your personal AI university counselor 🤖\n\n"
        "I'll ask you a few questions about your academic background, "
        "personal achievements, and goals — then I'll find the *best universities* "
        "for YOU with official application links! 🌍\n\n"
        "Let's get started! 🚀\n\n"
        "👤 *What is your full name?*",
        parse_mode="Markdown"
    )
    return NAME


# ─────────────────────────────────────────────
# QUESTION HANDLERS
# ─────────────────────────────────────────────
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        f"Nice to meet you, *{context.user_data['name']}*! 🌟\n\n"
        "🌍 *Which countries would you like to study in?*\n"
        "_(e.g. USA, UK, Canada, Germany, Netherlands — you can list multiple)_",
        parse_mode="Markdown"
    )
    return COUNTRY


async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    await update.message.reply_text(
        "📚 *What is your intended major or field of study?*\n"
        "_(e.g. Computer Science, Business, Medicine, Law, Engineering)_",
        parse_mode="Markdown"
    )
    return MAJOR


async def get_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["major"] = update.message.text
    await update.message.reply_text(
        "📊 *What is your GPA?*\n"
        "_(Please specify the scale too, e.g. 3.8/4.0 or 4.5/5.0)_",
        parse_mode="Markdown"
    )
    return GPA


async def get_gpa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gpa"] = update.message.text
    keyboard = [["Yes, I have SAT/ACT", "No SAT/ACT score"]]
    await update.message.reply_text(
        "📝 *Do you have a SAT or ACT score?*",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return SAT


async def get_sat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    if "Yes" in answer:
        await update.message.reply_text(
            "Great! *What is your SAT/ACT score?*\n_(e.g. SAT: 1450 or ACT: 32)_",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        context.user_data["sat_pending"] = True
        return SAT
    else:
        context.user_data["sat"] = "Not taken"
        return await ask_ielts(update, context)


async def get_sat_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("sat_pending"):
        context.user_data["sat"] = update.message.text
        context.user_data["sat_pending"] = False
        return await ask_ielts(update, context)


async def ask_ielts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["IELTS", "TOEFL", "Duolingo English Test", "No certificate"]]
    await update.message.reply_text(
        "🗣️ *Do you have an English proficiency certificate?*",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return IELTS


async def get_ielts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text
    if answer == "No certificate":
        context.user_data["ielts"] = "No English certificate"
        await update.message.reply_text(
            "🏆 *Tell me about your academic achievements and activities!*\n\n"
            "Include things like:\n"
            "• Academic competitions won\n"
            "• Research projects\n"
            "• Clubs or organizations\n"
            "• Any awards or honors\n\n"
            "_(Write as much as you can — the more detail, the better your matches!)_",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return ACTIVITIES
    else:
        context.user_data["ielts_type"] = answer
        await update.message.reply_text(
            f"*What is your {answer} score?*\n_(e.g. IELTS: 7.5 or TOEFL: 105)_",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        context.user_data["ielts_pending"] = True
        return IELTS


async def get_ielts_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("ielts_pending"):
        cert_type = context.user_data.get("ielts_type", "English certificate")
        context.user_data["ielts"] = f"{cert_type}: {update.message.text}"
        context.user_data["ielts_pending"] = False
        await update.message.reply_text(
            "🏆 *Tell me about your academic achievements and activities!*\n\n"
            "Include things like:\n"
            "• Academic competitions won\n"
            "• Research projects\n"
            "• Clubs or organizations\n"
            "• Any awards or honors\n\n"
            "_(Write as much as you can!)_",
            parse_mode="Markdown"
        )
        return ACTIVITIES


async def handle_sat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("sat_pending"):
        return await get_sat_score(update, context)
    return await get_sat(update, context)


async def handle_ielts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("ielts_pending"):
        return await get_ielts_score(update, context)
    return await get_ielts(update, context)



    context.user_data["activities"] = update.message.text
    await update.message.reply_text(
        "🎨 *Tell me about your personal portfolio & extracurriculars!*\n\n"
        "Include things like:\n"
        "• Volunteering experience\n"
        "• Personal projects or apps you built\n"
        "• Sports achievements\n"
        "• Art, music, or creative work\n"
        "• Leadership roles\n"
        "• Internships or work experience\n\n"
        "_(This helps me find universities that value YOUR unique profile!)_",
        parse_mode="Markdown"
    )
    return EXTRACURRICULARS


async def get_extracurriculars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["extracurriculars"] = update.message.text
    await update.message.reply_text(
        "🌟 *Do you have any special portfolio items?*\n\n"
        "For example:\n"
        "• Published research papers\n"
        "• GitHub projects\n"
        "• Art/design portfolio\n"
        "• Business you started\n"
        "• YouTube channel or blog\n\n"
        "_(Type 'None' if you don't have any yet)_",
        parse_mode="Markdown"
    )
    return PORTFOLIO


async def get_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["portfolio"] = update.message.text
    keyboard = [
        ["Under $10,000/year", "$10,000–$25,000/year"],
        ["$25,000–$50,000/year", "Over $50,000/year"],
        ["Looking for full scholarship only"]
    ]
    await update.message.reply_text(
        "💰 *What is your budget for tuition per year?*",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return BUDGET


async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    keyboard = [
        ["Yes — 100% full scholarship"],
        ["Yes — partial scholarship is fine"],
        ["No scholarship needed"]
    ]
    await update.message.reply_text(
        "🎓 *Are you looking for scholarships?*",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return SCHOLARSHIP


async def get_scholarship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["scholarship"] = update.message.text
    keyboard = [
        ["🏆 Ivy League / Top 10"],
        ["⭐ Top 11–50"],
        ["✅ Top 51–100"],
        ["🌍 Any good university"]
    ]
    await update.message.reply_text(
        "🎯 *What type of universities are you targeting?*",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return UNI_TYPE


async def get_uni_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["uni_type"] = update.message.text
    await update.message.reply_text(
        f"✨ *Perfect, {context.user_data['name']}!*\n\n"
        "🔍 I'm now analyzing your full profile and finding your best university matches...\n\n"
        "This might take a few seconds ⏳",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return await analyze_and_recommend(update, context)


# ─────────────────────────────────────────────
# AI ANALYSIS & RECOMMENDATION
# ─────────────────────────────────────────────
async def analyze_and_recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data

    prompt = f"""
You are ScholarSuite AI, an expert university admissions counselor.

Analyze this student's complete profile and recommend the TOP 5 best-fit universities for them.

=== STUDENT PROFILE ===
Name: {data.get('name')}
Target Countries: {data.get('country')}
Intended Major: {data.get('major')}
GPA: {data.get('gpa')}
SAT/ACT: {data.get('sat', 'Not taken')}
English Certificate: {data.get('ielts', 'None')}
Academic Activities & Achievements: {data.get('activities')}
Extracurriculars & Personal Portfolio: {data.get('extracurriculars')}
Special Portfolio Items: {data.get('portfolio')}
Tuition Budget: {data.get('budget')}
Scholarship Needs: {data.get('scholarship')}
University Type Target: {data.get('uni_type')}
=======================

For each university recommendation, provide:
1. University name and country with flag emoji
2. Why it's a great match for this specific student (be personal and specific)
3. Match percentage based on their profile
4. Estimated tuition per year
5. Available scholarships (name and coverage %)
6. Acceptance rate
7. Notable programs for their major
8. Application deadline
9. Official application link (use the real university apply URL)
10. One specific tip for this student to strengthen their application to this university

Format each university clearly with emojis and make it easy to read in Telegram.
End with a motivational message personalized to the student's name and goals.

Be specific, accurate, and genuinely helpful. Use real universities and real apply links.
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are ScholarSuite AI, a world-class university admissions counselor. You provide accurate, personalized university recommendations with real application links."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )

        result = response.choices[0].message.content

        # Split into chunks if too long for Telegram (4096 char limit)
        if len(result) > 4000:
            chunks = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode="Markdown")
        else:
            await update.message.reply_text(result, parse_mode="Markdown")

        # Follow-up options
        keyboard = [
            ["🔍 Find scholarships only"],
            ["📝 Get essay tips"],
            ["🔄 Start over with new profile"],
            ["📊 Compare 2 universities"]
        ]
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Sorry, something went wrong while analyzing your profile.\n"
            f"Error: {str(e)}\n\n"
            "Please try again with /start"
        )

    return ConversationHandler.END


# ─────────────────────────────────────────────
# /help COMMAND
# ─────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 *ScholarSuite Bot — Help*\n\n"
        "Commands:\n"
        "/start — Start your university search\n"
        "/help — Show this help message\n"
        "/cancel — Cancel current session\n\n"
        "Need support? Visit *scholarsuite.lovable.app*",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────
# /cancel COMMAND
# ─────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Session cancelled.\n\nType /start whenever you're ready to find your dream university! 🎓",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_major)],
            GPA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gpa)],
            SAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sat)],
            IELTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ielts)],
            ACTIVITIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_activities)],
            EXTRACURRICULARS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_extracurriculars)],
            PORTFOLIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_portfolio)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            SCHOLARSHIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_scholarship)],
            UNI_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_uni_type)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))

    print("🚀 ScholarSuite Bot is running!")
    app.run_polling()


if __name__ == "__main__":
    main()
