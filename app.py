from flask import Flask, request, abort
import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.getenv('YOUR_CHANNEL_ACCESS_TOKEN')
YOUR_CHANNEL_SECRET = os.getenv('YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    print("signature: " + signature)

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print("body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
        print("handler: " + handler.handle(body, signature))
    except InvalidSignatureError:
        print("handler_before: " + handler.handle(body, signature))
        print("Invalid signature. Please check your channel access token/channel secret.")
        print("handler_after: " + handler.handle(body, signature))
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("handle_message:")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

    print("handle_message_after: ", line_bot_api.reply_message(event.reply_token,TextSendMessage(text=event.message.text)))


if __name__ == "__main__":
    app.run()