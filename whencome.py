import requests
import json
import pandas as pd
import numpy as np
import time
from datetime import datetime
import math
from math import radians ,cos, sin, asin, sqrt
import streamlit as st
import os 
def process_time(times):
    if times != '':
        now = datetime.now()
        now = datetime.strptime(datetime.strftime(now,"%H:%M:%S"),"%H:%M:%S")
        arrival_time = datetime.strptime(times,"%H:%M:%S")
        if arrival_time < now:
            return("Arrived")
        else:
            output = (arrival_time-now)
            output = str(output)
            return output
    else:
        return('-')
info = []


def getbus(code):
    partinfo = []
    
    response = requests.get("http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2?BusStopCode="+code,headers = { 'AccountKey' : 'qV1hBipQTZiK4AHSYmS92Q==', 'accept' : 'application/json'})
    for i in range(len(response.json()['Services'])):
        
        df = pd.DataFrame.from_dict(response.json()['Services'][i])
        partinfo = ([df.at['OriginCode','ServiceNo'],process_time(df.at['EstimatedArrival','NextBus'][11:19]),df.at['Type','NextBus'].replace("DD","Double-deckered").replace("SD","Single-deckered"),process_time(df.at['EstimatedArrival','NextBus2'][11:19]),df.at['Type','NextBus2'].replace("DD","Double-deckered").replace("SD","Single-deckered"),process_time(df.at['EstimatedArrival','NextBus3'][11:19]),df.at['Type','NextBus3'].replace("DD","Double-deckered").replace("SD","Single-deckered")])
        info.append(partinfo)
    myarray = np.array(info)
    bustimes = pd.DataFrame(myarray,columns=['Bus Number','1st Bus ETA','1st Bus type','2nd Bus ETA','2nd Bus type','3rd Bus ETA','3rd Bus type'])
    return(bustimes)
#print(response.json())
bus_stops = requests.get("http://datamall2.mytransport.sg/ltaodataservice/BusStops",headers = { 'AccountKey' : 'qV1hBipQTZiK4AHSYmS92Q==', 'accept' : 'application/json'})
busstopdata = pd.DataFrame.from_dict(bus_stops.json()['value'])

for i in range(10):
    bus_stops = requests.get("http://datamall2.mytransport.sg/ltaodataservice/BusStops?$skip="+str((i+1)*500),headers = { 'AccountKey' : 'qV1hBipQTZiK4AHSYmS92Q==', 'accept' : 'application/json'})
    busstopdata = pd.concat([busstopdata,pd.DataFrame.from_dict(bus_stops.json()['value'])])
busstopdata = busstopdata.set_index('BusStopCode')
print(busstopdata)

lat,lon = os.popen('curl ipinfo.io/loc').read().split(',')
print(lat,lon)
print(busstopdata.index['Description' == busstopdata.iloc[i][1]])
closeby = []
closebyent = []
closebynum = []
for i in range(busstopdata.shape[0]):
    coords1=(float(lat),float(lon))
    coords2 = (float(busstopdata.iloc[i][2]),float(busstopdata.iloc[i][3]))
    lon1 ,lat1,lon2,lat2 = map(radians,[coords1[1],coords1[0],coords2[1],coords2[0]])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1
    
    #geopy.distance.geodesic(coords1, coords2).km
    if 6371*2*asin(sqrt(sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2))<1:
        closeby.append([busstopdata.iloc[i][1],busstopdata[busstopdata['Description']==busstopdata.iloc[i][1]].index[0]])
        closebyent.append(busstopdata.iloc[i][1])
        closebynum.append(busstopdata[busstopdata['Description']==busstopdata.iloc[i][1]].index[0])

letnum = 0
def letter():
    global letnum
    letnum = 0
def number():
    global letnum
    letnum = 1
option = st.selectbox('Select the name of the bus stop',closebyent,on_change=letter())
optionnum = st.selectbox('Enter the bus stop code',closebynum,on_change=number())
if letnum == 0:
    st.write('You selected:', option)
else:
    st.write('You selected:', busstopdata.at[optionnum,'Description'])


def busupdate(name):
    for i in range(len(closebyent)):
        if name == closeby[i][0]:
            st.table(getbus(closeby[i][1]))
def busupdatenum(num):
    st.table(getbus(num))
print(letnum)
if letnum == 0:
    st.button(label='Refresh',on_click=busupdate(option))
else:
    st.button(label='Refresh',on_click=busupdatenum(optionnum))