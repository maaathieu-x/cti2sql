#!/usr/bin/python3

import configparser
import requests
import json
import mysql.connector
from mysql.connector import errorcode
import datetime
import logging
import os 
import websocket
import sys
import sdnotify
import signal

config = configparser.ConfigParser()
config.read(os.path.dirname(sys.argv[0]) + '/cti2sql.conf')

config_sql = {
        'user': config['sql']['user'],
        'password': config['sql']['password'],
        'host': config['sql']['host'],
        'database': config['sql']['database'],
        'raise_on_warnings': True,
}

def signal_handler(sig, frame):
    if 'cursor' in vars():
        cursor.close()
    if 'cnx' in vars():
        cnx.close()
    if 'ws' in vars():
        ws.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

logging.basicConfig(filename=config['misc']['log_file'],level=logging.WARNING)

logging.warning(str(datetime.datetime.today()) + " cti2sql starting ")

token = config['ovh']['token'] 


urlv2 = config['ovh']['endpoint']


def on_error(ws, error):
    logging.warning(f"Erreur {error}")
    #print(f"Erreur {error}")

def on_close(ws):
    #print("### closed ###")
    pass
    #ws.run_forever()

def on_open(ws):

    ws.send('')

def on_message(ws, message):
    try:
        n = sdnotify.SystemdNotifier()
        event = json.loads(message)
        #print(event)
        #print(res)

        cnx = mysql.connector.connect(**config_sql)
        cursor = cnx.cursor(buffered=True)
        #print(res)
        #print(type(res))

        #print(event["event"])
        if event["event"] == "member-queue-end":
            #print(event)
            pass
        if "event" in event:
            if event["event"] == "member-queue-end":
                if event["data"]["QueueCause"] == "Terminated":
                    QueueMemberJoinedTime = datetime.datetime.fromtimestamp(int(event["data"]["QueueMemberJoinedTime"])).strftime('%Y-%m-%d %H:%M:%S')
                    QueueAgentAnsweredTime = datetime.datetime.fromtimestamp(int(event["data"]["QueueAgentAnsweredTime"])).strftime('%Y-%m-%d %H:%M:%S')
                    QueueMemberLeavingTime = datetime.datetime.fromtimestamp(int(event["data"]["QueueMemberLeavingTime"])).strftime('%Y-%m-%d %H:%M:%S')
                    query = "insert into events (`QueueMemberSessionUUID`, `Calling`, `QueueMemberJoinedTime`, `QueueAgentAnsweredTime`, `Agent`, `QueueMemberLeavingTime`, `QueueCause`) VALUES ('" + event["data"]["QueueMemberSessionUUID"]+ "', '" + event["data"]["Calling"] + "', '" + QueueMemberJoinedTime + "', '" + QueueAgentAnsweredTime + "', '" + event["data"]["Agent"] + "', '" + QueueMemberLeavingTime + "', 'Terminated');" 
                    cursor.execute(query)
                    cnx.commit()
                elif event["data"]["QueueCause"] == "Cancel":
                    QueueMemberJoinedTime = datetime.datetime.fromtimestamp(int(event["data"]["QueueMemberJoinedTime"])).strftime('%Y-%m-%d %H:%M:%S')
                    QueueMemberLeavingTime = datetime.datetime.fromtimestamp(int(event["data"]["QueueMemberLeavingTime"])).strftime('%Y-%m-%d %H:%M:%S')
                    query = "insert into events (`QueueMemberSessionUUID`, `Calling`, `QueueMemberJoinedTime`, `QueueMemberLeavingTime`, `QueueCause`) VALUES ('" + event["data"]["QueueMemberSessionUUID"]+ "', '" + event["data"]["Calling"] + "', '" + QueueMemberJoinedTime + "', '" + QueueMemberLeavingTime + "', 'Cancel');"
                    cursor.execute(query)
                    cnx.commit()

        if message == "Session not found\n":
            ws.keep_running = False
        else:
            pass
            #pass
            #logging.warning(str(datetime.datetime.today()) + " not a requests response")
    except mysql.connector.Error as err:
        #print(f"Erreur {err}")
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logging.warning(str(datetime.datetime.today()) + " Something is wrong with your user name or password")
            #print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logging.warning(str(datetime.datetime.today()) + " Database does not exists")
            #print("Database does not exists")
        else:
            logging.warning(str(datetime.datetime.today()) + " sql error: " + str(err.args) + " " + str(err.errno))
            #print("sql error: " + str(err.args) + " " + str(err.errno))
    except ValueError:
        #print(f"Erreur value error")
        logging.warning(str(datetime.datetime.today()) + " value error")
    except requests.exceptions.ReadTimeout:
        #print(f"Erreur timeout")
        logging.warning(str(datetime.datetime.today()) + " requests timeout")
    except Exception as e:
        logging.warning(str(datetime.datetime.today()) + " erreur2 " + str(e.args))
        #print(f"Erreur {e}")
    finally:
        if 'cursor' in vars():
            cursor.close()
            #print('cursor ferme')
        if 'cnx' in vars():
            cnx.close()
            #print('connexion fermee')


if __name__ == "__main__":
    n = sdnotify.SystemdNotifier()
    n.notify("READY=1")
    while 1:
        logging.warning(str(datetime.datetime.today()) + " requesting new session")
        #print("requesting new session")
        session = json.loads(requests.post("https://" + urlv2 + "/session", data = {}).text)
        id = session["id"]
        assoc = requests.post("https://" + urlv2 + "/session/" + id + "/subscribe/" + token, data = {})

        logging.warning(str(datetime.datetime.today()) + " session created, id " + id)
        #print("session created, id " + id)

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp("wss://" + urlv2 + "/session/" + id + "/events/websocket",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close,
                              on_open = on_open)
        ws.run_forever()

