# bot.py
import logging
from charset_normalizer import detect
import openai
import json
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from scrape_sulpak import scrape_sulpak_air_conditioners  # Import the scraping function
from langdetect import detect, LangDetectException

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting bot script")

openai.api_key = 'Open-AI API key'

# Load air conditioners data from JSON file
def load_air_conditioners_data():
    with open('air_conditioners.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# to detect the language of the prompt
def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return 'en'  # Default to English if detection fails
    
# to get recommendations from ChatGPT
async def get_recommendation(prompt):
    logger.info("Generating recommendation for prompt: %s", prompt)
    
    language = detect_language(prompt)
    
    try:
        # Load air conditioners data
        air_conditioners = load_air_conditioners_data()
        
        # Format the air conditioners data for the ChatGPT prompt
        ac_data = "\n".join([f"{i+1}. {ac['title']} - {ac['price']} - {ac['link']}" for i, ac in enumerate(air_conditioners)])
        
        if language == 'ru':
            instruction = "На основе этого списка порекомендуйте модель, которая соответствует следующим критериям:"
            response_instruction = "Ответьте на русском языке."
        elif language == 'kk':
            instruction = "Осы тізімнің негізінде келесі өлшемдерге сәйкес келетін модельді ұсыныңыз:"
            response_instruction = "Жауапты қазақ тілінде беріңіз."
        else:
            instruction = "Based on this list, recommend a model that suits the following criteria:"
            response_instruction = "Please respond in English."
        
        full_prompt = f"Here are some air conditioners you might consider:\n{ac_data}\n\n{instruction} {prompt}\n\n{response_instruction}"
        
        # Call the OpenAI API with the full prompt
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=4000
        )
        response_text = response.choices[0].message['content'].strip()
        logger.info("Received response from OpenAI: %s", response_text)
    except openai.error.OpenAIError as e:
        logger.error("Error calling OpenAI API: %s", str(e))
        if 'insufficient_quota' in str(e):
            return "Sorry, the service is currently unavailable due to exceeded quota. Please try again later."
        return "Sorry, there was an error generating the recommendation."

    # Combine the ChatGPT response with the product recommendations
    air_conditioners_info = "\n".join([f"{i+1}. {ac['title']} - {ac['price']} - {ac['link']}" for i, ac in enumerate(air_conditioners)])
    
    return f"{response_text}\n"

# Define a function to handle image inputs
async def handle_image(update: Update, context: CallbackContext):
    logger.info("Received an image")
    file = await update.message.photo[-1].get_file()
    file_path = 'room.jpg'
    await file.download(file_path)
    
    # Process the image if necessary 
    prompt = f"I want to buy an air conditioner for this room. Recommend the best one from Sulpak."
    recommendation = await get_recommendation(prompt)
    
    await update.message.reply_text(recommendation)

# function to handle text inputs
async def handle_text(update: Update, context: CallbackContext):
    logger.info("Received a text message")
    user_message = update.message.text
    recommendation = await get_recommendation(user_message)
    await update.message.reply_text(recommendation)

async def error(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    logger.info("Inside main function")
    application = ApplicationBuilder().token("telegram API").build()
    logger.info("Application created")

    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error)
    
    logger.info("Starting polling")
    application.run_polling()
    logger.info("Polling started")

    # Scrape data initially when bot starts
    scrape_sulpak_air_conditioners()

if __name__ == '__main__':
    main()
    logger.info("Script finished")

