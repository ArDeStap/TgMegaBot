import telebot, sqlite3, hashlib
from telebot import types
import requests

def GetTgBotAPIStructure():
    token = open('BOT_TOKEN', "r").readline()
    adminId = open('BOT_TOKEN', "r").readable()
    apiUrl = f'https://api.telegram.org/bot{token}/'
    return {'token': token,
            'adminId': adminId,
            'apiUrl': apiUrl}

bot = telebot.TeleBot(GetTgBotAPIStructure()['token'])

# Устанавливаем соединение с Базой Данных
def get_MainDb_connection():
  conn = sqlite3.connect('database.db')
  conn.row_factory = sqlite3.Row
  return conn

def get_TgDb_connection():
    conn = sqlite3.connect('TelegramUsersDB.db')
    conn.row_factory = sqlite3.Row
    return conn


def EncodeDataToSha(dataToEncode):
   return hashlib.sha3_512(dataToEncode.encode('latin-1')).hexdigest()

def GetUserByTgData(tg_data):
   con = get_MainDb_connection()
   encodedData = EncodeDataToSha(tg_data)
   user = con.execute('SELECT * FROM users WHERE tg_data = ? ', (encodedData,)).fetchone()
   con.close()
   return user 

def GetTgUserByUID(UID):
    con = get_TgDb_connection()
    user = con.execute('SELECT * FROM user_data WHERE users_id = ?', (UID,)).fetchone()
    con.close()
    return user

def insertTgUser(userData):
    con = get_TgDb_connection()
    curs = con.cursor()
    curs.execute('''INSERT INTO user_data (users_id, tg_data_json, rights_id, group_id) VALUES (?, ?, ?, ?)''', (userData['id'], userData['tgUser'], userData['rights_id'], userData['group_id']))
    con.commit()
    con.close()

def registerUser(usrData):
    # Хеширование пароля
    hashed_password = hashlib.sha256(usrData['password'].encode('utf-8')).hexdigest()

    # Подключение к нашей базе данных
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Добавление нового пользователя
    c.execute('INSERT INTO users (username, password, third_name, second_name, first_name) VALUES (?, ?, ?, ?, ?)', 
              [usrData['login'], hashed_password, usrData['o'], usrData['f'], usrData['i']])

    # Сохранение изменений и закрытие соединения с базой данных
    conn.commit()
    conn.close()

    messageToAdmin(usrData)

def constructUserTgData(msg):
      userData = {
          'id': str(msg.from_user.id),
          'username': str(msg.from_user.id)  
      }
      return userData

def messageToAdmin(userStructure):
    msg = f'User {userStructure['f']} {userStructure['i']} {userStructure['o']} has been registered'
    reqData = GetTgBotAPIStructure()
    requests.post(reqData['apiUrl']+'sendMessage', headers={ 'Content-Type': 'application/json', }, json={
        'chat_id': int(reqData['adminId']),
        'text': msg
    })


def addButtons(btnStructure, btnType, btnGrid):
    btnArray = []
    if btnType == 'inline':
        markup = types.InlineKeyboardMarkup()
        for button in btnStructure:
            btnArray.append(types.InlineKeyboardButton(button['text'], url=button['url'] if button['url'] != '' else None, callback_data=button['callback']))
        addBtnCount = 0
        for i in range(len(btnGrid)):
            colCount = 0
            for j in btnGrid[i]:
                if j:
                    colCount+=1
            markup.row(*btnArray[addBtnCount:colCount:1])
            addBtnCount += colCount
        return markup
    elif btnType == 'reply':
        markup = types.ReplyKeyboardMarkup()
        return markup


@bot.message_handler(commands=['start'])
def StartMessage(m):
    msgToSend = "TestBot\r\n\r\n"
    senderData = constructUserTgData(m)
    userData = GetUserByTgData(EncodeDataToSha(senderData['id']))
    if userData:
        msgToSend += f"Hello, {userData['first_name']}\r\n\r\n"
        TgUser = GetTgUserByUID(userData['id'])
        if not TgUser:
           msgToSend += "Welcome to your first time in TestBot. type /help for more info.\r\n\r\n"
           userData['tgUser'] = senderData
           insertTgUser(userData)
        else:
            msgToSend += "What you want to do?\r\n"
    else:
        msgToSend += f"Hello, {m.from_user.username}!\r\n"
        msgToSend += "Do you want to register your own profile?"   
        btnStructure = [
            {'text': 'YES', 'url': '', 'callback': 'register'},
            {'text': 'NO', 'url': '', 'callback': 'noRegister'}]
        btnGrid = [[True, True]]
        markup = addButtons(btnStructure, 'inline', btnGrid)    
    if 'markup' in locals():
       bot.send_message(m.chat.id, msgToSend, reply_markup=markup) 
    else:
       bot.send_message(m.chat.id, msgToSend)

@bot.callback_query_handler(func= lambda callback: True)
def callback_message(callback):
    if callback.data == 'register':
        mesg = bot.send_message(callback.message.chat.id, "Введите свой логин")               
        bot.register_next_step_handler(mesg, login_send)

def login_send(message):
    usrData = {}
    usrData['login'] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите пароль')
    bot.register_next_step_handler(mesg, password_send, usrData)

def password_send(message, usrData):
    usrData['password'] = message.text
    mesg = bot.send_message(message.chat.id, 'Введите ФИО через пробелы')
    bot.register_next_step_handler(mesg, fio_send, usrData)

def fio_send(message, usrData):
    usrFio = message.text.split(' ')
    if len(usrFio) < 2:
        mesg = bot.send_message(message.chat.id, 'Неправильно введены данные!\r\nВведите ФИО через пробелы')
        bot.register_next_step_handler(mesg, fio_send, usrData)
    else:
        if len(usrFio) == 2:
            usrData['i'] = usrFio[1]
            usrData['f'] = usrFio[0]
            usrData['o'] = ' '
            usrData['tgId'] = str(message.from_user.id)
            registerUser(usrData)
        else:
            usrData['i'] = usrFio[1]
            usrData['f'] = usrFio[0]
            usrData['o'] = str(*usrFio[2:len(usrFio)-1:1])
            usrData['tgId'] = str(message.from_user.id)
            registerUser(usrData)
       


bot.infinity_polling()