from telebot.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import bot_manager

manager = bot_manager.BotManager()
bot = manager.bot

# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, manager.get_help(chat_id))

################
# Subscription #
################

# Handle '/start'
@bot.message_handler(commands=['start'])
def start_subscription(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, manager.WELCOME_MSG)

    try:
        manager.get_user(chat_id)
        end_subscription(message, chat_id)
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
        end_subscription(message, chat_id)
    except bot_manager.UserNotInvited:
        bot.send_message(
            chat_id,
            "לא הוזמנת :(\nהאחראי פורומים זה הכתובת שלך")


def end_subscription(message, chat_id):
    user = manager.get_user(chat_id)
    markup = ReplyKeyboardRemove(selective=False)
    bot.send_message(
        chat_id,
        "הסריקה הושלמה! :)\nשלום {}!".format(user.data()['name']),
        reply_markup=markup)


############
# Commands #
############

# Handle '/info'
@bot.message_handler(commands=['info'])
def send_info(message):
    chat_id = message.chat.id
    balances = manager.get_user_balances(chat_id)
    balances_str_list = []
    for group, balance in balances.items():
        if balance > 0:
            balances_str_list.append(
                "קבוצה: {}\n"
                "כל הכבוד! יש לך עודף של {} שקלים".format(group, balance))
        elif balance < 0:
            balances_str_list.append(
                "קבוצה: {}\n"
                "יש לך חוב בקופה של {} שקלים".format(group, -balance)
            )
        else:
            balances_str_list.append(
                "קבוצה: {}\n"
                "המאזן שלך מושלם!".format(group)
            )

    balances_str = "\n\n".join(balances_str_list)
    bot.send_message(chat_id, balances_str)


# Handle '/add'
@bot.message_handler(commands=['add'])
def start_add_group_user(message):
    chat_id = message.chat.id
    admin_groups = manager.get_admin_groups(chat_id)
    if not admin_groups:
        return

    markup = ReplyKeyboardMarkup(row_width=1)
    buttons = []
    for group in admin_groups:
        buttons.append(KeyboardButton(group.data()['name']))

    markup.add(*buttons)
    bot.send_message(
        chat_id,
        "לאיפה להוסיף את הבחור/ה החדש/ה?",
        reply_markup=markup)

    bot.register_next_step_handler(message, process_group_choice)


def process_group_choice(message):
    chat_id = message.chat.id
    admin_groups_names = [group.data()['name']
                          for group in manager.get_admin_groups(chat_id)]

    markup = ReplyKeyboardRemove(selective=False)
    if message.text not in admin_groups_names:
        bot.send_message(
            chat_id,
            "את/ה לא המנהל/ת של הקבוצה!",
            reply_markup=markup)
        return

    bot.send_message(
        chat_id,
        "מה השם של הבחור/ה החדש/ה?\nניתן לשתף איש קשר ;)",
        reply_markup=markup)
    bot.register_next_step_handler(message, process_member_name)


def process_member_name(message):
    chat_id = message.chat.id
    if message.contact is not None:
        manager.pending_user["name"] = "{} {}".format(str(message.contact.first_name),
                                                      str(message.contact.last_name)).strip()
        manager.pending_user["phone"] = message.contact.phone_number
        end_add_group_user(chat_id)
    else:
        manager.pending_user["name"] = message.text
        bot.send_message(chat_id, "אפשר את המספר שלו/שלה? ;)")
        bot.register_next_step_handler(message, process_member_phone)


def process_member_phone(message):
    chat_id = message.chat.id
    manager.pending_user["phone"] = message.text
    end_add_group_user(chat_id)


def end_add_group_user(chat_id):
    if (manager.pending_user["name"] is None or
            manager.pending_user["phone"] is None):
        return

    try:
        manager.add_user(
            chat_id,
            manager.pending_user["phone"],
            manager.pending_user["name"])
    except bot_manager.UserAlreadyExistsError:
        bot.send_message(chat_id, "המספר טלפון כבר קיים במערכת")

    bot.send_message(chat_id, "תודה!")


def main():
    manager.run()


if __name__ == "__main__":
    main()
