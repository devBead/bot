import telebot 
from telebot.types import Message
from settings.config import token, admin_id, base_name
import sqlite3 as sq 
from datetime import datetime 

conn = sq.connect(base_name); cursor = conn.cursor() 



bot = telebot.TeleBot(token=token)



def init_db():
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users (
                   user_id INTEGER PRIMARY KEY, 
                   data_reg TEXT
                   )''')
    
    conn.commit()




def register_user(user_id, data_reg):

    c = cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
    if c <= 0:
        cursor.execute("INSERT INTO users (user_id, data_reg) VALUES (?,?)", (user_id, data_reg))
        conn.commit()
    else:
        return 


@bot.message_handler(commands=['start'])
def start(message: Message):
    data_reg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = message.from_user.id 


    register_user(user_id, data_reg)
    bot.send_message(user_id, f"Спасибо за регистрацию, @{message.from_user.id}!")
    return


def get_info(user_id):
    i = cursor.execute("SELECT user_id, data_reg FROM users WHERE user_id = ?", (user_id,))
    return {
        "user_id": i[0],
        "data_reg": i[1]
    }

@bot.message_handler(commands=['menu', 'prof'])
def menu(message: Message):
    info = get_info(message.from_user.id); data_reg = info['data_reg']

    msg = f"@{message.from_user.username}, ваш профиль:"


if __name__ == '__main__':
    bot.polling(none_stop=True)


