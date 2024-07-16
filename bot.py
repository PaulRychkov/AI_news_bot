import telebot
import requests
import pyodbc
from datetime import datetime, timedelta
import json
import codecs

class NewsBot:
    def __init__(self, db_connection_string, bot_api_token, openai_api_key, gpt_request_file, gpt_summarize_file):
        self.db_connection_string = db_connection_string
        self.gpt_request_file = gpt_request_file
        self.gpt_summarize_file = gpt_summarize_file
        self.openai_api_key = openai_api_key
        self.bot = telebot.TeleBot(bot_api_token)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        self._set_handlers()

    def _set_handlers(self):
        @self.bot.message_handler(content_types=['text'])
        def handle_text_messages(message):
            if len(message.text) <= 100:
                if message.text != "/start":
                    gpt_answer = self.get_gpt_answer(message.text)
                    if isinstance(gpt_answer, str):
                        result = gpt_answer
                    else:
                        result = self.get_gpt_summarize(gpt_answer)
                else:
                    result = "Привет, ты можешь узнать у меня новости по интересующей тебя теме за указанный период времени"
            else:
                result = "Извини, но твое сообщение слишком длинное, сократи его пожалуйста"
            if isinstance(result, list):
                for r in result: 
                    self.bot.send_message(message.from_user.id, r)
            else:
                self.bot.send_message(message.from_user.id, result)

    async def start(self):
        self.bot.polling(none_stop=True, interval=0)

    def get_gpt_answer(self, input_task):
        
        f = codecs.open(self.gpt_request_file, encoding="utf-8")
        gpt_task = f.read()
        f.close()

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=self.payload(gpt_task + input_task)).json()['choices'][0]['message']['content']

        response = json.loads(response[response.find("{"):response.rfind("}") + 1])
        if not response['themes']:
            return "Извини я не понял вопроса, ты можешь узнать у меня последние новости по интересующей тебя теме за указанный период времени"
        if response['themes'][0] == "-1":
            return "Извини новостей по данной тематике у меня пока нет, попробуй спросить новости по другим темам"        
        with pyodbc.connect(self.db_connection_string) as conn:
            cursor = conn.cursor()
            sql = """\
            declare @json NVARCHAR(MAX) = 
            (
            SELECT MESSAGE_DATA as message, MESSAGE_DATE as date
            FROM dbo.NEWS
            WHERE '%' + ? + '%' like '%' + CAST(CHAT_ID as NVARCHAR) + '%' 
            AND MESSAGE_DATE >= ?
            for json path
            )
            SELECT @json as value
            """
            cursor.execute(sql, self.get_chats_ids(','.join(response['themes'])), self.get_start_date(response['date']))
            news = eval(cursor.fetchall()[0].value)

            news_result = ['']

            news_ls = []
            for n in news:
                news_ls.append(n['message'] + '\n' + n['date'] + '\n')

            for n in news_ls:
                if len(news_result[-1]) + len(n) > 7000:
                    news_result.append('')
                news_result[-1] += n

            return news_result
        
    def get_gpt_summarize(self, news):

        with codecs.open(self.gpt_summarize_file, encoding="utf-8") as f:
            gpt_task = f.read()

        result = []
        for n in news:     
            result.append(self.get_gpt_summarize_step(n, gpt_task))

        max_len = max(len(sublist) for sublist in result)

        combined_list = []
        for i in range(max_len):
            for sublist in result:
                if i < len(sublist):
                    combined_list.append(sublist[i])

        if combined_list:
            res = ['Вот самые интересные новости по вашему запросу:\n']
            for idx, news_item in enumerate(combined_list):
                if len(res[-1]) + len(news_item) > 3900:
                    res.append('')
                res[-1] += f"\n{idx + 1}. {news_item['text']}\n{news_item['date']}\n"

        return res
    
    def get_gpt_summarize_step(self, news, gpt_task):

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=self.payload(gpt_task + news)).json()['choices'][0]['message']['content']
        response = json.loads(response[response.find("["):response.rfind("]") + 1])

        return response

    def get_start_date(self, date):
        timeframes = {
            "час": timedelta(hours=1),
            "день": timedelta(days=1),
            "2 дня": timedelta(days=2),
            "3 дня": timedelta(days=3),
            "4 дня": timedelta(days=4),
            "неделя": timedelta(weeks=1)
        }
        return datetime.now() - timeframes[date]

    def get_chats_ids(self, themes):
        chat_ids = {
            "спорт": "-1001167948059",
            "экономика": "-1001565562058",
            "технологии": "-1001551519421",
            "наука": "-1001371219605",
            "нейросети": "-1001466120158"
        }
        for theme, chat_id in chat_ids.items():
            themes = themes.replace(theme, chat_id)
        return themes
    
    def payload(self, text):
        return {
                "model": "gpt-4o",
                "messages": [
                    {
                    "role": "user",
                    "content": [
                        {
                        "type": "text",
                        "text": text
                        }
                    ]
                    }
                ]
                } 