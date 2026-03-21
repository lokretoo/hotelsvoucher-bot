import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from fpdf import FPDF
from datetime import datetime

# Conversation states
HOTEL_NAME, ADDRESS, PHONE, DURATION, CHECK_IN, CHECK_OUT, GUEST_INFO, ROOM_TYPE, ROOM_VIEW, MEAL_PLAN, AMOUNT_PAID, CONFIRMATION = range(13)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в Hotels Voucher Bot! 🏨\n\n"
        "Я помогу вам с поиском и бронированием отелей.\n\n"
        "Используйте /help для просмотра доступных команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

async def generate_voucher_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, txt=data.get("hotel_name", "Hotel Name"), ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, txt=f"Confirmation Number: R{datetime.now().strftime('%Y%m%d%H%M%S')}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_text_color(0, 0, 0) # Black
    pdf.set_font("Arial", "B", 12)

    # Property Information
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, pdf.get_y(), 210, 10, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.cell(0, 10, txt="PROPERTY INFORMATION", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0) # Black
    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 7, txt="Address:", border=0)
    pdf.cell(0, 7, txt=data.get("address", "N/A"), ln=True)
    pdf.cell(40, 7, txt="Phone:", border=0)
    pdf.cell(0, 7, txt=data.get("phone", "N/A"), ln=True)
    pdf.ln(5)

    # Stay Details
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, pdf.get_y(), 210, 10, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="STAY DETAILS", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0) # Black
    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 7, txt="Duration:", border=0)
    pdf.cell(0, 7, txt=data.get("duration", "N/A"), ln=True)
    pdf.cell(40, 7, txt="Check-in:", border=0)
    pdf.cell(0, 7, txt=data.get("check_in", "N/A"), ln=True)
    pdf.cell(40, 7, txt="Check-out:", border=0)
    pdf.cell(0, 7, txt=data.get("check_out", "N/A"), ln=True)
    pdf.ln(5)

    # Guest Information
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, pdf.get_y(), 210, 10, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="GUEST INFORMATION", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0) # Black
    pdf.set_font("Arial", "", 10)
    guest_info = data.get("guest_info", "N/A").split(", ")
    for i, guest in enumerate(guest_info):
        pdf.cell(40, 7, txt=f"Guest {i+1}:", border=0)
        pdf.cell(0, 7, txt=guest, ln=True)
    pdf.ln(5)

    # Room & Services
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, pdf.get_y(), 210, 10, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="ROOM & SERVICES", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0) # Black
    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 7, txt="Room Type:", border=0)
    pdf.cell(0, 7, txt=data.get("room_type", "N/A"), ln=True)
    pdf.cell(40, 7, txt="Room View:", border=0)
    pdf.cell(0, 7, txt=data.get("room_view", "N/A"), ln=True)
    pdf.cell(40, 7, txt="Meal Plan:", border=0)
    pdf.cell(0, 7, txt=data.get("meal_plan", "N/A"), ln=True)
    pdf.ln(5)

    # Payment Information
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, pdf.get_y(), 210, 10, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="PAYMENT INFORMATION", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0) # Black
    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 7, txt="Amount Paid:", border=0)
    pdf.cell(0, 7, txt=data.get("amount_paid", "N/A"), ln=True)
    pdf.ln(5)

    # Important Information
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt="Important Information", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, txt="\u2022 Please present this voucher upon arrival at the hotel.\n\u2022 A valid photo ID and credit card may be required at check-in.\n\u2022 Check-in time is as indicated above. Early check-in is subject to availability.\n\u2022 Late check-out requests should be made directly with the hotel.")

    file_path = "voucher.pdf"
    pdf.output(file_path)
    return file_path

async def generate_voucher_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Начнём создание ваучера. Пожалуйста, введите название отеля:"
    )
    context.user_data["voucher_data"] = {}
    return HOTEL_NAME

async def get_hotel_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["hotel_name"] = update.message.text
    await update.message.reply_text("Введите адрес отеля:")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["address"] = update.message.text
    await update.message.reply_text("Введите номер телефона отеля:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["phone"] = update.message.text
    await update.message.reply_text("Введите количество ночей (например, 7 nights):")
    return DURATION

async def get_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["duration"] = update.message.text
    await update.message.reply_text("Введите дату заезда (например, 21 Mar 2026):")
    return CHECK_IN

async def get_check_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["check_in"] = update.message.text
    await update.message.reply_text("Введите дату выезда (например, 28 Mar 2026):")
    return CHECK_OUT

async def get_check_out(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["check_out"] = update.message.text
    await update.message.reply_text("Введите информацию о гостях (например, Valerii Sysoev, Galina Sysoeva, 2 Adult):")
    return GUEST_INFO

async def get_guest_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["guest_info"] = update.message.text
    await update.message.reply_text("Введите тип номера (например, Deluxe Twin Room-2 Single beds):")
    return ROOM_TYPE

async def get_room_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["room_type"] = update.message.text
    await update.message.reply_text("Введите вид из номера (например, Pool view):")
    return ROOM_VIEW

async def get_room_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["room_view"] = update.message.text
    await update.message.reply_text("Введите план питания (например, Breakfast included):")
    return MEAL_PLAN

async def get_meal_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["meal_plan"] = update.message.text
    await update.message.reply_text("Введите сумму оплаты (например, 1155$):")
    return AMOUNT_PAID

async def get_amount_paid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["voucher_data"]["amount_paid"] = update.message.text
    data = context.user_data["voucher_data"]
    pdf_path = await generate_voucher_pdf(data)
    await update.message.reply_document(document=open(pdf_path, 'rb'))
    await update.message.reply_text("Ваш ваучер готов!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Создание ваучера отменено.")
    return ConversationHandler.END

if __name__ == "__main__":
    main()
    return ConversationHandler.END

def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set!")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("generate_voucher", generate_voucher_start)],
        states={
            HOTEL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hotel_name)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_duration)],
            CHECK_IN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_check_in)],
            CHECK_OUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_check_out)],
            GUEST_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_guest_info)],
            ROOM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_type)],
            ROOM_VIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_room_view)],
            MEAL_PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_meal_plan)],
            AMOUNT_PAID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount_paid)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()