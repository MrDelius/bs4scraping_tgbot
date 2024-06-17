import logging
import requests
from bs4 import BeautifulSoup
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Telegram Bot token and channel ID
BOT_TOKEN = '5581794924:AAFgwhDE_iCarFvstHGpmu_gEV3phFusl9Y'
CHANNEL_ID = -1001737360438

# URL of the website to scrape
URL = 'https://kg-portal.ru/news/anime/'
myURL = 'https://tgpost.onrender.com'


async def send_news(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Send a GET request to the website
        status = requests.get(myURL)
        status.raise_for_status()

        response = requests.get(URL)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'lxml')

        # Find the element with the specified class
        element = soup.select_one('.news_box.anime_cat')
        post_id = element.get('id')

        # Check if element is found
        if element is None:
            return

        # Extract image source, title, and content
        picture = element.find('picture')
        if picture is None:
            return

        image_src = picture.find('img').get('src')
        title = element.find('h2').get_text()
        content = element.select_one('.news_text').text.strip()

        # Retrieve the previous image source from context
        previous_id = context.job.data

        # Check if the current image source is different and not None
        if post_id and post_id != previous_id:
            logger.info("Sending news to channel...")
            # Send a photo to the channel
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=f'https://kg-portal.ru{image_src}',
                                         caption=f'<b>{title}</b>\n\n{content}\n@anime_novosti_top', parse_mode='HTML')
            # Update the previous image source in context
            context.job.data = post_id
            logger.info('Sent a new message to the channel')
            logger.debug("News sent successfully!")

    except Exception as e:
        # Handle exceptions
        logger.error(f'An error occurred: {e}')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Bot is active!')


# Define a function to handle errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f'Update {update} caused error {context.error}')


def main():
    # Set up the application with the job queue enabled
    application = Application.builder().token(BOT_TOKEN).build()

    # Log all errors
    application.add_error_handler(error)
    application.add_handler(CommandHandler('start', start))

    # Add a job to send news every hour
    job_queue = application.job_queue
    job_queue.run_repeating(send_news, interval=600, first=10, data={'previous_img': None})  # 3600 seconds = 1 hour

    # Start the bot
    application.run_polling()


if __name__ == '__main__':
    main()