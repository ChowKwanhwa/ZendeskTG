import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket, Comment, User

# Load environment variables
load_dotenv(override=True)  # 添加 override=True 确保覆盖系统环境变量
BOT_TOKEN = os.getenv('Bot_Token')
ZENDESK_EMAIL = os.getenv('Zendesk_Email')
ZENDESK_TOKEN = os.getenv('Zendesk_Token')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Debug log for environment variables
logger.info(f"Loaded environment variables:")
logger.info(f"ZENDESK_EMAIL: {ZENDESK_EMAIL}")

# Initialize Zendesk client with credentials
creds = {
    'email': ZENDESK_EMAIL,
    'token': ZENDESK_TOKEN,
    'subdomain': "superexhelp",
    'oauth_token': ZENDESK_TOKEN  # 使用 oauth_token
}

# Debug log for Zendesk configuration
logger.info(f"Initializing Zendesk client with credentials:")
logger.info(f"Email: {creds['email']}")
logger.info(f"Subdomain: {creds['subdomain']}")

# Initialize Zendesk client
zendesk_client = Zenpy(**creds)

# Add debug logging for authentication details
logger.info("Testing Zendesk connection...")
try:
    # Test the connection by making a simple API call
    test = zendesk_client.users.me()
    logger.info(f"Zendesk connection successful! Logged in as: {test.name}")
    
    # 添加更多的测试
    try:
        # 测试创建用户的权限
        test_user = zendesk_client.users.create_or_update(User(name="Test User", email="test@example.com"))
        logger.info("User creation test successful")
    except Exception as e:
        logger.error(f"User creation test failed: {str(e)}")
        
except Exception as e:
    logger.error(f"Zendesk connection test failed: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    logger.error("Please check:")
    logger.error("1. API token is correct in Zendesk Admin Center")
    logger.error("2. Email address is correct")
    logger.error("3. Account has proper permissions")

# Store user conversation states
user_states = {}

def get_active_ticket(user_id):
    """获取用户的活动工单"""
    if user_id in user_states and user_states[user_id].get('active_ticket'):
        return user_states[user_id]['active_ticket']
    return None

def close_ticket(user_id):
    """关闭用户的活动工单"""
    if user_id in user_states:
        user_states[user_id]['active_ticket'] = None

def start(update: Update, context: CallbackContext):
    """Send a welcome message when the command /start is issued."""
    welcome_message = (
        "Welcome to SuperEx Customer Service! \n\n"
        "How can I help you today? Please describe your issue, and our support team "
        "will get back to you as soon as possible."
    )
    update.message.reply_text(welcome_message)

def handle_message(update: Update, context: CallbackContext):
    """Handle user messages and create Zendesk tickets."""
    user = update.effective_user
    message = update.message.text
    chat_id = update.effective_chat.id

    # 确保消息只在私聊中处理
    if update.effective_chat.type != 'private':
        return

    try:
        # 检查用户是否有活动的工单
        active_ticket = get_active_ticket(user.id)
        
        if active_ticket is None:
            # 没有活动工单，创建新工单
            try:
                # 使用 username，如果没有则使用 first_name
                user_name = f"@{user.username}" if user.username else f"{user.first_name}"
                
                # 创建或更新 Zendesk 用户
                zendesk_user = User(
                    name=user_name,
                    email=f"{user.id}@telegram.user",
                    external_id=str(user.id)
                )
                zendesk_user = zendesk_client.users.create_or_update(zendesk_user)
                logger.info(f"User created/updated in Zendesk: {zendesk_user.id}")

                # 创建新工单
                ticket = Ticket(
                    subject=f"Telegram Support - {user_name}",
                    description=message,
                    requester_id=zendesk_user.id,
                    priority="normal",
                    type="question",
                    tags=["telegram_support", f"telegram_user_{user.id}"]
                )
                
                ticket_audit = zendesk_client.tickets.create(ticket)
                created_ticket = ticket_audit.ticket
                logger.info(f"Created Zendesk ticket: {created_ticket.id}")
                
                # 保存用户状态
                if user.id not in user_states:
                    user_states[user.id] = {
                        'chat_id': chat_id,
                        'active_ticket': None
                    }
                user_states[user.id]['active_ticket'] = {
                    'id': created_ticket.id,
                    'zendesk_user_id': zendesk_user.id
                }
                
                context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "Thank you for your message! Our support team has received your inquiry "
                        f"(Ticket #{created_ticket.id}) and will respond as soon as possible.\n\n"
                        "You can continue sending messages here, they will be added to this ticket. "
                        "To close this ticket and start a new one, use the /close command."
                    )
                )
                
            except Exception as e:
                logger.error(f"Error creating Zendesk ticket: {e}")
                raise
                
        else:
            # 有活动工单，添加评论
            try:
                # 创建评论
                ticket = zendesk_client.tickets(id=active_ticket['id'])
                ticket.comment = Comment(
                    body=message,
                    public=True,
                    author_id=active_ticket['zendesk_user_id']
                )
                zendesk_client.tickets.update(ticket)
                logger.info(f"Added comment to ticket {active_ticket['id']}")
                
                # 确认消息已收到
                context.bot.send_message(
                    chat_id=chat_id,
                    text="✓ Message received and added to your ticket."
                )
                
            except Exception as e:
                logger.error(f"Error adding comment to ticket: {e}")
                context.bot.send_message(
                    chat_id=chat_id,
                    text="Sorry, I couldn't add your message to the ticket. Please try again."
                )
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        context.bot.send_message(
            chat_id=chat_id,
            text="I apologize, but I couldn't process your request at the moment. Please try again later."
        )

def close_command(update: Update, context: CallbackContext):
    """处理关闭工单的命令"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    active_ticket = get_active_ticket(user.id)
    if active_ticket:
        try:
            # 关闭 Zendesk 工单
            ticket = zendesk_client.tickets(id=active_ticket['id'])
            ticket.status = 'closed'
            zendesk_client.tickets.update(ticket)
            
            # 清除活动工单
            close_ticket(user.id)
            
            context.bot.send_message(
                chat_id=chat_id,
                text=f"Ticket #{active_ticket['id']} has been closed. You can start a new conversation at any time."
            )
        except Exception as e:
            logger.error(f"Error closing ticket: {e}")
            context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, I couldn't close your ticket. Please try again."
            )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text="You don't have any active tickets to close."
        )

def main():
    """Start the bot."""
    # Load environment variables
    load_dotenv(override=True)
    
    # Initialize bot
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("close", close_command))
    dispatcher.add_handler(MessageHandler(
        Filters.text & Filters.private & ~Filters.command, 
        handle_message
    ))
    
    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
