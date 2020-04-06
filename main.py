from telebot.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import bot_manager

manager = bot_manager.BotManager()
bot = manager.bot

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=1)
    markup.add(
        KeyboardButton(
            'אני צריך את המספר שלך לצורכי אימות',
            request_contact=True))
    bot.send_message(message.chat.id, manager.WELCOME_MSG,
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

        manager.add_user(chat_id, message.contact.phone_number)
        end_session(message, chat_id)
    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def end_session(message, chat_id):
    try:
        user = manager.get_user(chat_id)
        markup = ReplyKeyboardRemove(selective=False)
        bot.send_message(
            chat_id,
            "הסריקה הושלמה! :)\n{}".format(str(user)),
            reply_markup=markup)
        bot.send_message(chat_id, user.get_value_status())
    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def main():
    manager.run()


if __name__ == "__main__":
    main()
