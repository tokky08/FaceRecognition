from flask import Flask, request, abort
from linebot.models import ImageMessage
from io import BytesIO
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
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

YOUR_FACE_API_KEY = os.getenv('YOUR_FACE_API_KEY')
YOUR_FACE_API_ENDPOINT = os.getenv('YOUR_FACE_API_ENDPOINT')
face_client = FaceClient(YOUR_FACE_API_ENDPOINT, CognitiveServicesCredentials(YOUR_FACE_API_KEY))

PERSON_GROUP_ID = os.getenv('PERSON_GROUP_ID')
PERSON_ID_HASIKAN = os.getenv('PERSON_ID_HASIKAN')
PERSON_ID_HAMABE = os.getenv('PERSON_ID_HAMABE')

YOUR_CHANNEL_ACCESS_TOKEN = os.getenv('YOUR_CHANNEL_ACCESS_TOKEN')
YOUR_CHANNEL_SECRET = os.getenv('YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


params = {
    "text_list": [],
    "name_list": [],
}


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        print(params["text_list"])
        print(params["name_list"])
        handler.handle(body, signature)
        print(params["text_list"])
        print(params["name_list"])

    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    params["name_list"] = []
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

    params["name_list"].append(event.message.text)

    return event.message.text


@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # text_list = []
    params["text_list"] = []
    try:
        # メッセージIDを受け取る
        message_id = event.message.id
        # メッセージIDに含まれるmessage_contentを抽出する
        message_content = line_bot_api.get_message_content(message_id)
        # contentの画像データをバイナリデータとして扱えるようにする
        image = BytesIO(message_content.content)

        # Detect from streamで顔検出
        detected_faces = face_client.face.detect_with_stream(image)

        # 検出結果に応じて処理を分ける
        if detected_faces != []:
            # 検出された顔の最初のIDを取得
            text = detected_faces[0].face_id

            # 顔検出ができたら顔認証を行う
            valified_hasikan = face_client.face.verify_face_to_person(
                face_id = detected_faces[0].face_id,
                person_group_id = PERSON_GROUP_ID,
                person_id = PERSON_ID_HASIKAN
            )

            print(valified_hasikan)

            valified_hamabe = face_client.face.verify_face_to_person(
                face_id = detected_faces[0].face_id,
                person_group_id = PERSON_GROUP_ID,
                person_id = PERSON_ID_HAMABE
            )

            print(valified_hamabe)

            if valified_hasikan.is_identical:
                text = "この写真は橋本環奈です(score:{:.3f})".format(valified_hasikan.confidence)
            elif valified_hamabe.is_identical:
                text = "この写真は浜辺美波です(score:{:.3f})".format(valified_hamabe.confidence)
            else:
                text = "この写真は誰ですか？学習させるので名前を入力してください！"


            # if text == "この写真は誰ですか？学習させるので名前を入力してください！":
            #     hamabe = face_client.person_group_person.create(
            #         person_group_id = PERSON_GROUP_ID,
            #         name = hamabe_name
            #     )
            
            # 認証結果に応じて処理を変える
            # if valified_hasikan:
            #     if valified_hasikan.is_identical:
            #         text = "この写真は橋本環奈です(score:{:.3f})".format(valified_hasikan.confidence)
            #     else:
            #         text = "この写真は橋本環奈ではありません(score:{:.3f})".format(valified_hasikan.confidence)

            # if valified_hamabe:
            #     if valified_hamabe.is_identical:
            #         text = "この写真は浜辺美波です(score:{:.3f})".format(valified_hamabe.confidence)
            #     else:
            #         text = "この写真は浜辺美波ではありません(score:{:.3f})".format(valified_hamabe.confidence)

        else:
            text = "写真から顔が検出できませんした。他の画像でお試しください。"
        
    except:
        text = "エラーが発生しました。"

    # text_list.append(text)
    # print(text_list)

    params["text_list"].append(text)
    print(params["text_list"])

    # LINEチャネルを通じてメッセージを返答
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text)
    )

    return text


if __name__ == "__main__":
    app.run()