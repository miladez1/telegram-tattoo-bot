# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import BOT_TOKEN, SCHEDULER_CONFIG
from database import Database
from handlers import (
    start, button_handler, handle_ai_design_description, handle_receipt_upload,
    handle_reservation_approval, cancel_conversation, start_ai_design, back_to_main_menu,
    AI_DESIGN_DESCRIPTION, BOOKING_RECEIPT_UPLOAD
)
from admin_handlers import (
    admin_panel, admin_slots_menu, admin_add_slot_start, admin_add_slot_process,
    admin_view_slots, admin_delete_slots, admin_delete_slot_confirm,
    admin_settings_menu, admin_edit_setting_start, admin_edit_setting_process,
    admin_broadcast_start, admin_broadcast_process, admin_api_key_start,
    admin_api_key_process, admin_stats, cancel_admin_conversation,
    admin_text_management, admin_main_messages, admin_ai_messages, admin_booking_messages,
    admin_button_texts, admin_edit_text_start, admin_edit_text_process,
    ADMIN_ADD_SLOT, ADMIN_EDIT_SETTING, ADMIN_BROADCAST, ADMIN_SET_API_KEY, ADMIN_EDIT_TEXT
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def cleanup_expired_reservations():
    """Clean up expired reservations"""
    db = Database()
    expired_reservations = db.get_expired_reservations(SCHEDULER_CONFIG['reservation_timeout_minutes'])
    
    for reservation_id, slot_id in expired_reservations:
        try:
            db.cancel_expired_reservation(reservation_id, slot_id)
            logger.info(f"Cleaned up expired reservation {reservation_id}")
        except Exception as e:
            logger.error(f"Error cleaning up reservation {reservation_id}: {e}")

def notify_expiring_reservations():
    """Notify users about reservations that will expire soon"""
    from telegram import Bot
    import os
    
    # Get bot token from environment or config
    bot_token = os.getenv('BOT_TOKEN', BOT_TOKEN)
    bot = Bot(token=bot_token)
    
    db = Database()
    near_expiry = db.get_reservations_near_expiry(
        timeout_minutes=SCHEDULER_CONFIG['reservation_timeout_minutes'], 
        warning_minutes=30  # Warn 30 minutes before expiry
    )
    
    for reservation_id, user_id, slot_text, pending_time in near_expiry:
        try:
            # Calculate time remaining
            from datetime import datetime, timedelta
            expiry_time = pending_time + timedelta(minutes=SCHEDULER_CONFIG['reservation_timeout_minutes'])
            time_remaining = expiry_time - datetime.now()
            minutes_remaining = int(time_remaining.total_seconds() / 60)
            
            warning_message = f"""⚠️ هشدار انقضای رزرو

رزرو شما برای زمان {slot_text} در {minutes_remaining} دقیقه دیگر منقضی می‌شود.

اگر هنوز رسید پرداخت را ارسال نکرده‌اید، لطفاً سریع‌تر اقدام کنید تا رزرو شما لغو نشود."""
            
            bot.send_message(chat_id=user_id, text=warning_message)
            db.mark_expiry_warning_sent(reservation_id)
            
            logger.info(f"Sent expiry warning for reservation {reservation_id} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending expiry warning for reservation {reservation_id}: {e}")

def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """Start the bot."""
    # Create updater and pass bot token
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # Initialize database
    db = Database()
    
    # Set up scheduler for cleaning expired reservations
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cleanup_expired_reservations,
        IntervalTrigger(minutes=5),  # Check every 5 minutes
        id='cleanup_expired_reservations'
    )
    scheduler.add_job(
        notify_expiring_reservations,
        IntervalTrigger(minutes=10),  # Check for expiring reservations every 10 minutes
        id='notify_expiring_reservations'
    )
    scheduler.start()

    # AI Design Conversation Handler
    ai_design_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(lambda u, c: start_ai_design(u.callback_query, c), pattern='ai_design')],
        states={
            AI_DESIGN_DESCRIPTION: [
                MessageHandler(Filters.text & ~Filters.command, handle_ai_design_description)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_conversation),
            CallbackQueryHandler(lambda u, c: back_to_main_menu(u.callback_query, c), pattern='back_to_main')
        ]
    )

    # Booking Conversation Handler  
    booking_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(lambda u, c: None, pattern='book_slot_.*')],
        states={
            BOOKING_RECEIPT_UPLOAD: [
                MessageHandler(Filters.photo, handle_receipt_upload),
                MessageHandler(Filters.text & ~Filters.command, handle_receipt_upload)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_conversation),
            CallbackQueryHandler(lambda u, c: back_to_main_menu(u.callback_query, c), pattern='back_to_main')
        ]
    )

    # Admin Conversation Handlers
    admin_add_slot_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_add_slot_start, pattern='admin_add_slot')],
        states={
            ADMIN_ADD_SLOT: [MessageHandler(Filters.text & ~Filters.command, admin_add_slot_process)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_admin_conversation),
            CallbackQueryHandler(lambda u, c: admin_slots_menu(u, c), pattern='admin_slots')
        ]
    )

    admin_edit_setting_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_edit_setting_start, pattern='edit_.*')],
        states={
            ADMIN_EDIT_SETTING: [MessageHandler(Filters.text & ~Filters.command, admin_edit_setting_process)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_admin_conversation),
            CallbackQueryHandler(lambda u, c: admin_settings_menu(u, c), pattern='admin_settings')
        ]
    )

    admin_broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_start, pattern='admin_broadcast')],
        states={
            ADMIN_BROADCAST: [MessageHandler(Filters.text & ~Filters.command, admin_broadcast_process)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_admin_conversation),
            CallbackQueryHandler(lambda u, c: admin_panel(u, c), pattern='admin_panel')
        ]
    )

    admin_api_key_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_api_key_start, pattern='admin_api_key')],
        states={
            ADMIN_SET_API_KEY: [MessageHandler(Filters.text & ~Filters.command, admin_api_key_process)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_admin_conversation),
            CallbackQueryHandler(lambda u, c: admin_panel(u, c), pattern='admin_panel')
        ]
    )

    admin_text_edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_edit_text_start, pattern='edit_text_.*')],
        states={
            ADMIN_EDIT_TEXT: [MessageHandler(Filters.text & ~Filters.command, admin_edit_text_process)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_admin_conversation),
            CallbackQueryHandler(lambda u, c: admin_text_management(u, c), pattern='admin_text_management')
        ]
    )

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))

    # Conversation handlers
    dp.add_handler(ai_design_conv_handler)
    dp.add_handler(booking_conv_handler)
    dp.add_handler(admin_add_slot_handler)
    dp.add_handler(admin_edit_setting_handler)
    dp.add_handler(admin_broadcast_handler)
    dp.add_handler(admin_api_key_handler)
    dp.add_handler(admin_text_edit_handler)

    # Callback query handlers
    dp.add_handler(CallbackQueryHandler(button_handler, pattern='^(book_appointment|contact|book_appointment_discount|back_to_main|book_discount_.*)$'))
    dp.add_handler(CallbackQueryHandler(handle_reservation_approval, pattern='^(approve_reservation_|reject_reservation_).*'))
    dp.add_handler(CallbackQueryHandler(admin_panel, pattern='admin_panel'))
    dp.add_handler(CallbackQueryHandler(admin_slots_menu, pattern='admin_slots'))
    dp.add_handler(CallbackQueryHandler(admin_view_slots, pattern='admin_view_slots'))
    dp.add_handler(CallbackQueryHandler(admin_delete_slots, pattern='admin_delete_slots'))
    dp.add_handler(CallbackQueryHandler(admin_delete_slot_confirm, pattern='delete_slot_.*'))
    dp.add_handler(CallbackQueryHandler(admin_settings_menu, pattern='admin_settings'))
    dp.add_handler(CallbackQueryHandler(admin_stats, pattern='admin_stats'))
    dp.add_handler(CallbackQueryHandler(admin_text_management, pattern='admin_text_management'))
    dp.add_handler(CallbackQueryHandler(admin_main_messages, pattern='admin_main_messages'))
    dp.add_handler(CallbackQueryHandler(admin_ai_messages, pattern='admin_ai_messages'))
    dp.add_handler(CallbackQueryHandler(admin_booking_messages, pattern='admin_booking_messages'))
    dp.add_handler(CallbackQueryHandler(admin_button_texts, pattern='admin_button_texts'))

    # Error handler
    dp.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()
    
    logger.info("Persian Tattoo Bot started successfully!")
    print("🤖 Persian Tattoo Bot is running...")
    print("Press Ctrl+C to stop the bot")

    # Run the bot until you press Ctrl-C
    updater.idle()
    
    # Stop scheduler on exit
    scheduler.shutdown()

if __name__ == '__main__':
    main()