import mysql.connector
import datetime as dt
import requests
import telegram
import time

# key and id for telegram bot
key = '1902150125:AAGKzqptH_gOK2D2Xv13veNb733ATzMtuOo'
chat_id = 1940115787

data_retrieved = False

def connect():
      return mysql.connector.connect(
            host="localhost",
            user="ronsio",
            passwd="YMALQPxnskwo1029!",
            database="django_site"
      )

# function for retrieving sleep data from oura api fro current day
def sleep_score(token, days):
      today = (dt.datetime.now() - dt.timedelta(days=days)).date().strftime('%Y-%m-%d')
      data = requests.get('https://api.ouraring.com/v1/sleep?start=' + today + '&end=' + today + '&access_token=' + token).json()
      d = {}
      d['score'] = data['sleep'][0]['score']
      d['timestamp'] = (dt.datetime.now() - dt.timedelta(days=days - 1)).date().strftime('%Y-%m-%d %H:%M:%S')
      d['duration'] = data['sleep'][0]['total']
      d['time_in_bed'] = data['sleep'][0]['duration']
      d['efficency'] = data['sleep'][0]['efficiency']
      d['restfulness'] = data['sleep'][0]['score_disturbances']
      d['rem'] = data['sleep'][0]['rem']
      d['deep'] = data['sleep'][0]['deep']
      d['light'] = data['sleep'][0]['light']
      d['latency'] = data['sleep'][0]['score_latency']
      d['heartrate'] = data['sleep'][0]['hr_average']
      
      return d

# function fro retrieving activity data
def activity_score(token, days):
      today = (dt.datetime.now() - dt.timedelta(days=days - 1)).date().strftime('%Y-%m-%d')
      data = requests.get('https://api.ouraring.com/v1/activity?start=' + today + '&end=' + today + '&access_token=' + token).json()

      d = {}
      d['timestamp'] = (dt.datetime.now() - dt.timedelta(days=days - 1)).date().strftime('%Y-%m-%d %H:%M:%S')
      d['activity_score'] = data['activity'][0]['score']
      d['steps'] = data['activity'][0]['steps']
      d['calories'] = data['activity'][0]['cal_total']
      d['score_meet_daily_targets'] = data['activity'][0]['score_meet_daily_targets']
      d['score_recovery_time'] = data['activity'][0]['score_recovery_time']
      d['score_training_volume'] = data['activity'][0]['score_training_volume']

      return d

# function for fetching readiness score
def readiness_score(token, days):
      today = (dt.datetime.now() - dt.timedelta(days=days)).date().strftime('%Y-%m-%d')
      data = requests.get('https://api.ouraring.com/v1/readiness?start=' + today + '&end=' + today + '&access_token=' + token).json()

      d = {}
      d['timestamp'] = (dt.datetime.now() - dt.timedelta(days=days)).date().strftime('%Y-%m-%d %H:%M:%S')
      d['score'] = data['readiness'][0]['score']

      return d

while data_retrieved == False:

      # connecting to sqlitedatabase
      db = connect()

      # setting day difference to one to retrieve data from yesterday
      days = 1

      # starting sqlite cursor
      c = db.cursor()

      # creating datestring for request
      today = (dt.datetime.now() - dt.timedelta(days=1)).date().strftime('%Y-%m-%d %H:%M:%S')

      # request for sleep data
      try:
            # writing readiness_score into databse
            d = readiness_score('JW5REMSG7S64QOWCEGEOHTVDCLYVTJGG', days)
            c.execute("INSERT INTO dashboard_readiness (timestamp, readiness_score) VALUES (%s, %s)", (d['timestamp'], d['score']))

            d = sleep_score('JW5REMSG7S64QOWCEGEOHTVDCLYVTJGG', days)

            # writing to sqlite database
            c.execute("INSERT INTO dashboard_sleep (timestamp, sleep_score, duration, time_in_bed, efficency, restfulness, rem, deep, light, latency, heartrate) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (d['timestamp'], d['score'], d['duration'], d['time_in_bed'], d['efficency'], d['restfulness'], d['rem'], d['deep'], d['light'], d['latency'], d['heartrate']))

            # request for acitivity data
            d = activity_score('JW5REMSG7S64QOWCEGEOHTVDCLYVTJGG', days)

            # writing to sqlite database
            c.execute("INSERT INTO dashboard_activity (timestamp, activity_score, steps, calories, score_meet_daily_targets, score_recovery_time, score_training_volume) VALUES (%s,%s,%s,%s,%s,%s,%s)", (d['timestamp'], d['activity_score'], d['steps'], d['calories'], d['score_meet_daily_targets'], d['score_recovery_time'], d['score_training_volume']))
            
            # update activity data from yesterday
            d = activity_score('JW5REMSG7S64QOWCEGEOHTVDCLYVTJGG', days + 1)
            # deleting old data
            c.execute("DELETE FROM dashboard_activity WHERE timestamp = %s", ((dt.datetime.now() - dt.timedelta(days=days)).date().strftime('%Y-%m-%d %H:%M:%S'),))
            # inserting new data
            c.execute("INSERT INTO dashboard_activity (timestamp, activity_score, steps, calories, score_meet_daily_targets, score_recovery_time, score_training_volume) VALUES (%s,%s,%s,%s,%s,%s,%s)", (d['timestamp'], d['activity_score'], d['steps'], d['calories'], d['score_meet_daily_targets'], d['score_recovery_time'], d['score_training_volume']))

            db.commit()
            db.close()
            
            bot = telegram.Bot(token=key)
            bot.send_message(text='Oura data for {datum} added to database!'.format(datum=dt.datetime.now().strftime('%Y-%m-%d')), chat_id=chat_id)
            data_retrieved = True

      except IndexError:
            db.commit()
            db.close()
            waiting_time = 60*5
            bot = telegram.Bot(token=key)
            bot.send_message(text='Oura data for today is not available yet! Trying again in {time} seconds!'.format(time=waiting_time), chat_id=chat_id)
            time.sleep(waiting_time)