from turtle import onclick
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
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
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
loc_button = Button(label="Get Location")
loc_button.js_on_event("button_click", CustomJS(code="""
    navigator.geolocation.getCurrentPosition(
        (loc) => {
            document.dispatchEvent(new CustomEvent("GET_LOCATION", {detail: {lat: loc.coords.latitude, lon: loc.coords.longitude}}))
        }
    )
    """))
result = streamlit_bokeh_events(
    loc_button,
    events="GET_LOCATION",
    key="get_location",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)
lat = 0 
lon = 0
if result:
    if "GET_LOCATION" in result:
        print(result.get("GET_LOCATION"))
    lat = result.get("GET_LOCATION")['lat']
    lon = result.get("GET_LOCATION")['lon']
print(busstopdata.index['Description' == busstopdata.iloc[i][1]])
closeby = [' ']
closebyent = [' ']
closebynum = [' ']
def busupdate(name):
    for i in range(len(closebyent)):
        if name == closeby[i][0]:
            st.table(getbus(closeby[i][1]))
def busupdatenum(num):
    st.table(getbus(num))

if lat != 0 and lon != 0:
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
    option = st.selectbox('Select the name of the bus stop',closebyent)
    optionnum = st.selectbox('Enter the bus stop code',closebynum)  
    if option != ' ':
        st.write('You selected:', option)  
        st.button(label='Refresh',on_click=busupdate(option))
    elif optionnum != ' ':
        st.write('You selected:', busstopdata.at[optionnum,'Description'])
        st.button(label='Refresh',on_click=busupdatenum(optionnum)) 
    else:
        st.write("You haven't selected anything")
