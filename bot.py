import os
import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from fpdf import FPDF
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в Hotels Voucher Bot! 🏨\n\n"
        "Просто пришлите мне данные о бронировании одним сообщением, и я сразу сделаю PDF-ваучер.\n\n"
        "Пример формата:\n"
        "Mercure Warszawa Grand ★★★★\n"
        "Confirmation: R6243158189\n"
        "Address: 28 Krucza Street, Warsaw, Poland, 00-522\n"
        "Phone: 390497620893\n"
        "Check-in: 22 Mar 2026\n"
        "Check-out: 01 Apr 2026\n"
        "Nights: 10 nights\n"
        "Guest names: Vadym Bortnyk\n"
        "Room name: Classic Twin Room\n"
        "Price: 2990$"
    )

async def generate_voucher_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_fill_color(36, 47, 65) # Dark blue
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255) # White
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, txt=data.get("hotel_name", "Hotel Name"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 10, txt=f"Confirmation Number: {data.get('confirmation', 'N/A')}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_text_color(0, 0, 0) # Black

    # Sections helper
    def add_section(title, fields):
        pdf.set_fill_color(36, 47, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, txt=title, ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        for label, value in fields:
            pdf.cell(40, 7, txt=f"{label}:", border=0)
            pdf.cell(0, 7, txt=str(value), ln=True)
        pdf.ln(5)

    add_section("PROPERTY INFORMATION", [
        ("Address", data.get("address", "N/A")),
        ("Phone", data.get("phone", "N/A"))
    ])

    add_section("STAY DETAILS", [
        ("Duration", data.get("nights", "N/A")),
        ("Check-in", data.get("check_in", "N/A")),
        ("Check-out", data.get("check_out", "N/A"))
    ])

    guest_list = data.get("guest_names", "N/A").split("\n")
    guests = [(f"Guest {i+1}", g.strip()) for i, g in enumerate(guest_list) if g.strip()]
    add_section("GUEST INFORMATION", guests)

    add_section("ROOM & SERVICES", [
        ("Room Type", data.get("room_name", "N/A")),
        ("Meal Plan", data.get("meal_plan", "Breakfast included"))
    ])

    add_section("PAYMENT INFORMATION", [
        ("Amount Paid", data.get("price", "N/A"))
    ])

    # Important Information
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, txt="Important Information", ln=True)
    pdf.set_font("Helvetica", "", 10)
    info_text = (
        "• Please present this voucher upon arrival at the hotel.\n"
        "• A valid photo ID and credit card may be required at check-in.\n"
        "• Check-in time is as indicated above. Early check-in is subject to availability.\n"
        "• Late check-out requests should be made directly with the hotel."
    )
    pdf.multi_cell(0, 5, txt=info_text)

    file_path = "voucher.pdf"
    pdf.output(file_path)
    return file_path

def parse_input(text):
    lines = text.strip().split('\n')
    data = {}
    
    # First line is usually the hotel name
    data['hotel_name'] = lines[0].strip()
    
    # Use regex to find key-value pairs
    patterns = {
        'confirmation': r'Confirmation:\s*(.*)',
        'address': r'Address:\s*(.*)',
        'phone': r'Phone:\s*(.*)',
        'check_in': r'Check-in:\s*(.*)',
        'check_out': r'Check-out:\s*(.*)',
        'nights': r'Nights:\s*(.*)',
        'guest_names': r'Guest names:\s*(.*)',
        'room_name': r'Room name:\s*(.*)',
        'meal_plan': r'Meal plan:\s*(.*)',
        'price': r'Price:\s*(.*)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
            
    # Handle multi-line guest names if the regex didn't catch all
    if 'Guest names:' in text:
        guest_section = text.split('Guest names:')[1].split('Room name:')[0].strip()
        data['guest_names'] = guest_section

    return data

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    await update.message.reply_text("Обрабатываю данные и создаю ваучер...")
    
    try:
        data = parse_input(text)
        pdf_path = await generate_voucher_pdf(data)
        
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file, 
                filename=f"Voucher_{data.get('hotel_name', 'Hotel').replace(' ', '_')}.pdf"
            )
        await update.message.reply_text("Ваш ваучер готов! Пришлите новые данные для следующего.")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Произошла ошибка при создании ваучера. Убедитесь, что данные введены верно.")

def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set!")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot is starting with bulk processing mode...")
    app.run_polling()

if __name__ == "__main__":
    main()
