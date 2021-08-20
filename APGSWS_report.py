import pandas as pd
import os
import requests
import json
from statistics import mean
from tqdm import tqdm
from time import sleep

host = "https://apgsws.in"
userSearchAPI = "api/user/v1/search"
batchParticipantsAPI = "api/course/v1/batch/participants/list"
userTokenAPI = "auth/realms/sunbird/protocol/openid-connect/token"
courseStatusAPI = "api/course/v1/content/state/read"

courseId = "do_1133310849852375041158"
batchId = "0133314135182131206"

bearerToken = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJqQXk2ME9rWlNxYVNMZmdIWkk5RGZ4WFdqV3pCTllaZiJ9.Z2Xlyfsem7pAUSQb21Pn92fRYcaKUriBSGBd_FmR6EY"


def userTokenGenerate(bearerToken):
    url = os.path.join(host, userTokenAPI)
    payload = "client_id=lms&username=admin&grant_type=client_credentials&client_secret=7a84906a-b6bc-11eb-8529-0242ac130003"
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'authorization': bearerToken
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    return json.loads(response.text).get("access_token")

def courseParticipants(bearerToken, batchId):
    url = os.path.join(host, batchParticipantsAPI)
    payload = {"request":{"batch":{"batchId":batchId}}}
    headers = {
        'authorization': bearerToken,
        'x-authenticated-user-token': userTokenGenerate(bearerToken),
        'content-type': "application/json",
        'accept': "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    return json.loads(response.text).get("result").get("batch").get("participants")

def getUserDetails(userList: list):
    url = os.path.join(host, userSearchAPI)
    headers = {
        'authorization': bearerToken,
        'x-authenticated-user-token': userTokenGenerate(bearerToken),
        'content-type': "application/json",
        'accept': "application/json"
    }
    userDetailList = []
    for i in range(int(len(userList)/250)+1):
        payload = {"request": {"query": "", "filters": {"id": userList[i*250: (i+1)*250]}}}
        response = requests.request("POST", url, json=payload, headers=headers)
        resp = json.loads(response.text).get("result").get("response").get("content")
        userDetailList+=resp
    return userDetailList


def getUserCSV(userList: list):
    finalList = []
    for user in userList:
        keys = ["HRMS_ID", "CFMS_ID", "Secretariat_Code", "Secretariat Name", "Age", "Designation", "Education", 
                "Department", "Mandal/ULB", "Revenue Division", "District", "Email_ID", "Mobile_Number", 
                "Date_of_Birth", "Joining_Date", "Gender"]
        values = user.get("lastName")[5:].split("$#$#")
        userDict = dict(zip(keys, values))
        userDict["userId"] = user.get("id")
        finalList.append(userDict)
    return pd.DataFrame(finalList)


def getCourseStatus(userId, courseId, batchId):
    url = os.path.join(host, courseStatusAPI)
    payload = {"request": {"userId": userId, "courseId": courseId, "batchId": batchId}}
    headers = {
        'authorization': bearerToken,
        'x-authenticated-user-token': userTokenGenerate(bearerToken),
        'content-type': "application/json",
        'accept': "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    contents = json.loads(response.text).get("result").get("contentList")
    try:
        mean_status = mean([content.get("status") for content in contents])
        if mean_status == 2.0:
            return "Completed"
        elif 0.0 < mean_status < 2.0:
            return "In Progress"
        else:
            return "Not Started"
    except:
        return -1


def dataframeToCsv(df, courseId=courseId, batchId=batchId):
    df.drop(['Age'], axis=1, inplace=True)
    df["GSWS_Course"] = ""
    for row in tqdm(df.iterrows(), desc="Generating course progress report.........", mininterval=1):
        try:
            status = getCourseStatus(userId=row[1]['userId'], courseId=courseId, batchId=batchId)
        except:
            sleep(300)
            try:
                status = getCourseStatus(userId=row[1]['userId'], courseId=courseId, batchId=batchId)
            except:
                sleep(900)
                try:
                    status = getCourseStatus(userId=row[1]['userId'], courseId=courseId, batchId=batchId)
                except:
                    sleep(2700)
                    try:
                        status = getCourseStatus(userId=row[1]['userId'], courseId=courseId, batchId=batchId)
                    except:
                        break
        row[1]['GSWS_Course'] = status
    df.to_csv("APGSWS_Report.csv")


userList = getUserDetails(courseParticipants(bearerToken, batchId))
dataframeToCsv(getUserCSV(userList))




