from flask import Flask, request, jsonify
import os
import logging
from dotenv import load_dotenv
import telegram
from telegram.error import TelegramError

app = Flask(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('Bot_Token')
bot = telegram.Bot(token=BOT_TOKEN)

@app.route('/', methods=['GET', 'POST'])
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return jsonify({
            'status': 'ok',
            'message': 'Webhook server is running'
        })
    
    app.logger.info("Received webhook request")
    data = request.get_json()
    app.logger.info(f"Request data: {data}")
    
    try:
        app.logger.info(f"Received webhook data: {data}")
        
        # 处理 Zendesk 事件
        if 'type' in data and data['type'] == 'zen:event-type:ticket.comment_added':
            app.logger.info(f"Processing comment added event")
            
            # 从 detail 获取 ticket 信息
            ticket = data.get('detail', {})
            # 从 event 获取 comment 信息
            comment = data.get('event', {}).get('comment', {})
            
            if ticket and comment:
                app.logger.info(f"Processing ticket {ticket.get('id')} with comment {comment.get('id')}")
                
                # 获取 requester_id（Zendesk 用户 ID）
                requester_id = str(ticket.get('requester_id', ''))
                app.logger.info(f"Requester ID from ticket: {requester_id}")
                
                # 使用 Zendesk API 获取用户信息
                try:
                    from zenpy import Zenpy
                    
                    # 初始化 Zendesk 客户端
                    creds = {
                        'email': os.getenv('Zendesk_Email'),
                        'token': os.getenv('Zendesk_Token'),
                        'subdomain': "superex4871"
                    }
                    zendesk_client = Zenpy(**creds)
                    
                    # 获取用户信息
                    user = zendesk_client.users(id=requester_id)
                    
                    # 确保用户有 external_id（Telegram ID）
                    if not user.external_id:
                        app.logger.error(f"User {requester_id} has no external_id (Telegram ID)")
                        return jsonify({'status': 'error', 'message': 'No Telegram ID found'}), 400
                    
                    telegram_id = user.external_id
                    app.logger.info(f"Found Telegram ID from user external_id: {telegram_id}")
                    
                    # 检查工单标签，确保匹配
                    ticket_tags = ticket.get('tags', [])
                    expected_tag = f"telegram_user_{telegram_id}"
                    if expected_tag not in ticket_tags:
                        app.logger.error(f"Ticket {ticket.get('id')} does not belong to Telegram user {telegram_id}")
                        return jsonify({'status': 'error', 'message': 'Ticket does not belong to user'}), 400
                    
                except Exception as ze:
                    app.logger.error(f"Failed to get user from Zendesk: {ze}")
                    return jsonify({'status': 'error', 'message': str(ze)}), 500
                
                # 检查评论是否来自客服（非 requester）
                comment_author_id = str(comment.get('author', {}).get('id', ''))
                if comment_author_id == requester_id:
                    app.logger.info("Skipping comment from requester")
                    return jsonify({'status': 'success', 'message': 'Skipped requester comment'}), 200
                
                # 准备消息内容
                ticket_id = ticket.get('id', 'Unknown')
                status = ticket.get('status', 'Unknown').lower()
                author_name = comment.get('author', {}).get('name', 'Support Team')
                message = (
                    f"Update for Ticket #{ticket_id}\n"
                    f"Status: {status}\n"
                    f"From: {author_name}\n\n"
                    f"Response:\n"
                    f"{comment.get('body', 'No message content')}"
                )
                
                try:
                    # 发送消息到 Telegram
                    app.logger.info(f"Attempting to send message to Telegram user {telegram_id}")
                    bot.send_message(
                        chat_id=telegram_id,
                        text=message
                    )
                    app.logger.info("Successfully sent message to Telegram")
                except telegram.error.TelegramError as te:
                    app.logger.error(f"Failed to send Telegram message: {te}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to send Telegram message: {str(te)}'
                    }), 500
            
            return jsonify({'status': 'success'}), 200
        
        return jsonify({'status': 'success', 'message': 'Event type not handled'}), 200
        
    except Exception as e:
        app.logger.error(f"Error processing webhook: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # 设置日志级别
    app.logger.setLevel(logging.INFO)
    # 添加文件处理器
    handler = logging.FileHandler('webhook.log')
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    app.run(port=5000)
