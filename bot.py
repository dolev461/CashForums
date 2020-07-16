from telebot.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, Update
import os
import functools
import logging
import flask
import bot_manager
import config


WELCOME_MSG = ("שלום, אני בוט.\n"
               "אני אעזור לך להתמודד עם הלחץ הנפשי של הפורומים.\n\n"
               "שנייה סורק אותך...")
ADD_PREFIX = "add_"
REMOVE_PREFIX = "remove_"
DISABLE_PREFIX = "disable_"
INFO_PREFIX = "info_"
BILL_PREFIX = "bill_"
REFUND_PREFIX = "refund_"
MEMBER_RM_PREFIX = "memberrm_"
MEMBER_DISABLE_PREFIX = "memberdisable_"
MEMBER_BILL_PREFIX = "memberbill_"
MEMBER_REFUND_PREFIX = "memberrefund_"

HOST = "0.0.0.0"
PORT = os.getenv("PORT", 5000)


manager = bot_manager.BotManager()
bot = manager.bot
server = flask.Flask(__name__)


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
    except bot_manager.UserNotInvitedError:
        bot.send_message(
            chat_id,
            "לא הוזמנת :(\nהאחראי פורומים זה הכתובת שלך")


def end_subscription(message, chat_id):
    user = manager.get_user(chat_id)
    markup = ReplyKeyboardMarkup(row_width=1)
    markup.add(KeyboardButton("/help"))
    bot.send_message(
        chat_id,
        "הסריקה הושלמה! :)\nשלום {}!"
        "\nבבקשה תכתוב /help בשביל לראות מה אני מסוגל לעשות.".format(
            user.data()['name']),
        reply_markup=markup)


####################
# Helper Functions #
####################
def is_any_group_admin(chat_id):
    if not manager.get_admin_groups(chat_id):
        bot.send_message(
            chat_id,
            "רק אחראי\ת פורומים יכול\ה לשאת באחריות כזאת כבדה 🏋️‍♀️")
        return False

    return True


def ask_for_group(chat_id, text, callback_prefix=""):
    admin_groups = manager.get_admin_groups(chat_id)
    if not admin_groups:
        return

    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for group in admin_groups:
        buttons.append(InlineKeyboardButton(
            group,
            callback_data="{}{}".format(callback_prefix, group)))

    markup.add(*buttons)
    bot.send_message(
        chat_id,
        text,
        reply_markup=markup)


def process_group_choice(chat_id, group, success_text, markup=None):
    fail_markup = ReplyKeyboardMarkup(row_width=1)
    fail_markup.add(KeyboardButton("/help"))
    if not manager.is_group_admin(chat_id, group):
        bot.send_message(
            chat_id,
            "את/ה לא המנהל/ת של הקבוצה!",
            reply_markup=fail_markup)
        return False

    bot.send_message(
        chat_id,
        success_text,
        reply_markup=markup)

    return True


def create_members_markup(group, callback_prefix=""):
    markup = InlineKeyboardMarkup(row_width=1)
    buttons = []
    try:
        for user in manager.get_group(group).get_users():
            buttons.append(InlineKeyboardButton(
                user["name"],
                callback_data="{}{}".format(callback_prefix, user["phone"])))

        markup.add(*buttons)
    except bot_manager.GroupNotExistError:
        pass

    return markup


#################
# User Commands #
#################
# Handle '/help'
@bot.message_handler(commands=['help'])
def send_help(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        "היי, אני בוט וזה מה שאני יכול לעשות:",
        reply_markup=manager.get_help(chat_id))


@bot.callback_query_handler(func=lambda query: query.data.startswith(manager.CB_INFO))
def info(call):
    message = call.message
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

    bot.answer_callback_query(call.id)

########################
# Group Admin Commands #
########################
@bot.callback_query_handler(func=lambda query: query.data.startswith(manager.CB_ADD))
def start_add_member(call):
    chat_id = call.message.chat.id
    if not is_any_group_admin(chat_id):
        return

    ask_for_group(chat_id, "לאיפה להוסיף את הבחור/ה החדש/ה?", ADD_PREFIX)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda query: query.data.startswith(ADD_PREFIX))
def process_add_group_choice(call):
    chat_id = call.message.chat.id
    group = call.data.replace(ADD_PREFIX, "", 1)

    if not manager.is_group_admin(chat_id, group):
        raise Exception()

    bot.answer_callback_query(call.id)
    bot.send_message(
        chat_id,
        "מה השם של הבחור/ה החדש/ה?\nניתן לשתף איש קשר ;)")
    manager.pending_user["group"] = group
    bot.register_next_step_handler(call.message, process_member_name)


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
        bot.send_message(chat_id, "אני לא יודע לאיפה להוסיף 😢")
        return

    try:
        try:
            manager.add_user_by_phone(
                manager.pending_user["phone"],
                manager.pending_user["name"])
        except bot_manager.UserAlreadyExistsError:
            pass

        try:
            manager.add_member(
                manager.pending_user["group"],
                manager.pending_user["phone"])
        except bot_manager.UserAlreadyInGroupError:
            bot.send_message(chat_id, "המספר טלפון כבר קיים בקבוצה")
        else:
            bot.send_message(chat_id, "תודה!")
    except bot_manager.InvalidPhoneError:
        bot.send_message(
            chat_id,
            "זה לא מספר לגיטימי בכלל 📱"
        )

    manager.clear_pending_user()


@bot.callback_query_handler(func=lambda query: query.data.startswith(manager.CB_REMOVE))
def remove_member(call):
    chat_id = call.message.chat.id
    if not is_any_group_admin(chat_id):
        return

    ask_for_group(chat_id, "מאיזו קבוצה מתבצעת ההדחה? 😔", REMOVE_PREFIX)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda query: query.data.startswith(REMOVE_PREFIX))
def process_remove_group_choice(call):
    chat_id = call.message.chat.id
    group = call.data.replace(REMOVE_PREFIX, "", 1)
    if not manager.is_group_admin(chat_id, group):
        raise Exception()

    manager.pending_user["group"] = group
    markup = create_members_markup(group, MEMBER_RM_PREFIX)
    bot.answer_callback_query(call.id)
    bot.send_message(
        chat_id,
        "בחר\י את המודח\ת שלך 🔥",
        reply_markup=markup)


@bot.callback_query_handler(func=lambda query: query.data.startswith(MEMBER_RM_PREFIX))
def process_remove_member(call):
    chat_id = call.message.chat.id
    if manager.pending_user["group"] is None:
        bot.send_message(chat_id, "לא נבחרה קבוצה להדחה -_-")
        bot.answer_callback_query(call.id)
        return

    phone = call.data.replace(MEMBER_RM_PREFIX, "")
    name = manager.get_user(chat_id).data()["name"]

    manager.remove_member(manager.pending_user["group"], phone)
    bot.send_message(chat_id, "בה ביי {}. בהצלחה!".format(name))
    bot.answer_callback_query(call.id)

    manager.clear_pending_user()


@bot.callback_query_handler(func=lambda query: query.data.startswith(manager.CB_DISABLE))
def disable_member(call):
    chat_id = call.message.chat.id
    if not is_any_group_admin(chat_id):
        return

    ask_for_group(chat_id, "מאיזו קבוצה מתבצעת ההקפאה? 😔", DISABLE_PREFIX)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda query: query.data.startswith(DISABLE_PREFIX))
def process_disable_group_choice(call):
    chat_id = call.message.chat.id
    group = call.data.replace(DISABLE_PREFIX, "", 1)
    if not manager.is_group_admin(chat_id, group):
        raise Exception()

    manager.pending_user["group"] = group
    markup = create_members_markup(group, MEMBER_DISABLE_PREFIX)
    bot.answer_callback_query(call.id)
    bot.send_message(
        chat_id,
        "בחר\י את המוקפא\ת שלך 🥶",
        reply_markup=markup)


@bot.callback_query_handler(func=lambda query: query.data.startswith(MEMBER_DISABLE_PREFIX))
def process_disable_member(call):
    chat_id = call.message.chat.id
    if manager.pending_user["group"] is None:
        bot.send_message(chat_id, "לא נבחרה קבוצה להקפאה -_-")
        bot.answer_callback_query(call.id)
        return

    phone = call.data.replace(MEMBER_DISABLE_PREFIX, "", 1)
    name = manager.get_user_from_phone(phone)['name']

    manager.toggle_disable_member(manager.pending_user["group"], phone)
    bot.send_message(
        chat_id, "{} אם חזרת תהנה, אחרת מחכים לשובך!".format(name))
    bot.answer_callback_query(call.id)

    manager.clear_pending_user()


@bot.callback_query_handler(func=lambda query: query.data.startswith(manager.CB_BILL) or query.data.startswith(manager.CB_REFUND))
def start_bill(call):
    chat_id = call.message.chat.id
    if not is_any_group_admin(chat_id):
        return

    if call.data.startswith(manager.CB_BILL):
        ask_for_group(chat_id, "מאיזו קבוצה מתבצע החיוב? 💳", BILL_PREFIX)
    else:  # Refund)
        ask_for_group(chat_id, "מאיזו קבוצה מתבצע הזיכוי? 💳", REFUND_PREFIX)

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda query: query.data.startswith(BILL_PREFIX) or query.data.startswith(REFUND_PREFIX))
def process_bill_member_choice(call):
    chat_id = call.message.chat.id
    group = call.data.replace(BILL_PREFIX, "", 1).replace(REFUND_PREFIX, "", 1)
    if not manager.is_group_admin(chat_id, group):
        raise Exception()

    manager.pending_user["group"] = group
    bot.answer_callback_query(call.id)
    if call.data.startswith(BILL_PREFIX):
        markup = create_members_markup(group, MEMBER_BILL_PREFIX)
        bot.send_message(
            chat_id,
            "בחר\י את מי לחייב 🤑",
            reply_markup=markup)
    else:  # Refund
        markup = create_members_markup(group, MEMBER_REFUND_PREFIX)
        bot.send_message(
            chat_id,
            "בחר\י את מי לזכות 🤑",
            reply_markup=markup)


@bot.callback_query_handler(func=lambda query: query.data.startswith(MEMBER_BILL_PREFIX) or query.data.startswith(MEMBER_REFUND_PREFIX))
def process_bill_amount(call):
    chat_id = call.message.chat.id
    phone = call.data.replace(MEMBER_BILL_PREFIX, "", 1).replace(
        MEMBER_REFUND_PREFIX, "", 1)
    name = manager.get_user(chat_id).data()["name"]
    manager.pending_user["phone"] = phone
    manager.pending_user["name"] = name

    bot.answer_callback_query(call.id)
    if call.data.startswith(MEMBER_BILL_PREFIX):
        bot.send_message(
            chat_id,
            "הכנס סכום לחיוב ובבקשה לא לטעות זה חשוב 😅")
        bot.register_next_step_handler(call.message, process_bill_member)
    else:  # Refund
        bot.send_message(
            chat_id,
            "הכנס סכום לזיכוי ובבקשה לא לטעות זה חשוב 😅")
        bot.register_next_step_handler(
            call.message, functools.partial(process_bill_member, is_refund=True))


def process_bill_member(message, is_refund=False):
    chat_id = message.chat.id
    amount = message.text
    if is_refund:
        amount = "-" + amount

    try:
        manager.bill_member(
            manager.pending_user["group"],
            manager.pending_user["phone"],
            amount)

        bot.send_message(
            chat_id,
            "מה שנעשה נעשה!")
    except bot_manager.InvalidAmountError:
        bot.send_message(
            chat_id,
            "זה אפילו לא מספר 😒")
    except bot_manager.GroupNotExistError:
        bot.send_message(
            chat_id,
            "אני לא זוכר איזו קבוצה לחייב 🥴"
        )

    manager.clear_pending_user()


@bot.callback_query_handler(func=lambda query: query.data.startswith(manager.CB_GROUP_INFO))
def start_group_info(call):
    chat_id = call.message.chat.id
    if not is_any_group_admin(chat_id):
        return

    groups = manager.get_admin_groups(chat_id)
    if len(groups) == 1:
        send_group_info(chat_id, groups.pop())
    else:
        ask_for_group(chat_id, "מה הקבוצה שאנחנו מחפשים?", INFO_PREFIX)

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda query: query.data.startswith(INFO_PREFIX))
def process_group_info(call):
    chat_id = call.message.chat.id

    group = call.data.replace(INFO_PREFIX, "", 1)
    if process_group_choice(
            chat_id,
            group,
            "פרטי הקבוצה {}:".format(group)):
        send_group_info(chat_id, group)

    bot.answer_callback_query(call.id)


def send_group_info(chat_id, group):
    try:
        balances = manager.get_all_users_balances(group)
        disabled = [user['name'] for user in manager.get_disabled_users(group)]
    except bot_manager.GroupNotExistError:
        bot.send_message(chat_id, "אני לא מכיר את הקבוצה: {}".format(group))

    # Sort by money
    sorted_balances = sorted(
        balances.items(),
        key=lambda item: item[1])
    disabled_balances = [
        balance for balance in sorted_balances if balance[0] in disabled]
    active_balances = [
        balance for balance in sorted_balances if balance not in disabled_balances]

    msg = "\n".join(["{} {}: {}".format("🟢" if amount >= 0 else "🔴", name, amount)
                     for name, amount in active_balances] +
                    ["{} {}: {}".format("⚫", name, amount)
                     for name, amount in disabled_balances])

    bot.send_message(chat_id, msg)


##################
# Admin Commands #
##################
@bot.callback_query_handler(func=lambda query: query.data.startswith(manager.CB_GROUP_ADD))
def start_group_create(call):
    message = call.message
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
    bot.answer_callback_query(call.id)
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
    if gname is None:
        bot.send_message(chat_id, "לא נבחר שם לקבוצה :(")
        return

    if message.contact is not None:
        phone = message.contact.phone_number
    else:
        phone = message.text

    try:
        manager.get_user_from_phone(phone)
        manager.create_group(gname, phone)
        manager.add_member(gname, phone)
        bot.send_message(
            chat_id,
            "יצרתי את הקבוצה '{}'😉".format(gname)
        )
    except bot_manager.UserNotExistError:
        bot.reply_to(
            message,
            "יצירת הקבוצה נכשלה, לא הצלחתי למצוא את המספר {} במערכת.".format(
                phone)
        )
    except bot_manager.GroupAlreadyExistsError:
        bot.send_message(
            chat_id,
            "הקבוצה {} כבר קיימת 🤦‍♀️".format(gname)
        )
    except bot_manager.InvalidPhoneError:
        bot.send_message(
            chat_id,
            "זה לא מספר לגיטימי בכלל 📱"
        )


@bot.callback_query_handler(func=lambda query: query.data.startswith(manager.CB_GROUP_RM))
def start_group_delete(call):
    message = call.message
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
    bot.answer_callback_query(call.id)
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


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id, "לא הבנתי... ביפ בופ...")


@server.route("/" + config.config["API_TOKEN"], methods=["POST"])
def get_message():
    bot.process_new_updates(
        [Update.de_json(flask.request.stream.read().decode("utf-8"))])

    return "!", 200


@server.route("/")
def webhook():
    logging.info("CashForums telegram bot is up :)")
    manager.run()
    logging.info("The bot is down :(")

    return "!", 200


if __name__ == "__main__":
    try:
        #os.environ["DEBUG"] = "TRUE"
        if os.getenv("DEBUG", False):
            manager.run(debug=True)
        else:
            server.run(host=HOST, port=PORT)
    finally:
        bot.remove_webhook()
