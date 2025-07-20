# -*- coding: utf-8 -*-

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ConversationHandler
from database import Database
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Admin conversation states
ADMIN_ADD_SLOT = 1
ADMIN_EDIT_SETTING = 2
ADMIN_BROADCAST = 3
ADMIN_SET_API_KEY = 4
ADMIN_EDIT_TEXT = 5

db = Database()

def admin_panel(update: Update, context: CallbackContext):
    """Show admin panel"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    if hasattr(update, 'callback_query'):
        query = update.callback_query
        query.answer()
        message_func = query.edit_message_text
    else:
        message_func = update.message.reply_text
    
    keyboard = [
        [InlineKeyboardButton("⏰ مدیریت ساعات", callback_data='admin_slots')],
        [InlineKeyboardButton("✏️ تنظیمات متن‌ها", callback_data='admin_settings')],
        [InlineKeyboardButton("🎨 مدیریت متون ربات", callback_data='admin_text_management')],
        [InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data='admin_broadcast')],
        [InlineKeyboardButton("🔑 تنظیم کلید API", callback_data='admin_api_key')],
        [InlineKeyboardButton("📊 آمار ربات", callback_data='admin_stats')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_func("👑 پنل مدیریت\n\nیکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=reply_markup)

def admin_slots_menu(update: Update, context: CallbackContext):
    """Show slots management menu"""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن زمان جدید", callback_data='admin_add_slot')],
        [InlineKeyboardButton("🗑 حذف زمان", callback_data='admin_delete_slots')],
        [InlineKeyboardButton("📋 مشاهده زمان‌ها", callback_data='admin_view_slots')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("⏰ مدیریت ساعات\n\nیکی از گزینه‌ها را انتخاب کنید:", reply_markup=reply_markup)

def admin_add_slot_start(update: Update, context: CallbackContext):
    """Start adding new slot"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "لطفاً متن زمان جدید را وارد کنید (مثال: چهارشنبه - ۲۵ تیر ۱۴۰۴ - ساعت ۱۴:۰۰):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data='admin_slots')]])
    )
    
    return ADMIN_ADD_SLOT

def admin_add_slot_process(update: Update, context: CallbackContext):
    """Process new slot addition"""
    slot_text = update.message.text
    
    try:
        db.add_slot(slot_text)
        update.message.reply_text(
            f"✅ زمان جدید با موفقیت اضافه شد:\n{slot_text}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_slots')]])
        )
    except Exception as e:
        logger.error(f"Error adding slot: {e}")
        update.message.reply_text(
            "❌ خطا در افزودن زمان. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_slots')]])
        )
    
    return ConversationHandler.END

def admin_view_slots(update: Update, context: CallbackContext):
    """View all slots"""
    query = update.callback_query
    query.answer()
    
    slots = db.get_available_slots()
    
    if not slots:
        query.edit_message_text(
            "هیچ زمانی موجود نیست.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_slots')]])
        )
        return
    
    slots_text = "📋 زمان‌های موجود:\n\n"
    for i, (slot_id, slot_text) in enumerate(slots, 1):
        slots_text += f"{i}. {slot_text}\n"
    
    query.edit_message_text(
        slots_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_slots')]])
    )

def admin_delete_slots(update: Update, context: CallbackContext):
    """Show slots for deletion"""
    query = update.callback_query
    query.answer()
    
    slots = db.get_available_slots()
    
    if not slots:
        query.edit_message_text(
            "هیچ زمانی برای حذف موجود نیست.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_slots')]])
        )
        return
    
    keyboard = []
    for slot_id, slot_text in slots:
        keyboard.append([InlineKeyboardButton(f"🗑 {slot_text}", callback_data=f'delete_slot_{slot_id}')])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='admin_slots')])
    
    query.edit_message_text(
        "انتخاب کنید کدام زمان حذف شود:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def admin_delete_slot_confirm(update: Update, context: CallbackContext):
    """Confirm and delete slot"""
    query = update.callback_query
    query.answer()
    
    slot_id = int(query.data.split('_')[2])
    
    try:
        db.delete_slot(slot_id)
        query.edit_message_text(
            "✅ زمان با موفقیت حذف شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_slots')]])
        )
    except Exception as e:
        logger.error(f"Error deleting slot: {e}")
        query.edit_message_text(
            "❌ خطا در حذف زمان.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_slots')]])
        )

def admin_settings_menu(update: Update, context: CallbackContext):
    """Show settings management menu"""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💬 پیام خوشامدگویی", callback_data='edit_welcome_message')],
        [InlineKeyboardButton("💳 شماره کارت", callback_data='edit_card_number')],
        [InlineKeyboardButton("👤 صاحب حساب", callback_data='edit_card_owner')],
        [InlineKeyboardButton("💰 مبلغ بیعانه", callback_data='edit_deposit_amount')],
        [InlineKeyboardButton("📞 اطلاعات تماس", callback_data='edit_contact_info')],
        [InlineKeyboardButton("📢 کانال اجباری", callback_data='edit_force_channel')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("✏️ تنظیمات متن‌ها\n\nکدام تنظیمات را ویرایش می‌کنید?", reply_markup=reply_markup)

def admin_edit_setting_start(update: Update, context: CallbackContext):
    """Start editing a setting"""
    query = update.callback_query
    query.answer()
    
    setting_key = query.data.replace('edit_', '')
    context.user_data['editing_setting'] = setting_key
    
    # Get current value
    current_value = db.get_setting(setting_key)
    
    setting_names = {
        'welcome_message': 'پیام خوشامدگویی',
        'card_number': 'شماره کارت',
        'card_owner': 'صاحب حساب',
        'deposit_amount': 'مبلغ بیعانه (تومان)',
        'contact_info': 'اطلاعات تماس',
        'force_channel': 'کانال اجباری (@ همراه نام کانال)'
    }
    
    setting_name = setting_names.get(setting_key, setting_key)
    
    query.edit_message_text(
        f"ویرایش {setting_name}\n\nمقدار فعلی:\n{current_value}\n\nمقدار جدید را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data='admin_settings')]])
    )
    
    return ADMIN_EDIT_SETTING

def admin_edit_setting_process(update: Update, context: CallbackContext):
    """Process setting edit"""
    new_value = update.message.text
    setting_key = context.user_data.get('editing_setting')
    
    if not setting_key:
        update.message.reply_text("خطا در پردازش. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    
    try:
        db.set_setting(setting_key, new_value)
        
        setting_names = {
            'welcome_message': 'پیام خوشامدگویی',
            'card_number': 'شماره کارت',
            'card_owner': 'صاحب حساب',
            'deposit_amount': 'مبلغ بیعانه',
            'contact_info': 'اطلاعات تماس',
            'force_channel': 'کانال اجباری'
        }
        
        setting_name = setting_names.get(setting_key, setting_key)
        
        update.message.reply_text(
            f"✅ {setting_name} با موفقیت به‌روزرسانی شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_settings')]])
        )
    except Exception as e:
        logger.error(f"Error updating setting: {e}")
        update.message.reply_text(
            "❌ خطا در به‌روزرسانی تنظیمات.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_settings')]])
        )
    
    return ConversationHandler.END

def admin_broadcast_start(update: Update, context: CallbackContext):
    """Start broadcast message"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "📢 ارسال پیام همگانی\n\nمتن پیام خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data='admin_panel')]])
    )
    
    return ADMIN_BROADCAST

def admin_broadcast_process(update: Update, context: CallbackContext):
    """Process broadcast message"""
    message_text = update.message.text
    
    # Get all users
    users = db.get_all_users()
    
    if not users:
        update.message.reply_text(
            "هیچ کاربری یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]])
        )
        return ConversationHandler.END
    
    # Send progress message
    progress_msg = update.message.reply_text("در حال ارسال پیام...")
    
    sent_count = 0
    failed_count = 0
    
    for user_id in users:
        try:
            context.bot.send_message(chat_id=user_id, text=message_text)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed_count += 1
    
    # Update progress message with results
    progress_msg.edit_text(
        f"📊 نتایج ارسال پیام همگانی:\n\n"
        f"✅ ارسال شده: {sent_count}\n"
        f"❌ ناموفق: {failed_count}\n"
        f"📊 کل: {len(users)}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]])
    )
    
    return ConversationHandler.END

def admin_api_key_start(update: Update, context: CallbackContext):
    """Start API key setting"""
    query = update.callback_query
    query.answer()
    
    current_key = db.get_setting('ai_api_key')
    masked_key = current_key[:8] + "..." if current_key and len(current_key) > 8 else "تنظیم نشده"
    
    query.edit_message_text(
        f"🔑 تنظیم کلید API\n\nکلید فعلی: {masked_key}\n\nکلید API جدید را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data='admin_panel')]])
    )
    
    return ADMIN_SET_API_KEY

def admin_api_key_process(update: Update, context: CallbackContext):
    """Process API key setting"""
    api_key = update.message.text.strip()
    
    try:
        db.set_setting('ai_api_key', api_key)
        update.message.reply_text(
            "✅ کلید API با موفقیت تنظیم شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]])
        )
    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        update.message.reply_text(
            "❌ خطا در تنظیم کلید API.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]])
        )
    
    return ConversationHandler.END

def admin_stats(update: Update, context: CallbackContext):
    """Show bot statistics"""
    query = update.callback_query
    query.answer()
    
    try:
        users_count = len(db.get_all_users())
        available_slots = len(db.get_available_slots())
        
        # Get pending reservations count
        import sqlite3
        conn = sqlite3.connect(db.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM reservations WHERE status = 'pending'")
        pending_reservations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reservations WHERE status = 'confirmed'")
        confirmed_reservations = cursor.fetchone()[0]
        
        conn.close()
        
        stats_text = f"""📊 آمار ربات

👥 تعداد کاربران: {users_count}
⏰ زمان‌های موجود: {available_slots}
⏳ رزروهای در انتظار: {pending_reservations}
✅ رزروهای تایید شده: {confirmed_reservations}"""
        
        query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]])
        )
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        query.edit_message_text(
            "❌ خطا در دریافت آمار.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]])
        )

def admin_text_management(update: Update, context: CallbackContext):
    """Show comprehensive text management menu"""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💬 پیام‌های اصلی", callback_data='admin_main_messages')],
        [InlineKeyboardButton("🎨 متون هوش مصنوعی", callback_data='admin_ai_messages')],
        [InlineKeyboardButton("📅 متون رزرو", callback_data='admin_booking_messages')],
        [InlineKeyboardButton("🔘 متون دکمه‌ها", callback_data='admin_button_texts')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("🎨 مدیریت جامع متون ربات\n\nکدام دسته از متون را ویرایش می‌کنید?", reply_markup=reply_markup)

def admin_main_messages(update: Update, context: CallbackContext):
    """Show main messages editing menu"""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🌟 پیام خوشامدگویی", callback_data='edit_text_welcome_message')],
        [InlineKeyboardButton("📞 اطلاعات تماس", callback_data='edit_text_contact_info')],
        [InlineKeyboardButton("❌ پیام خطای عمومی", callback_data='edit_text_error_general')],
        [InlineKeyboardButton("✅ پیام لغو عملیات", callback_data='edit_text_operation_cancelled')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_text_management')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("💬 ویرایش پیام‌های اصلی", reply_markup=reply_markup)

def admin_ai_messages(update: Update, context: CallbackContext):
    """Show AI messages editing menu"""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("❓ درخواست توضیح طرح", callback_data='edit_text_ai_design_prompt')],
        [InlineKeyboardButton("⏳ پیام در حال پردازش", callback_data='edit_text_ai_design_processing')],
        [InlineKeyboardButton("✨ پیام نتیجه", callback_data='edit_text_ai_design_result')],
        [InlineKeyboardButton("⚠️ پیام خطا", callback_data='edit_text_ai_design_error')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_text_management')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("🎨 ویرایش متون هوش مصنوعی", reply_markup=reply_markup)

def admin_booking_messages(update: Update, context: CallbackContext):
    """Show booking messages editing menu"""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📋 انتخاب زمان", callback_data='edit_text_booking_select_slot')],
        [InlineKeyboardButton("❌ زمان موجود نیست", callback_data='edit_text_booking_no_slots')],
        [InlineKeyboardButton("⚠️ زمان در دسترس نیست", callback_data='edit_text_booking_slot_unavailable')],
        [InlineKeyboardButton("📸 درخواست رسید", callback_data='edit_text_booking_receipt_request')],
        [InlineKeyboardButton("✅ رسید دریافت شد", callback_data='edit_text_booking_receipt_received')],
        [InlineKeyboardButton("✅ رزرو تایید شد", callback_data='edit_text_booking_confirmed')],
        [InlineKeyboardButton("❌ رزرو رد شد", callback_data='edit_text_booking_rejected')],
        [InlineKeyboardButton("💰 انتخاب با تخفیف", callback_data='edit_text_booking_discount_select')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_text_management')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("📅 ویرایش متون رزرو", reply_markup=reply_markup)

def admin_button_texts(update: Update, context: CallbackContext):
    """Show button texts editing menu"""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🎨 دکمه طراحی", callback_data='edit_text_button_ai_design')],
        [InlineKeyboardButton("📅 دکمه رزرو", callback_data='edit_text_button_book_appointment')],
        [InlineKeyboardButton("📞 دکمه تماس", callback_data='edit_text_button_contact')],
        [InlineKeyboardButton("👑 دکمه پنل ادمین", callback_data='edit_text_button_admin_panel')],
        [InlineKeyboardButton("💰 دکمه رزرو با تخفیف", callback_data='edit_text_booking_discount_button')],
        [InlineKeyboardButton("🔙 دکمه بازگشت", callback_data='edit_text_back_button')],
        [InlineKeyboardButton("❌ دکمه لغو", callback_data='edit_text_cancel_button')],
        [InlineKeyboardButton("✅ دکمه تایید ادمین", callback_data='edit_text_admin_approve_button')],
        [InlineKeyboardButton("❌ دکمه رد ادمین", callback_data='edit_text_admin_reject_button')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_text_management')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("🔘 ویرایش متون دکمه‌ها", reply_markup=reply_markup)

def admin_edit_text_start(update: Update, context: CallbackContext):
    """Start editing a specific text"""
    query = update.callback_query
    query.answer()
    
    setting_key = query.data.replace('edit_text_', '')
    context.user_data['editing_text'] = setting_key
    
    # Get current value
    current_value = db.get_setting(setting_key)
    
    text_names = {
        # Main messages
        'welcome_message': 'پیام خوشامدگویی',
        'contact_info': 'اطلاعات تماس',
        'error_general': 'پیام خطای عمومی',
        'operation_cancelled': 'پیام لغو عملیات',
        
        # AI messages
        'ai_design_prompt': 'درخواست توضیح طرح',
        'ai_design_processing': 'پیام در حال پردازش',
        'ai_design_result': 'پیام نتیجه',
        'ai_design_error': 'پیام خطا',
        
        # Booking messages
        'booking_select_slot': 'انتخاب زمان',
        'booking_no_slots': 'زمان موجود نیست',
        'booking_slot_unavailable': 'زمان در دسترس نیست',
        'booking_receipt_request': 'درخواست رسید',
        'booking_receipt_received': 'رسید دریافت شد',
        'booking_confirmed': 'رزرو تایید شد',
        'booking_rejected': 'رزرو رد شد',
        'booking_discount_select': 'انتخاب با تخفیف',
        
        # Button texts
        'button_ai_design': 'دکمه طراحی',
        'button_book_appointment': 'دکمه رزرو',
        'button_contact': 'دکمه تماس',
        'button_admin_panel': 'دکمه پنل ادمین',
        'booking_discount_button': 'دکمه رزرو با تخفیف',
        'back_button': 'دکمه بازگشت',
        'cancel_button': 'دکمه لغو',
        'admin_approve_button': 'دکمه تایید ادمین',
        'admin_reject_button': 'دکمه رد ادمین'
    }
    
    text_name = text_names.get(setting_key, setting_key)
    
    query.edit_message_text(
        f"ویرایش {text_name}\n\nمتن فعلی:\n{current_value}\n\nمتن جدید را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data='admin_text_management')]])
    )
    
    return ADMIN_EDIT_TEXT

def admin_edit_text_process(update: Update, context: CallbackContext):
    """Process text edit"""
    new_value = update.message.text
    setting_key = context.user_data.get('editing_text')
    
    if not setting_key:
        update.message.reply_text("خطا در پردازش. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    
    try:
        db.set_setting(setting_key, new_value)
        
        text_names = {
            # Main messages
            'welcome_message': 'پیام خوشامدگویی',
            'contact_info': 'اطلاعات تماس',
            'error_general': 'پیام خطای عمومی',
            'operation_cancelled': 'پیام لغو عملیات',
            
            # AI messages  
            'ai_design_prompt': 'درخواست توضیح طرح',
            'ai_design_processing': 'پیام در حال پردازش',
            'ai_design_result': 'پیام نتیجه',
            'ai_design_error': 'پیام خطا',
            
            # Booking messages
            'booking_select_slot': 'انتخاب زمان',
            'booking_no_slots': 'زمان موجود نیست',
            'booking_slot_unavailable': 'زمان در دسترس نیست',
            'booking_receipt_request': 'درخواست رسید',
            'booking_receipt_received': 'رسید دریافت شد',
            'booking_confirmed': 'رزرو تایید شد',
            'booking_rejected': 'رزرو رد شد',
            'booking_discount_select': 'انتخاب با تخفیف',
            
            # Button texts
            'button_ai_design': 'دکمه طراحی',
            'button_book_appointment': 'دکمه رزرو',
            'button_contact': 'دکمه تماس',
            'button_admin_panel': 'دکمه پنل ادمین',
            'booking_discount_button': 'دکمه رزرو با تخفیف',
            'back_button': 'دکمه بازگشت',
            'cancel_button': 'دکمه لغو',
            'admin_approve_button': 'دکمه تایید ادمین',
            'admin_reject_button': 'دکمه رد ادمین'
        }
        
        text_name = text_names.get(setting_key, setting_key)
        
        update.message.reply_text(
            f"✅ {text_name} با موفقیت به‌روزرسانی شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_text_management')]])
        )
    except Exception as e:
        logger.error(f"Error updating text setting: {e}")
        update.message.reply_text(
            "❌ خطا در به‌روزرسانی متن.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_text_management')]])
        )
    
    return ConversationHandler.END

def cancel_admin_conversation(update: Update, context: CallbackContext):
    """Cancel admin conversation"""
    update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END