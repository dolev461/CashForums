import bot_manager
import user_details
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

bot_manager = bot_manager.BotManager()
bot = bot_manager.bot

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=1)
    markup.add(
        KeyboardButton(
            'אני צריך את המספר שלך לצורכי אימות',
            request_contact=True))
    bot.send_message(message.chat.id, bot_manager.WELCOME_MSG,
                     reply_markup=markup)
    bot.register_next_step_handler(message, process_phone_number)


def process_phone_number(message):
    try:
        chat_id = message.chat.id
        if message.contact is None:
            bot.send_message(
                chat_id,
                "אי אפשר להמשיך ככה... זה לא אני זה אתה!")
            # Try again
            bot.register_next_step_handler(message, process_phone_number)
            return

        bot_manager.add_user(chat_id, message.contact.phone_number)
        end_session(message, chat_id)
    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def process_sex(message):
    try:
        chat_id = message.chat.id
        sex = message.text
        user = bot_manager.get_user(chat_id)
        if user.name == user_details.UNKNOWN:
            print("New user detected, who hasn't used '/start' yet")

        user.sex = sex
        if sex == user_details.MALE:
            bot.send_message(chat_id, "יא גבר, שמח לראות אותך!")
        elif sex == user_details.FEMALE:
            bot.send_message(chat_id, "שלום לך גברת " + user.name)
        else:
            raise Exception("זאת לא אפשרות. אני הבוט אל תיקח לי את העבודה.")

        end_session(message, chat_id)

    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def end_session(message, chat_id):
    try:
        user = bot_manager.get_user(chat_id)
        markup = ReplyKeyboardRemove(selective=False)
        bot.send_message(
            chat_id,
            "הסריקה הושלמה! :)\n{}".format(str(user)),
            reply_markup=markup)
        bot.send_message(chat_id, user.get_value_status())
    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def main():
    bot_manager.run()


if __name__ == "__main__":
    main()
