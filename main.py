from telebot.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import pprint
import logging
import bot_manager

manager = bot_manager.BotManager()
bot = manager.bot

# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, manager.get_help(chat_id))


# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, manager.WELCOME_MSG)
    try:
        manager.get_user(chat_id)
        end_session(message, chat_id)
    except bot_manager.UserNotExistError:
        markup = ReplyKeyboardMarkup(row_width=1)
        markup.add(
            KeyboardButton(
                "שתף מספר טלפון",
                request_contact=True))
        bot.send_message(
            chat_id,
            "אני צריך את המספר שלך לצורכי אימות",
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

        try:
            manager.add_user(chat_id, message.contact.phone_number)
            end_session(message, chat_id)
        except bot_manager.UserNotInvited:
            bot.send_message(
                chat_id,
                "לא הוזמנת :(\nהאחראי פורומים זה הכתובת שלך")

    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def end_session(message, chat_id):
    try:
        user = manager.get_user(chat_id)
        markup = ReplyKeyboardRemove(selective=False)
        bot.send_message(
            chat_id,
            "הסריקה הושלמה! :)\n{}".format(pprint.pformat(user.data())),
            reply_markup=markup)

        # TODO: Send value
    except Exception as e:
        bot.reply_to(message, "אוי לא " + str(e))


def main():
    manager.run()


if __name__ == "__main__":
    main()
