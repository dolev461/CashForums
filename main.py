import bot_manager
import user_details

bot_manager = bot_manager.BotManager()
bot = bot_manager.bot

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, bot_manager.WELCOME_MSG)
    bot.register_next_step_handler(message, process_name)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, message.text)


def process_name(message):
    try:
        chat_id = message.chat.id
        name = message.text
        bot_manager.add_user(chat_id, name)
        reply = bot.reply_to(
            message, "האם אתה זכר או נקבה? [זכר/נקבה]")
        bot.register_next_step_handler(reply, process_sex)
    except Exception as e:
        bot.reply_to(message, "אוי לא")


def process_sex(message):
    try:
        chat_id = message.chat.id
        sex = message.text
        user = bot_manager.get_user(chat_id)
        user.sex = sex
        if sex == user_details.MALE:
            bot.send_message(chat_id, "יא גבר, שמח לראות אותך!")
        elif sex == user_details.FEMALE:
            bot.send_message(chat_id, "שלום לך גברת " + user.name)
        else:
            raise Exception("זאת לא אפשרות. אני הבוט אל תיקח לי את העבודה.")

        end_session(chat_id)

    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def end_session(chat_id):
    bot.send_message(chat_id, "בה ביי :)")


def main():
    bot_manager.run()


if __name__ == "__main__":
    main()
