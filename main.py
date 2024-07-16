import asyncio
from bot import NewsBot
from parser import NewsParser
from env_setup import DB_CONNECTION_STRING, PHONE, API_ID, API_HASH, BOT_API_TOKEN, OPENAI_API_KEY

async def main():
    parser = NewsParser(DB_CONNECTION_STRING, PHONE, API_ID, API_HASH)
    await parser.parse()

    bot = NewsBot(DB_CONNECTION_STRING, BOT_API_TOKEN, OPENAI_API_KEY, 'news_ai_bot\gpt.md', 'news_ai_bot\gptSummarize.md')
    await asyncio.gather(bot.start(), parser.start())

if __name__ == "__main__":
    asyncio.run(main())