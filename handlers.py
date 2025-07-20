# -*- coding: utf-8 -*-

import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ConversationHandler
from database import Database
from config import ADMIN_IDS, AI_API_CONFIG

logger = logging.getLogger(__name__)

# Conversation states
AI_DESIGN_DESCRIPTION = 1
BOOKING_RECEIPT_UPLOAD = 2

db = Database()

def start(update: Update, context: CallbackContext):
    """Start command handler"""
    user = update.effective_user
    db.add_user(user.id, user.first_name, user.username)
    
    # Check forced subscription
    force_channel = db.get_setting('force_join_channel')
    if force_channel:
        try:
            member = context.bot.get_chat_member(force_channel, user.id)
            if member.status in ['left', 'kicked']:
                keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{force_channel.replace('@', '')}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(
                    "برای استفاده از ربات ابتدا در کانال ما عضو شوید:",
                    reply_markup=reply_markup
                )
                return
        except:
            pass
    
    welcome_message = db.get_setting('welcome_message')
    keyboard = [
        [InlineKeyboardButton("🎨 طراحی طرح تتو با هوش مصنوعی", callback_data='ai_design')],
        [InlineKeyboardButton("📅 رزرو وقت تتو", callback_data='book_appointment')],
        [InlineKeyboardButton("📞 تماس با ما", callback_data='contact')]
    ]
    
    # Add admin panel button for admins
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 پنل مدیریت", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    """Handle inline button presses"""
    query = update.callback_query
    query.answer()
    
    if query.data == 'ai_design':
        start_ai_design(query, context)
    elif query.data == 'book_appointment':
        show_available_slots(query, context)
    elif query.data == 'contact':
        show_contact_info(query, context)
    elif query.data.startswith('book_slot_'):
        slot_id = int(query.data.split('_')[2])
        book_slot(query, context, slot_id)
    elif query.data.startswith('book_discount_'):
        slot_id = int(query.data.split('_')[2])
        book_slot_with_discount(query, context, slot_id)
    elif query.data == 'back_to_main':
        back_to_main_menu(query, context)

def start_ai_design(query, context):
    """Start AI design conversation"""
    query.edit_message_text(
        "لطفاً توضیحات کاملی از طرحی که در ذهن دارید بنویسید:\n\n"
        "مثال‌ها:\n"
        "• یک عقاب با بال‌های باز به سبک بلک ورک\n"
        "• طرح هندسی مثلث‌های متقابل روی مچ دست\n"
        "• یک جمجمه با چشم‌های درخشان به سبک رئالیسم\n"
        "• اژدهای آسیایی حول ساعد دست به سبک ترایبال\n"
        "• کهکشان راه شیری روی پشت دست به سبک دات ورک",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]])
    )
    return AI_DESIGN_DESCRIPTION

def handle_ai_design_description(update: Update, context: CallbackContext):
    """Process AI design description"""
    description = update.message.text
    
    # Show processing message
    processing_msg = update.message.reply_text("در حال ساخت طرح شما... لطفاً چند لحظه صبر کنید.")
    
    # Call AI API (mock implementation - replace with actual API)
    try:
        generated_image_url = call_ai_api(description)
        
        if generated_image_url:
            # Delete processing message
            context.bot.delete_message(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id
            )
            
            # Send generated image with discount offer
            keyboard = [[InlineKeyboardButton("📅 رزرو وقت برای اجرای این طرح (با ۱۰٪ تخفیف)", callback_data='book_appointment_discount')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_photo(
                photo=generated_image_url,
                caption="طرح شما آماده شد! ✨\n\nاگر برای اجرای همین طرح وقت رزرو کنید، ۱۰٪ تخفیف ویژه دریافت خواهید کرد.",
                reply_markup=reply_markup
            )
        else:
            raise Exception("API call failed")
            
    except Exception as e:
        logger.error(f"AI API error: {e}")
        processing_msg.edit_text(
            "متاسفانه در ساخت طرح مشکلی پیش آمد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]])
        )
    
    return ConversationHandler.END

def call_ai_api(description):
    """Call AI API to generate tattoo design with enhanced prompt engineering"""
    api_key = db.get_setting('ai_api_key')
    
    if not api_key:
        logger.warning("AI API key not configured")
        return None
    
    # Enhanced prompt engineering to reduce flower bias
    # Add specific tattoo style constraints and avoid botanical defaults
    enhanced_prompt = construct_tattoo_prompt(description)
    
    # Log the prompt for debugging
    logger.info(f"AI Prompt constructed: {enhanced_prompt}")
    
    # This is a mock implementation
    # Replace with actual AI API call (OpenAI DALL-E, Stability AI, etc.)
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'prompt': enhanced_prompt,
            'n': 1,
            'size': '1024x1024',
            'style': 'vivid',  # For more artistic tattoo-like results
            'quality': 'hd'    # Higher quality for tattoo designs
        }
        
        # Mock response - replace with actual API call
        # response = requests.post(AI_API_CONFIG['api_url'], headers=headers, json=data)
        # if response.status_code == 200:
        #     return response.json()['data'][0]['url']
        
        # For testing, return a placeholder image
        logger.info(f"Mock API call successful for prompt: {enhanced_prompt[:50]}...")
        return "https://via.placeholder.com/512x512.png?text=Generated+Tattoo+Design"
        
    except Exception as e:
        logger.error(f"AI API call failed: {e}")
        return None

def construct_tattoo_prompt(user_description):
    """
    Construct an enhanced tattoo prompt that reduces flower bias
    and focuses on diverse tattoo art styles
    """
    # Clean and analyze user description
    cleaned_description = user_description.strip()
    
    # Check if user specifically wants floral elements
    floral_keywords = ['گل', 'flower', 'rose', 'رز', 'botanical', 'leaf', 'برگ', 'شاخه', 'branch']
    user_wants_floral = any(keyword.lower() in cleaned_description.lower() for keyword in floral_keywords)
    
    # Base tattoo prompt with professional tattoo terminology
    base_prompt = "Professional tattoo design artwork, black ink lineart, tattoo flash style"
    
    # Add the user's description
    main_prompt = f"{base_prompt}, {cleaned_description}"
    
    # Add style constraints to prevent default flowers (only if user didn't request floral)
    if not user_wants_floral:
        anti_floral_constraints = [
            "non-floral design",
            "bold geometric or figurative elements", 
            "traditional tattoo motifs",
            "avoid botanical patterns"
        ]
        constraint_text = ", ".join(anti_floral_constraints)
        main_prompt += f", {constraint_text}"
    
    # Add positive tattoo style guidance
    style_guidance = [
        "high contrast black ink",
        "clean linework", 
        "tattoo stencil ready",
        "professional tattoo art style"
    ]
    
    final_prompt = f"{main_prompt}, {', '.join(style_guidance)}"
    
    # Ensure prompt isn't too long (most APIs have limits)
    if len(final_prompt) > 400:
        # Truncate while keeping essential parts
        essential_parts = f"{base_prompt}, {cleaned_description}, non-floral, professional tattoo art"
        final_prompt = essential_parts[:400]
    
    return final_prompt

def show_available_slots(query, context):
    """Show available appointment slots"""
    slots = db.get_available_slots()
    
    if not slots:
        query.edit_message_text(
            "متاسفانه در حال حاضر زمانی برای رزرو موجود نیست. لطفاً بعداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]])
        )
        return
    
    keyboard = []
    for slot_id, slot_text in slots:
        keyboard.append([InlineKeyboardButton(slot_text, callback_data=f'book_slot_{slot_id}')])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')])
    
    query.edit_message_text(
        "لطفاً یکی از زمان‌های موجود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def book_slot(query, context, slot_id, discount=False):
    """Book an appointment slot"""
    user_id = query.from_user.id
    
    # Get slot information
    slots = db.get_available_slots()
    slot_text = None
    for sid, stext in slots:
        if sid == slot_id:
            slot_text = stext
            break
    
    if not slot_text:
        query.edit_message_text(
            "متاسفانه این زمان دیگر موجود نیست. لطفاً زمان دیگری انتخاب کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]])
        )
        return
    
    # Create reservation
    reservation_id = db.create_reservation(user_id, slot_id)
    context.user_data['current_reservation_id'] = reservation_id
    context.user_data['selected_slot_text'] = slot_text
    
    # Get payment details
    card_number = db.get_setting('card_number')
    card_owner = db.get_setting('card_owner')
    deposit_amount = db.get_setting('deposit_amount')
    
    discount_text = ""
    if discount:
        # Apply 10% discount
        original_amount = int(deposit_amount)
        discounted_amount = int(original_amount * 0.9)
        deposit_amount = str(discounted_amount)
        discount_text = f"\n🎉 تخفیف ۱۰٪ اعمال شد! (از {original_amount} به {discounted_amount} تومان)"
    
    payment_message = f"""شما زمان {slot_text} را انتخاب کردید.

این زمان به مدت ۳۰ دقیقه برای شما رزرو موقت شد.{discount_text}

برای نهایی کردن رزرو، لطفاً مبلغ بیعانه به مقدار {deposit_amount} تومان را به شماره کارت زیر واریز کرده و از رسید پرداخت اسکرین‌شات بگیرید و ارسال کنید:

💳 شماره کارت: {card_number}
👤 صاحب حساب: {card_owner}

لطفاً اسکرین‌شات رسید را در همین چت ارسال کنید."""
    
    query.edit_message_text(
        payment_message,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو رزرو", callback_data='back_to_main')]])
    )
    
    return BOOKING_RECEIPT_UPLOAD

def book_slot_with_discount(query, context, slot_id=None):
    """Book slot with 10% discount after AI design"""
    if slot_id is None:
        # Show available slots for discount booking
        show_available_slots_for_discount(query, context)
    else:
        book_slot(query, context, slot_id, discount=True)

def show_available_slots_for_discount(query, context):
    """Show available slots for discount booking"""
    slots = db.get_available_slots()
    
    if not slots:
        query.edit_message_text(
            "متاسفانه در حال حاضر زمانی برای رزرو موجود نیست. لطفاً بعداً تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]])
        )
        return
    
    keyboard = []
    for slot_id, slot_text in slots:
        keyboard.append([InlineKeyboardButton(f"{slot_text} (با ۱۰٪ تخفیف)", callback_data=f'book_discount_{slot_id}')])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')])
    
    query.edit_message_text(
        "لطفاً یکی از زمان‌های موجود را با ۱۰٪ تخفیف انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_receipt_upload(update: Update, context: CallbackContext):
    """Handle receipt photo upload"""
    if not update.message.photo:
        update.message.reply_text("لطفاً تصویر رسید پرداخت را ارسال کنید.")
        return BOOKING_RECEIPT_UPLOAD
    
    # Get the largest photo
    photo = update.message.photo[-1]
    reservation_id = context.user_data.get('current_reservation_id')
    
    if not reservation_id:
        update.message.reply_text("خطا در پردازش رزرو. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END
    
    # Save receipt photo ID
    db.update_reservation_receipt(reservation_id, photo.file_id)
    
    # Confirm receipt received
    update.message.reply_text("رسید شما دریافت شد. پس از تایید توسط ادمین، رزرو شما نهایی خواهد شد. لطفاً منتظر بمانید.")
    
    # Forward to all admins
    send_receipt_to_admins(context, reservation_id, photo.file_id, update.effective_user)
    
    return ConversationHandler.END

def send_receipt_to_admins(context, reservation_id, photo_file_id, user):
    """Send receipt to all admins for approval"""
    reservation_data = db.get_reservation_by_id(reservation_id)
    
    if not reservation_data:
        return
    
    _, user_id, slot_id, status, receipt_photo_id, pending_time, created_at, slot_text, first_name, username = reservation_data
    
    caption = f"""رسید جدید برای تایید

کاربر: {first_name} (@{username if username else 'بدون نام کاربری'})
شناسه کاربر: {user_id}
زمان انتخابی: {slot_text}"""
    
    keyboard = [
        [
            InlineKeyboardButton("✅ تایید", callback_data=f'approve_reservation_{reservation_id}'),
            InlineKeyboardButton("❌ رد", callback_data=f'reject_reservation_{reservation_id}')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for admin_id in ADMIN_IDS:
        try:
            context.bot.send_photo(
                chat_id=admin_id,
                photo=photo_file_id,
                caption=caption,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Failed to send receipt to admin {admin_id}: {e}")

def show_contact_info(query, context):
    """Show contact information"""
    contact_info = db.get_setting('contact_info')
    
    query.edit_message_text(
        contact_info,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_main')]])
    )

def back_to_main_menu(query, context):
    """Return to main menu"""
    user = query.from_user
    welcome_message = db.get_setting('welcome_message')
    
    keyboard = [
        [InlineKeyboardButton("🎨 طراحی طرح تتو با هوش مصنوعی", callback_data='ai_design')],
        [InlineKeyboardButton("📅 رزرو وقت تتو", callback_data='book_appointment')],
        [InlineKeyboardButton("📞 تماس با ما", callback_data='contact')]
    ]
    
    # Add admin panel button for admins
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("👑 پنل مدیریت", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(welcome_message, reply_markup=reply_markup)

def handle_reservation_approval(update: Update, context: CallbackContext):
    """Handle admin reservation approval/rejection"""
    query = update.callback_query
    query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        return
    
    action, reservation_id = query.data.split('_', 1)[0], int(query.data.split('_')[2])
    reservation_data = db.get_reservation_by_id(reservation_id)
    
    if not reservation_data:
        query.edit_message_caption("خطا: رزرو یافت نشد.")
        return
    
    _, user_id, slot_id, status, receipt_photo_id, pending_time, created_at, slot_text, first_name, username = reservation_data
    
    if action == 'approve':
        db.confirm_reservation(reservation_id)
        
        # Notify user
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=f"✅ رزرو شما برای ساعت {slot_text} با موفقیت تایید و نهایی شد."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
        # Confirm to admin
        query.edit_message_caption(
            caption=f"{query.message.caption}\n\n✅ رزرو تایید شد.",
            reply_markup=None
        )
    
    elif action == 'reject':
        db.reject_reservation(reservation_id)
        
        # Notify user
        try:
            context.bot.send_message(
                chat_id=user_id,
                text="❌ متاسفانه رزرو شما توسط ادمین رد شد. لطفاً برای رزرو مجدد اقدام کنید."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
        # Confirm to admin
        query.edit_message_caption(
            caption=f"{query.message.caption}\n\n❌ رزرو رد شد و زمان آن آزاد گردید.",
            reply_markup=None
        )

def cancel_conversation(update: Update, context: CallbackContext):
    """Cancel current conversation"""
    update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END