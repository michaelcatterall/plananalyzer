# type: ignore
"""Welcome to Pynecone! This file outlines the steps to create a basic app."""
from pcconfig import config

import pynecone as pc

import random
import requests
import json
import bs4 as bs
import pandas as pd

secData = pd.DataFrame({})
i_interval = []

class planState(pc.State):    
    
    gendersJson: str
    gendersStatus: str
    TSS : int
    IF: int
    VI: int
    zoneList : list
    username = ''
    email = ''
    password = ''
    userId = ''
    planName = ''
    token = ''

    def plananalysisPage(self):
        return pc.redirect('/plananalysis')

    def tokenGet(self) : 

        #stages tenant
        tenantId = '6B0D62EB-675B-497F-9394-711DD1629F9D'
        tokenRequestUrl = 'https://identity.stagescloud.com/connect/token'
        tokenRequestHeaders = {'Content-Type': 'application/x-www-form-urlencoded'}
        tokenRequestData = {
            'client_id':'studio-home-app',
            'grant_type':'password',
            'username': self.username,
            'password': self.password,
            'acr_values':'tenant:' + tenantId
        }

        tokenRequest = requests.post(tokenRequestUrl, headers = tokenRequestHeaders, data = tokenRequestData)
        self.gendersStatus = tokenRequest.status_code
        
        if tokenRequest.status_code == 200:
            tokenResponse = (tokenRequest)
            self.token = tokenResponse.json()['access_token']
            return pc.redirect('/plananalysis')
        else:
            return pc.window_alert('Error logging in. Check ')
        
        


        
    def getPlanDetails(self):

        secData = pd.DataFrame({})
        dummyFTP = 100
        sec = 1
        secTot = 1

        api_call_headers = {'Authorization': 'Bearer ' + self.token}
        
        user_api_url = 'https://stagescloud.com/api/v0.1/Users/'
        userParms = {'query': self.username}
        user_get = requests.get(user_api_url, headers=api_call_headers, verify=True, params=userParms)
        userJson = user_get.json()
        for u in userJson['result']:
            self.userId = u['id']


        #get plan for user parms
        planSearch_api_url = 'https://stagescloud.com/api/v0.1/Plans/'
        planSearch_parms = {"query": self.planName, "userId": self.userId, "plansType": 1}
        PlanSearch_api_call_responseGet = requests.get(planSearch_api_url, headers = api_call_headers, verify = True, params = planSearch_parms)
        
        planSearch_response = (PlanSearch_api_call_responseGet).json()
        print(planSearch_response)
        if planSearch_response['totalRecords'] == 0:
            return pc.window_alert('No plans found')
        elif planSearch_response['totalRecords'] >1:
            return pc.window_alert('Multiple plans found - please narrow search')

        for p in planSearch_response['result']:
            print("plan name: ", p['name'], "    planId: ", p['id'], "user initials: ", p['userInitials'])
            #get plan details
            plan_api_url = 'https://stagescloud.com/api/v0.1/Plans/' + str(p['id']) + "/xml"
            api_call_responseGet = requests.get( plan_api_url, headers = api_call_headers, verify = True)
        
            soupXml = bs.BeautifulSoup(api_call_responseGet.text, 'lxml')

            i_count = 0
            
            x_duration = soupXml.find_all("interval")

            data = []
            count = 0
            for i in x_duration:
                count += 1
                row = [count, int(i["duration"]), int(i["value"])]
                data.append(row)


            #build per second intervals
            for i_data in data:
                while sec <= i_data[1]:
                        if secTot == 2172:
                            print(i_data)
                        new_row = {"secTot" : secTot, "power": i_data[2] * dummyFTP / 100, "zonePercent" : i_data[2]}
                        #print(new_row)
                        #secData = secData.append(new_row, ignore_index=True)
                        secData = pd.concat([secData, pd.DataFrame([new_row])])
                        sec += 1
                        secTot += 1
                else: 
                    sec = 1
            #return pc.window_alert(secData[0])
            #print(secData)
            
            
            secData['moving'] = secData['power'].rolling(30, min_periods=1).mean()
            testsum = 0
            for i, row in secData.iterrows():
                testsum += row['moving']    
            
            secData['movingFour'] = secData.apply(lambda row: pow(int(row['moving']),4), axis=1)
            print(secData.mean(axis=0))
            
            #totTime = time.gmtime(round(secData.iloc[-1]['secTot']))
            NP = round((secData['movingFour'].sum()  / secTot ) **0.25)
            self.IF = round(NP / dummyFTP,2)
            self.TSS = round(self.IF**2*secTot/36)
            self.VI = round(secData['power'].mean() / NP, 1)

            z1=0
            z2=0
            z3=0
            z4=0
            z5=0
            z6=0
            z7=0
            totSec=0
            for i in data:
                totSec = totSec + i[1]
                if i[2] <= 55:
                    z1 = z1 + i[1]
                elif i[2] <= 75:
                    z2 = z2 + i[1]
                elif i[2] <= 90:
                    z3 = z3 + i[1]     
                elif i[2] <= 105:
                    z4 = z4 + i[1]
                elif i[2] <= 120:
                    z5 = z5 + i[1]   
                elif i[2] <= 150:
                    z6 = z6 + i[1]
                else:
                    z7 = z7 + i[1]
            
            #self.zoneList = [['z1' , z1], ['z2': z2], ['z3': z3], ['z4': z4], ['z5': z5], ['z6': z6], ['z7': z7]]
            z1 = round(z1 / 60, 0)
            z2 = round(z2 / 60, 0)
            z3 = round(z3 / 60, 0)
            z4 = round(z4 / 60, 0)
            z5 = round(z5 / 60, 0)
            z6 = round(z6 / 60, 0)
            z7 = round(z7 / 60, 0)
            self.zoneList = [z1, z2, z3, z4, z5, z6, z7]
            print(self.zoneList) 
            

            # if zone <=120 and zone > 105 and duration > 300:
            # return 'warning: duration > 5 min'
            # elif zone <= 150 and zone > 120 and duration > 120:
            # return 'warning: duration > 2 min'
            # elif zone > 150  and duration > 20:
            # return 'warning: duration > 20 sec'
            # else:
            # return 'ok'
        
        
def index():
    return pc.vstack(
        
        pc.input(
            placeholder = 'email address',
            on_blur = planState.set_username
        ),
        pc.input(
            placeholder = 'password',
            type_ = 'password',
            on_blur = planState.set_password
        ),
        pc.button('log into StagesCloud',
                  on_click= planState.tokenGet
        
        ),
        
        
        

        
        
    )

def plananalysis():
    return pc.vstack(
        
        
        pc.input(
            placeholder = 'first letters of plan name',
            on_blur = planState.set_planName
        ),
        pc.button('get plan',
                on_click = planState.getPlanDetails),
        pc.text('TSS: ', planState.TSS),     
        pc.text('Variability Index: ', planState.VI),
        pc.text('Intensity factor: ', planState.IF),
        pc.table_container(
            pc.table(
                pc.table_caption('Minutes in zones', placement = 'top'),
                pc.thead(
                    
                    pc.tr(
                        pc.th('z1'),
                        pc.th('z2'),
                        pc.th('z3'),
                        pc.th('z4'),
                        pc.th('z5'),
                        pc.th('z6'),
                        pc.th('z7'),
                    ),
                ),
                pc.tbody(
                    rows = [planState.zoneList]
                )
            )
        )
        )
        
    

# Add state and page to the app.
app = pc.App(state=planState)
app.add_page(index)
app.add_page(plananalysis)
app.compile()
