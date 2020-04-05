#!/usr/bin/python

# This is a simple echo bot using the decorator mechanism.
# It echoes any incoming text messages.

import telebot
import user_details

API_TOKEN = '1187013257:AAGkU0Md05rHtEkBJ465AARklivI7nfDG1Q'
WELCOME_MSG = ("שלום אני בוט.\n"
               "אני אעזור לך להתמודד עם הלחץ הנפשי של הפורומים.\n"
               "\nמה השם שלך?")


bot = telebot.TeleBot(API_TOKEN)
user_dict = {}

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, WELCOME_MSG)
    bot.register_next_step_handler(message, process_name)

# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, message.text)


def process_name(message):
    try:
        chat_id = message.chat.id
        name = message.text
        user = user_details.User(name)
        user_dict[chat_id] = user
        reply = bot.reply_to(
            message, "האם אתה זכר או נקבה? [זכר/נקבה]")
        bot.register_next_step_handler(reply, process_sex)
    except Exception as e:
        bot.reply_to(message, "אוי לא")


def process_sex(message):
    try:
        chat_id = message.chat.id
        sex = message.text
        user = user_dict[chat_id]
        user.sex = sex
        if sex == user_details.MALE:
            bot.send_message(chat_id, "יא גבר, שמח לראות אותך!")
        elif sex == user_details.FEMALE:
            bot.send_message(chat_id, "שלום לך גברת " + user.name)
        else:
            raise Exception("זאת לא אפשרות. אני הבוט אל תיקח לי את העבודה.")

    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def main():
    bot.enable_save_next_step_handlers(delay=2)
    bot.load_next_step_handlers()
    bot.polling()


if __name__ == "__main__":
    main()
