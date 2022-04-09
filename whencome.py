import requests
import json
import pandas as pd
import numpy as np
import time
import math
from math import radians ,cos, sin, asin, sqrt
import streamlit as st
import os 
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import pytz
from datetime import datetime
def select(ops,bus,data):
    if ops == []:
        return '-'
    else:
        text = ''
        if 'Bus operator' in ops:
            text += data.at['OriginCode','Operator']
        if 'Seats available' in ops and len(text) != 1:
            text += ' '+data.at['Load','NextBus']
        elif 'Seats available' in ops and len(text) < 1:
            text += data.at['Load','NextBus']
        if 'Vehicle type' in ops and len(text) != 1:
            text += ' '+data.at['Type',bus].replace("DD","2-deck").replace("SD","1-deck").replace("BD","Bendy")
        elif 'Vehicle type' in ops and len(text) < 1:
            text += data.at['Type',bus].replace("DD","2-deck").replace("SD","1-deck").replace("BD","Bendy")
        if 'Wheel-chair accessibility' in ops and len(text) != 1:
            text += ' '+data.at['Feature','NextBus']
        elif 'Wheel-chair accessibility' in ops and len(text) < 1:
            text += data.at['Feature','NextBus']
        return(text)

def process_time(times):
    if times != '':
        now = datetime.now(pytz.timezone('Asia/Singapore'))
        now = datetime.strptime(datetime.strftime(now,"%H:%M:%S"),"%H:%M:%S")
        arrival_time = datetime.strptime(times,"%H:%M:%S")
        if arrival_time < now:
            return("Arrived")
        else:
            output = (arrival_time-now)
            minutes,seconds = round(output.total_seconds()//60),round(output.total_seconds()%60)
            if len(str(minutes)) <2:
                minutes = '0'+str(minutes)
            if len(str(seconds)) <2:
                seconds = '0'+str(seconds)
            output = "{min}:{sec}".format(min=minutes,sec=seconds)
            return output
    else:
        return('-')
info = []
def getbus(code):
    partinfo = []    
    response = requests.get("http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2?BusStopCode="+str(code),headers = { 'AccountKey' : st.secrets['key'], 'accept' : 'application/json'})
    for i in range(len(response.json()['Services'])):
        df = pd.DataFrame.from_dict(response.json()['Services'][i])
        partinfo = ([df.at['OriginCode','ServiceNo'],process_time(df.at['EstimatedArrival','NextBus'][11:19]),select(options,'NextBus',df),process_time(df.at['EstimatedArrival','NextBus2'][11:19]),select(options,'NextBus2',df),process_time(df.at['EstimatedArrival','NextBus3'][11:19]),select(options,'NextBus3',df)])
        info.append(partinfo)
    myarray = np.array(info)
    bustimes = pd.DataFrame(myarray,columns=['Bus Number','1st Bus ETA(MM:SS)','1st Bus type','2nd Bus ETA(MM:SS)','2nd Bus type','3rd Bus ETA(MM:SS)','3rd Bus type'])
    bustimes = bustimes.set_index('Bus Number')
    bustimes = bustimes.sort_index()
    return(bustimes)
busstopdata = pd.DataFrame()
busstopdata = pd.read_excel(open("bus_stops.xlsx",'rb'),sheet_name='bus_stops')
busstopdata = busstopdata.set_index('BusStopCode')
closeby = []
closebyent = []
dist = []
def busupdate(name):
    for i in range(len(closebyent)):
        if name == closeby[i][0]:
            st.table(getbus(closeby[i][1]))
loc_button = Button(label="Get Location",width=0,background ="#000000")
loc_button.js_on_event("button_click", CustomJS(code="""
    navigator.geolocation.getCurrentPosition(
        (loc) => {
            document.dispatchEvent(new CustomEvent("GET_LOCATION", {detail: {lat: loc.coords.latitude, lon: loc.coords.longitude}}))})"""))
result = streamlit_bokeh_events(
    loc_button,
    events="GET_LOCATION",
    key="get_location",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)
lat,lon = 0,0
lats,lons = [],[]
if result:
    if "GET_LOCATION" in result:
        lat = result.get("GET_LOCATION")['lat']
        lon = result.get("GET_LOCATION")['lon']
        map_data = pd.DataFrame({'lat':[lat],'lon':[lon]})      
if lat != 0 and lon != 0:
    for i in range(busstopdata.shape[0]):
        coords1=(lat,lon)
        coords2 = (float(busstopdata.iloc[i][2]),float(busstopdata.iloc[i][3]))
        lon1 ,lat1,lon2,lat2 = map(radians,[coords1[1],coords1[0],coords2[1],coords2[0]])
        dlon = lon2 - lon1 
        dlat = lat2 - lat1
        #geopy.distance.geodesic(coords1, coords2).km
        if 6371*2*asin(sqrt(sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2))<0.5:
            closeby.append([busstopdata.iloc[i][1]+' ('+str(busstopdata[busstopdata['Description']==busstopdata.iloc[i][1]].index[0])+')',busstopdata[busstopdata['Description']==busstopdata.iloc[i][1]].index[0]])
            closebyent.append(busstopdata.iloc[i][1]+' ('+str(busstopdata[busstopdata['Description']==busstopdata.iloc[i][1]].index[0])+')')
            dist.append(6371*2*asin(sqrt(sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2)))
            lats.append(float(busstopdata.iloc[i][2]))
            lons.append(float(busstopdata.iloc[i][3]))
    lats.append(lat)
    lons.append(lon)
    plots = pd.DataFrame(data={'lat':lats,'lon':lons})
    busstops = {'Name':closebyent,'Distance':dist}
    busstopdf = pd.DataFrame(data=busstops)
    busstopdf['Distance'] = pd.to_numeric(busstopdf['Distance'])
    busstopdf = busstopdf.sort_values("Distance")
    options = st.multiselect('Select the info to show:',['Bus operator','Seats available','Vehicle type','Wheel-chair accessibility'])
    print(options)
    option = st.selectbox('Select the name of the bus stop',busstopdf['Name'])
    if option != ' ':
        st.write('You selected:', option)
        if 'Bus operator' in options:
            st.write('Bus operators:')
            st.write('SBST: SBS Transit')
            st.write('SMRT: SMRT Corporation')
            st.write('TTS: Tower Transit Singapore')
            st.write('GAS: Go Ahead Singapore')
        if  'Seats available'in options or'Wheel-chair accessibility' in options:
            optiontext = 'Legend:'
            if 'Seats available'in options:
                optiontext += ' SEA: seats available SDA: Standing available LSD: Limited standing'
            if 'Wheel-chair accessibility' in options:
                optiontext += ' WAB: Wheel-chair accessible'
            st.write(optiontext)
        st.button(label='Refresh',on_click=busupdate(option))
    else:
        st.write("You haven't selected anything")
    st.map(plots,zoom = 14)
