import telebot 
from telebot.types import Message, CallbackQuery
from datetime import datetime
import time
from settings.config import token, admin_id, base_name, TOKEN_YOOMONEY, RECIVER, CLIENT_ID
from yoomoney import Client, Quickpay
import pyjokes 
from googletrans import Translator
import sqlite3 as sq
translator = Translator()



bot = telebot.TeleBot(token=token)

def init_db():
    conn = sq.connect(base_name)
    cursor = conn.cursor() 
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users (
                   user_id INTEGER PRIMARY KEY, 
                   data_reg TEXT
                   )''')
    conn.commit()
    conn.close()


def register_user(user_id, data_reg):
    conn = sq.connect(base_name)
    cursor = conn.cursor() 
    c = cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
    if c <= 0:
        cursor.execute("INSERT INTO users (user_id, data_reg) VALUES (?, ?)", (user_id, data_reg))
        conn.commit()

@bot.message_handler(commands=['start'])
def start(message: Message):
    data_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = message.from_user.id 

    register_user(user_id, data_reg)
    menu(message)
    return

def get_info(user_id) -> dict:
    conn = sq.connect(base_name); cursor=conn.cursor()
    i = cursor.execute("SELECT user_id, data_reg FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if i:
        return {
            "user_id": i[0],
            "data_reg": i[1]
        }
    return None


@bot.message_handler(commands=['anekdot', 'jokes'])
def jokes(message: Message):
    keyboard=telebot.types.InlineKeyboardMarkup(row_width=2)
    button1 = telebot.types.InlineKeyboardButton(text="Сгенерировать анекдот", callback_data="jokes_generate")
    keyboard.add(button1)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "jokes_generate")
def jokes_generate(call):
    chat_id = call.message.chat.id 

    joke = pyjokes.get_joke()
    joke_result = translator.translate(joke, dest='ru').text

    bot.send_message(chat_id, f"Анекдот сгенерирован:\n\n{joke_result}")

@bot.message_handler(commands=['menu', 'prof'])
def menu(message: Message):
    info = get_info(message.from_user.id)
    if info:

        k = telebot.types.InlineKeyboardMarkup(row_width=2)
        button1 = telebot.types.InlineKeyboardButton("Jokes", callback_data="jokes_generate")
        button2 = telebot.types.InlineKeyboardButton('Payment', callback_data='payment')
        k.add(button1, button2)
        data_reg = info['data_reg']
        msg = f"@{message.from_user.username}, ваш профиль:"
        msg += f"\n\nДата регистрации: {data_reg}"
        bot.send_message(message.from_user.id, msg, reply_markup=k)
    else:
        msg = "Информация о вашем профиле не найдена."
        bot.send_message(message.from_user.id, msg)
    
    # bot.send_message(message.from_user.id, msg, reply_markup=k)


# == создание оплаты 
@bot.callback_query_handler(func=lambda call: call.data == "payment")
def oplata(call: CallbackQuery):
    chat_id = call.message.chat.id 
    msg = bot.send_message(chat_id, f"@{call.from_user.username}, введите сумму на которую хотите пополнить кошелек в нашем боте:\nМинимальная сумма пополнения: 2₽")
    bot.register_next_step_handler(msg, input_pay)

def input_pay(message: Message):
    try:
        # преобразуем сумму, удаляем "к" и заменяем на "000"
        amount = int(message.text.replace("к", "000"))
    except ValueError:
        bot.send_message(message.chat.id, "Некорректная сумма пополнения")
        return 
    
    if amount < 2:
        bot.send_message(message.chat.id, "Минимальная сумма пополнения через ЮMoney -- 2₽")
        return 
    
    if amount > 3000:
        bot.send_message(message.chat.id, "Максимальная сумма пополнения через ЮMoney -- 3000₽")
        return 
    
    # == создаем 
    date = datetime.now()
    label = f"{message.from_user.id}_{date.isoformat()}"
    link = add_chet(amount, label)
    bot.send_message(message.chat.id, f"Заявка на сумму {amount:,.0f}₽ создана.\nПерейдите по ссылке и оплатите: {link}")


    check_payment(message.from_user.id, label, amount)

def check_payment(user_id, label, amount):
    start_time = time.time()
    client = Client(TOKEN_YOOMONEY)

    while time.time() - start_time < 60 * 5:  
        try:
            history = client.operation_history(label=label)
            for operation in history.operations:  
                if operation.status == "success":
                    bot.send_message(user_id, f"Ваш платёж в размере: {amount:,.0f}₽. Пополнение баланса успешно")
                    return 
            time.sleep(10)  
        except Exception as e:
            print(f"Error checking payment: {e}")
            time.sleep(5)  

    bot.send_message(user_id, "Время на оплату вышло.")

def add_chet(amount, label):
    quickpay = Quickpay(
        receiver=RECIVER, 
        quickpay_form="shop", 
        targets="Оплата",
        paymentType="SB", 
        sum=amount, 
        label=label
    )
    return quickpay.base_url

if __name__ == '__main__':
    #   Инициализация базы данных
    bot.infinity_polling()
    init_db()