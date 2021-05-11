#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
from twilio.rest import Client
from dotenv import load_dotenv
from cowin_api import CoWinAPI
import datetime, time
import pandas as pd
import numpy as np


# In[2]:


def get_district_id(state, district):
    cowin = CoWinAPI()
    states = cowin.get_states()
    state = [i for i in states["states"] if state in i["state_name"].lower()]

    districts = cowin.get_districts(state[0]["state_id"])
    district = [
        i for i in districts["districts"] if district in i["district_name"].lower()
    ]

    district_id = str(district[0]["district_id"])
    return district_id


def createDf(listInput):
    dfNull = {
        "date": "N/A",
        "vaccine": "N/A",
        "name": "N/A",
        "address": "N/A",
        "district_name": "N/A",
        "block_name": "N/A",
        "pincode": "N/A",
        "min_age_limit": "N/A",
        "fee_type": "N/A",
        "available_capacity": "N/A",
    }
    if len(listInput) == 0:
        return pd.DataFrame(dfNull, index=[0])
    else:
        baseDict = listInput
        info = []
        for i in baseDict:
            relevantData = dict(
                (key, value)
                for key, value in i.items()
                if key
                in [
                    "name",
                    "fee_type",
                    "sessions",
                    "address",
                    "block_name",
                    "district_name",
                    "pincode",
                ]
            )
            relevantData["available_capacity"] = relevantData["sessions"][0][
                "available_capacity"
            ]
            relevantData["min_age_limit"] = relevantData["sessions"][0]["min_age_limit"]
            relevantData["vaccine"] = relevantData["sessions"][0]["vaccine"]
            relevantData["date"] = relevantData["sessions"][0]["date"]
            del relevantData["sessions"]
            info.append(relevantData)

        df = pd.DataFrame(info)
        df_final = df[
            [
                "date",
                "vaccine",
                "name",
                "address",
                "block_name",
                "min_age_limit",
                "available_capacity",
            ]
        ]
        return pd.DataFrame(df_final)
    


# In[3]:


def get_availability(
    date,
    min_age=18,
    state="Bihar",
    districts=["Patna", "Muzaffarpur", "Vaishali"],
    blocks=["Saraiya", "Vaishali", "Paroo"],
):
    cowin = CoWinAPI()
    data = pd.DataFrame([])
    for district in districts:
        dist = get_district_id(state.lower(), district.lower())
        avail = cowin.get_availability_by_district(dist, date, min_age)
        data1 = createDf(avail["centers"])
        data = pd.concat([data, data1])

    vac = pd.DataFrame([])
    for block in blocks:
        vac1 = data[data["block_name"] == block]
        vac = pd.concat([vac, vac1])
    vac = vac.reset_index().drop(["index"], axis=1)
    
    columns = ['date', 'vaccine', 'available_capacity', 'name', 'min_age_limit']
    vac = vac[columns]
    return vac

def get_data(num_days=10):
    date1 = datetime.date.today()
    df = pd.DataFrame([])
    for day in range(num_days):
        date = date1 + datetime.timedelta(days=day)
        date = date.strftime("%d-%m-%Y") 
        print('Retrieving data for %s'%date)
        data = get_availability(date, age)
        df = pd.concat([df, data]) 
    df = df.sort_values(by = 'available_capacity', ascending=False)
    return df

def build_message_text(data):
    msg = ''
    if data['available_capacity'].sum():
        header = 'Vaccines available for nearby Center. See below table for information. \n\n '
    else:
        header = 'No Vaccine slots available. \n\n '
        
    for line in data.values:
        lline = list(line)
        lline = ' | '.join([str(n) for n in lline]) + ' \n '
        #newline = '|'.join(list(line))
        msg = msg + lline 
        #print(lline)
    msg = header + msg
    return msg

def send_msg(mobile_number, msg):
    load_dotenv()
    TWILIO_ACCOUNT_SID = os.environ.get("ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
    FROM_WHATSAPP_NUMBER = os.environ.get("FROM_WHATSAPP_NUMBER")
    FROM_SMS_NUMBER = os.environ.get("FROM_SMS_NUMBER")
    client = Client()
    client.messages.create(
        body=msg,
        from_=FROM_WHATSAPP_NUMBER,
        to="whatsapp:" + mobile_number,
    )


# In[4]:


age = 18      
num_days = 3  # Number of Days to look vaccine slots for
interval = 10  # time interval at which to check the vaccine splots [in seconds]

mobile1 = "+917061255xxx" # Mobile number with country code
    
counter = 0
while True:
    if counter == 0:
        data = get_data(num_days)
        counter = data['available_capacity'].sum()
        msg = build_message_text(data)
        send_msg(mobile1, msg) 
        time.sleep(interval)
    else:
        print('Vaccine slots found.')
        break 
        
print("Script run over!!")

