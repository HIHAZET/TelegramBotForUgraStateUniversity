import time
from datetime import datetime, timedelta
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import requests
import json

token = "Telegram Token"
bot = AsyncTeleBot(token)


apiUrl = "https://www.ugrasu.ru/api/directory/"

nowDay = datetime.now()
#Создание клавиатуры
keyboard = types.ReplyKeyboardMarkup()
keyboard.add(types.KeyboardButton(text="Прошлая неделя"))
keyboard.add(types.KeyboardButton(text="Текущая неделя"))
keyboard.add(types.KeyboardButton(text="Следующая неделя"))

#Смена недели на прошлую или будущую
def changeWeek(inFuture: bool):

    if inFuture:
        newWeek = nowDay + timedelta(days=7)
    else:
        newWeek = nowDay - timedelta(days=7)

    return newWeek

#Получение начала и конца недели, относительно выбранной недели
def GetStartAndEndWeek():
    start = nowDay - timedelta(days=nowDay.weekday())
    end = start + timedelta(days=6)
    return [start.strftime('%Y-%m-%d'),end.strftime('%Y-%m-%d'),nowDay.strftime('%Y-%m-%d')]

#Получение ответа от апи
def getResponseApi(req):
    return json.loads(str(requests.get(apiUrl + req).text))

#Получение расписания студентов
def getScheduleInGroupStudents(studentId):

    if studentId == None:
        return None

    week = GetStartAndEndWeek()
    schedule = getResponseApi(f"lessons?fromdate={week[0]}&todate={week[1]}&groupOid={studentId}")

    lessions = []
    for lession in schedule:
        day = lession['dayOfWeekString']
        startTime = lession['beginLesson']
        endTime = lession['endLesson']
        discipline = lession['discipline']
        kindOfWork = lession['kindOfWork']
        auditorium = lession['auditorium']
        teacher = lession['lecturer']
        stream = lession['stream']

        if stream == None:
            stream = ""
        lessions.append({'dayOfWeekString':day, 'startTime':startTime, 'endTime':endTime, 'teacher':teacher, 'discipline':discipline, 'kindOfWork':kindOfWork, 'auditorium':auditorium,'stream':stream})
    return lessions

#Получение расписания для преподавателей
def getScheduleForTeacher(teacherId):

    if teacherId == None:
        return None

    week = GetStartAndEndWeek()
    schedule = getResponseApi(f"lessons?fromdate={week[0]}&todate={week[1]}&lecturerOid={teacherId}")

    lessions = []

    for lession in schedule:
        startTime = lession['beginLesson']
        endTime = lession['endLesson']
        group = getGroup(lession['groupOid'])
        stream = lession['stream']
        groupName = ""
        if group != None:
            groupName = group[0]
        else:
            groupName = stream
        discipline = lession['discipline']
        auditorium = lession['auditorium']
        kindOfWork = lession['kindOfWork']
        dayOfWeekString = lession['dayOfWeekString']

        lessions.append({'dayOfWeekString':dayOfWeekString,'startTime':startTime,'endTime':endTime,'group':groupName,'discipline':discipline,'kindOfWork':kindOfWork,'auditorium':auditorium})

    return lessions

#Получение id преподавателя
def getTeacher(message):
    teachers = getResponseApi("lecturers")
    for teacherInfo in teachers:
        if message in teacherInfo['shortFIO']:
            return teacherInfo['lecturerOid']

    return None

#Получение данных об группе
def getGroup(groupId):
    groups = getResponseApi("groups")
    for group in groups:
        if groupId == group['groupOid'] or groupId == group['name']:
            try:
                return [group['name'],group['speciality'],group['groupOid']]
            except:
                return None
    return None

#Получение текста для отправки пользователю
def getOutputScheduleForTeacher(schedule):
    #{'dayOfWeekString':dayOfWeekString,'startTime':startTime,'endTime':endTime,'group':groupName,'discipline':discipline,'kindOfWork':kindOfWork,'auditorium':auditorium}

    if len(schedule) == 0:
        return {'output':None,'listOutputs':[]}

    output = ""
    lastDay = ""
    listOutputs = []
    for lession in schedule:
        sep = ""
        if(lastDay != lession['dayOfWeekString']):
            sep = f"==========<b>{lession['dayOfWeekString']}</b>===========\n"
            lastDay = lession['dayOfWeekString']
        output += f"{sep}<i>{lession['startTime']}</i>-<i>{lession['endTime']}</i>\n" \
                  f"  {lession['discipline']} {lession['group']} {lession['auditorium']}\n" \
                  f"  {lession['kindOfWork']}" \
                  f"\n \n"
        listOutputs.append(f"{sep}<b>{lession['startTime']}</b>-<b>{lession['endTime']}</b>\n" \
                  f"  {lession['discipline']} {lession['group']} {lession['auditorium']}\n" \
                  f"  {lession['kindOfWork']}")
    return {'output':output,'listOutputs':listOutputs}

#Получение текста для отправки пользователю
def getOutputScheduleForStudents(schedule):
    #{'dayOfWeekString':dayOfWeekString, 'startTime':startTime, 'endTime':endTime, 'teacher':teacher, 'discipline':discipline, 'kindOfWork':kindOfWork, 'auditorium':auditorium}

    if schedule == None or schedule == "Нет занятий!":
        return {'output':None,'listOutputs':[]}

    output = ""
    lastDay = ""
    listOutputs = []
    for lession in schedule:
        sep = ""
        if (lastDay != lession['dayOfWeekString']):
            sep = f"==========<b>{lession['dayOfWeekString']}</b>===========\n"
            lastDay = lession['dayOfWeekString']


        output += f"{sep}<i>{lession['startTime']}</i>-<i>{lession['endTime']}</i>\n" \
                  f"  {lession['discipline']} | {lession['teacher']}\n" \
                  f"  {lession['auditorium']}\n" \
                  f"  {lession['kindOfWork']}\n" \
                  f"  {lession['stream']}\n" \
                  f"\n \n"
        listOutputs.append(f"{sep}<i>{lession['startTime']}</i>-<i>{lession['endTime']}</i>\n" \
                  f"  {lession['discipline']} | {lession['teacher']}\n" \
                  f"  {lession['auditorium']}\n" \
                  f"  {lession['kindOfWork']}\n" \
                  f"  {lession['stream']}")
    return {'output':output,'listOutputs':listOutputs}

#Отправка сообщения для помощи
@bot.message_handler(commands=["start"])
async def sendHelp(message):

    await bot.send_message(message.chat.id,"Для получения информации нужно ввести ФИО или название группы.\n"
                                           "Пример: Евсеенко Е.А\nПример: 3ф21бу",parse_mode="HTML",reply_markup=keyboard)

#Обработчик основных сообщений
@bot.message_handler(func=lambda message: True)
async def handlerMessages(message):

    if message.text == "Прошлая неделя":
        globals()['nowDay'] = changeWeek(False)
        await bot.send_message(message.chat.id, f"Выбрана неделя: <b>{nowDay.strftime('%Y-%m-%d')}</b>",
                               reply_markup=keyboard,parse_mode="HTML")
        return

    if message.text == "Следующая неделя":
        globals()['nowDay'] = changeWeek(True)
        await bot.send_message(message.chat.id, f"Выбрана неделя: <b>{nowDay.strftime('%Y-%m-%d')}</b>",
                               reply_markup=keyboard,parse_mode="HTML")
        return

    if message.text == "Текущая неделя":
        globals()['nowDay'] = datetime.now()
        await bot.send_message(message.chat.id, f"Выбрана неделя: <b>{nowDay.strftime('%Y-%m-%d')}</b>",
                               reply_markup=keyboard,parse_mode="HTML")
        return


    await bot.send_message(message.chat.id,"Идёт поиск...",reply_markup=keyboard)

    teacher = getTeacher(message.text)
    group = getGroup(message.text)

    if teacher != None:
        scheduleTeacher = getScheduleForTeacher(teacher)
        output = getOutputScheduleForTeacher(scheduleTeacher)
        if output['output'] == None:
            output['output'] = "Нет занятий!"

        if len(output['output']) < 4000:
            await bot.send_message(message.chat.id, output['output'],parse_mode="HTML",reply_markup=keyboard)
        else:
            for lession in output['listOutputs']:
                await bot.send_message(message.chat.id, lession,reply_markup=keyboard,parse_mode="HTML")
                time.sleep(0.2)
    elif group != None:
        scheduleStudents = getScheduleInGroupStudents(group[2])

        if scheduleStudents == None or len(scheduleStudents) <= 0:
            scheduleStudents = "Нет занятий!"
            await bot.send_message(message.chat.id, scheduleStudents, reply_markup=keyboard)
            return

        output = getOutputScheduleForStudents(scheduleStudents)

        if output == None or len(output['output']) <= 0:
            output['output'] = "Нет занятий!"

        if len(output['output']) < 4000:
            await bot.send_message(message.chat.id,output['output'],parse_mode="HTML",reply_markup=keyboard)
        else:
            for lession in output['listOutputs']:
                await bot.send_message(message.chat.id, lession,reply_markup=keyboard,parse_mode="HTML")
                time.sleep(0.2)

    else:
        await bot.send_message(message.chat.id, "Для получения информации нужно ввести ФИО или название группы.\n"
                                                "Пример: Евсеенко Е.А\nПример: 3ф21бу",reply_markup=keyboard)

    await bot.send_message(message.chat.id, "Поиск окончен", reply_markup=keyboard, parse_mode="HTML")

#Запуск бота
import asyncio
asyncio.run(bot.polling())

