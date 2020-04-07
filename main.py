from telebot.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
import bot_manager


WELCOME_MSG = ("שלום, אני בוט.\n"
               "אני אעזור לך להתמודד עם הלחץ הנפשי של הפורומים.\n\n"
               "שנייה סורק אותך...")


manager = bot_manager.BotManager()
bot = manager.bot


################
# Subscription #
################

# Handle '/start'
@bot.message_handler(commands=['start'])
def start_subscription(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, WELCOME_MSG)

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


####################
# Helper Functions #
####################

def ask_for_contact(chat_id, text):
    admin_groups = manager.get_admin_groups(chat_id)
    if not admin_groups:
        return

    markup = ReplyKeyboardMarkup(row_width=1)
    buttons = []
    for group in admin_groups:
        buttons.append(KeyboardButton(group))

    markup.add(*buttons)
    bot.send_message(
        chat_id,
        text,
        reply_markup=markup)


############
# Commands #
############

# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, manager.get_help(chat_id))

# Handle '/info'
@bot.message_handler(commands=['info'])
def send_info(message):
    chat_id = message.chat.id
    if not manager.is_user_exists(chat_id):
        return

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
                "אין לך חוב בקופה. מדהים :)".format(group)
            )

    balances_str = "\n\n".join(balances_str_list)
    if balances_str:
        bot.send_message(chat_id, balances_str)
    else:
        bot.send_message(chat_id, "לא מצאתי את הקבוצה שלך :(")


# Handle '/add'
@bot.message_handler(commands=['add'])
def start_add_member(message):
    chat_id = message.chat.id

    ask_for_contact(chat_id, "לאיפה להוסיף את הבחור/ה החדש/ה?")

    bot.register_next_step_handler(message, process_group_choice)


def process_group_choice(message):
    chat_id = message.chat.id
    admin_groups = manager.get_admin_groups(chat_id)

    markup = ReplyKeyboardRemove(selective=False)
    if message.text not in admin_groups:
        bot.send_message(
            chat_id,
            "את/ה לא המנהל/ת של הקבוצה!",
            reply_markup=markup)
        return

    manager.pending_user["group"] = message.text
    bot.send_message(
        chat_id,
        "מה השם של הבחור/ה החדש/ה?\nניתן לשתף איש קשר ;)",
        reply_markup=markup)
    bot.register_next_step_handler(message, process_member_name)


def process_member_name(message):
    chat_id = message.chat.id
    if message.contact is not None:
        name = []
        if message.contact.first_name is not None:
            name.append(str(message.contact.first_name))
        if message.contact.last_name is not None:
            name.append(str(message.contact.last_name))
        manager.pending_user["name"] = " ".join(name)
        manager.pending_user["phone"] = message.contact.phone_number
        end_add_member(chat_id)
    else:
        manager.pending_user["name"] = message.text
        bot.send_message(chat_id, "אפשר את המספר שלו/שלה? ;)")
        bot.register_next_step_handler(message, process_member_phone)


def process_member_phone(message):
    chat_id = message.chat.id
    manager.pending_user["phone"] = message.text
    end_add_member(chat_id)


def end_add_member(chat_id):
    if (manager.pending_user["name"] is None or
            manager.pending_user["phone"] is None or
            manager.pending_user["group"] is None):
        return

    try:
        manager.add_user_by_phone(
            manager.pending_user["phone"],
            manager.pending_user["name"])
    except bot_manager.UserAlreadyExistsError:
        bot.send_message(chat_id, "המספר טלפון כבר קיים במערכת")

    try:
        manager.add_member(
            manager.pending_user["group"],
            manager.pending_user["phone"])
    except bot_manager.UserAlreadyInGroupError:
        bot.send_message(chat_id, "המספר טלפון כבר קיים בקבוצה")

    bot.send_message(chat_id, "תודה!")
    manager.pending_user = {
        "name": None,
        "phone": None,
        "group": None
    }

# Handle '/groupadd'
@bot.message_handler(commands=['groupadd'])
def start_group_create(message):
    chat_id = message.chat.id
    user = manager.get_user(chat_id)
    if not user.data()['admin']:
        bot.reply_to(
            message,
            "זה רק לאדמינים הפיצ'ר הזה 😑")
        return

    bot.reply_to(
        message,
        "איך לקרוא לקבוצה?"
    )
    bot.register_next_step_handler(message, process_group_create)

def process_group_create(message):
    chat_id = message.chat.id

    name = message.text

    bot.reply_to(
        message,
        "סבבה, אני אקרא לקבוצה '{}'".format(name))
    manager.pending_group['name'] = name

    bot.send_message(
        chat_id,
        "מה מספר הפלאפון של מנהל הקבוצה? (ניתן לשתף איש קשר)"
    )
    bot.register_next_step_handler(message, process_group_create_admin)

def process_group_create_admin(message):
    chat_id = message.chat.id
    gname = manager.pending_group['name']
    if message.contact is not None:
        phone = bot_manager.BotManager.format_il_phone_number(message.contact.phone_number)
    else:
        phone = bot_manager.BotManager.format_il_phone_number(message.text)

    try:
        user = manager.get_user_from_phone(phone)
        manager.create_group(gname, phone)
        manager.add_member(gname, phone)
        bot.send_message(
            chat_id,
            "יצרתי את הקבוצה '{}'😉".format(gname)
        )
    except bot_manager.UserNotExistError:
        bot.reply_to(
            message,
            "יצירת הקבוצה נכשלה, לא הצלחתי למצוא את המספר {} במערכת.".format(phone)
        )
    except bot_manager.GroupAlreadyExists:
        bot.send_message(
            chat_id,
            "הקבוצה {} כבר קיימת 🤦‍♀️".format(gname)
        )

# Handle '/grouprm'
@bot.message_handler(commands=['grouprm'])
def start_group_delete(message):
    chat_id = message.chat.id
    user = manager.get_user(chat_id)
    if not user.data()['admin']:
        bot.reply_to(
            message,
            "זה רק לאדמינים הפיצ'ר הזה 😑")
        return

    bot.reply_to(
        message,
        "מה שם הקבוצה שצריך למחוק? 🤔"
    )
    bot.register_next_step_handler(message, process_group_delete)

def process_group_delete(message):
    chat_id = message.chat.id
    name = message.text

    try:
        group = manager.get_group(name)
        group.delete()
        bot.send_message(
            chat_id,
            "הקבוצה נמחקה."
        )
    except bot_manager.GroupNotExistError:
        bot.reply_to(
            message,
            "אין קבוצה כזאת 🤦‍♀️, המחיקה נכשלה."
        )


# Handle '/rm'
@bot.message_handler(commands=['rm'])
def remove_member(message):
    pass


def main():
    manager.run()


if __name__ == "__main__":
    main()
