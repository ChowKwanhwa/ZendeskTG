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
    'subdomain': "superex4871",
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

    # Create or update Zendesk user
    zendesk_user = User(
        name=f"{user.first_name} {user.last_name or ''}".strip(),
        email=f"{user.id}@telegram.user",
        external_id=str(user.id)
    )

    try:
        # Try to find or create the user in Zendesk
        try:
            zendesk_user = zendesk_client.users.create_or_update(zendesk_user)
            logger.info(f"User created/updated in Zendesk: {zendesk_user.id}")
        except Exception as e:
            logger.error(f"Error creating/updating Zendesk user: {e}")
            raise

        # Create Zendesk ticket
        ticket = Ticket(
            subject=f"Telegram Support - {user.first_name}",
            description=message,
            requester_id=zendesk_user.id,
            priority="normal",
            type="question"
        )
        
        created_ticket = zendesk_client.tickets.create(ticket)
        logger.info(f"Created Zendesk ticket: {created_ticket.id}")
        
        # Store ticket ID in user state
        user_states[user.id] = created_ticket.id
        
        update.message.reply_text(
            "Thank you for your message! Our support team has received your inquiry "
            f"(Ticket #{created_ticket.id}) and will respond as soon as possible."
        )
        
    except Exception as e:
        logger.error(f"Error creating Zendesk ticket: {e}")
        update.message.reply_text(
            "I apologize, but I couldn't process your request at the moment. "
            "Please try again later."
        )

def main():
    """Start the bot."""
    # Create the Updater
    updater = Updater(token=BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
