import schedule
import time
import datetime
import pandas as pd
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import os
import requests
import json
from UserManagement import userManagement
from statistics import mean, StatisticsError
from tqdm import tqdm
import streamlit as st
from stqdm import stqdm
import base64
import sys
from time import sleep

if not os.path.exists("SchedularFiles"):
    os.mkdir("SchedularFiles")


# MYJBR DETAILS
envUrl="https://myjbr.flexresourcemanagement.com"
bearerToken="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3NWM2MjU2OGI0NDQ0MTRmODdmZTljM2M3MWE0NTdlMSJ9.0bKHF_wWZiMoqhkcB6TZsmpZGNLhCg3xr-N9OPDTi9I"


def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="download.csv">Download data as csv</a>'
    return href

def getBatchDetail(envUrl, bearerToken, userToken):
    url = os.path.join(envUrl, "api/course/v1/batch/list")
    payload = {"request":{"filters":{"status": 1}}}
    headers = {
                "content-type": "application/json",
                "authorization": bearerToken,
                "x-authenticated-user-token": userToken,
                "accept": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    return [{"batchId":i.get("identifier"), "courseId": i.get("courseId"), "batchName": i.get("name")} for i in json.loads(response.text).get("result").get("response").get("content")]

def getBatchEnrolledUsers(envUrl, bearerToken, userToken, batchId):
    url = os.path.join(envUrl, "api/course/v1/batch/participants/list")
    headers = {
        'authorization': bearerToken,
        'content-type': "application/json",
        'accept': "application/json",
        'x-authenticated-user-token': userToken
    }
    payload = {"request":{"batch":{"batchId":batchId}}}
    response = requests.request("POST", url, json=payload, headers=headers)
    users = json.loads(response.text).get("result").get("batch").get("participants")
    return users
    
    

def getCourseStatus(envUrl, bearerToken, userToken, userId, courseId, batchId):
    url = os.path.join(envUrl, "content/course/v1/content/state/read")
    payload = {
        "request": {
            "userId": userId,
            "batchId": batchId,
            "courseId": courseId
        }
    }
    headers = {
        'authorization': bearerToken,
        'content-type': "application/json",
        'accept': "application/json",
        'x-authenticated-user-token': userToken
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


def sendEmail(receiver, cc, subject, message, filename,
              bcc="egovsup2ort@gmail.com", sender="egovsup2ort@gmail.com"):
    data = MIMEMultipart()
    data['From'] = sender
    data['To'] = receiver
    data['Cc'] = cc
    data['Bcc'] = bcc
    data['Subject'] = subject
    data.attach(MIMEText(message, 'html'))
    try:
        attachment = open("{}".format(filename), "rb")
        p = MIMEBase('application', 'octet-stream')
        p.set_payload((attachment).read())
        encoders.encode_base64(p)
        p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        data.attach(p)
    except FileNotFoundError:
        pass
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(sender, "pwc@1234")
    text = data.as_string()
    s.sendmail(receiver, sender, text)
    s.quit()


if __name__ == "__main__":
    #with open(sys.argv[1]) as f:
    df_shivam = pd.read_excel(sys.argv[1]   , engine="openpyxl")

    userList = [i for i in df_shivam["user_id"].to_list() if not isinstance(i, int)]
    lenUserList = len(userList)
    user = userManagement(envUrl, bearerToken)
    userToken = user.generateUserToken()
    print(user.searchUser())
    results = user.searchUser().get("content")
        
    batches = getBatchDetail(envUrl, bearerToken, userToken)
    b0_enroll = getBatchEnrolledUsers(envUrl, bearerToken, userToken, batchId=batches[0].get("batchId"))
    b1_enroll = getBatchEnrolledUsers(envUrl, bearerToken, userToken, batchId=batches[1].get("batchId"))
        
    out_table = []
    for num, userId in enumerate(stqdm(userList, desc="Generating course progress report.........", mininterval=1)):
        sleep(0)
        if num%150==0:
            userToken = user.generateUserToken()
        try:
            c1_status = getCourseStatus(envUrl, bearerToken, userToken, userId,
                                        courseId=batches[0].get("courseId"),
                                        batchId=batches[0].get("batchId"))
        
            c2_status = getCourseStatus(envUrl, bearerToken, userToken, userId,
                                        courseId=batches[1].get("courseId"),
                                        batchId=batches[1].get("batchId"))
        except:
            try:
                print("Second Try: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                sleep(10)
                c1_status = getCourseStatus(envUrl, bearerToken, userToken, userId,
                                            courseId=batches[0].get("courseId"),
                                            batchId=batches[0].get("batchId"))
        
                c2_status = getCourseStatus(envUrl, bearerToken, userToken, userId,
                                            courseId=batches[1].get("courseId"),
                                            batchId=batches[1].get("batchId"))
            except:
                print("Second Try Failed! Putting empty entry: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                c1_status, c2_status = "", ""
        
        if c1_status == -1:
            if userId in b0_enroll:
                c1_status = "Course Assigned but not started"
            else:
            	c1_status = "Course Not Assigned"
        
        if c2_status == -1:
            if userId in b1_enroll:
            	c2_status = "Course Assigned but not started"
            else:
            	c2_status = "Course Not Assigned"
        
        
        out_table.append({"user_id": userId,
                          batches[0].get("batchName"): c1_status,
                          batches[1].get("batchName"): c2_status
                          })

        df_swap = pd.DataFrame(out_table)
        df = pd.merge(df_shivam, df_swap, on='user_id', how='outer')
        df.to_csv("MYJBR_COURSE_STATUS.csv", index=False)

    sendEmail(receiver="swapnanilsharma+pwc@gmail.com",
                  subject="Course Status report for MYJBR dated {}".format(str(datetime.date.today())),
                  message="""<p>Hi Team,</p>
                             <p><br></p>
                             <p>Please find attached the MYJBR Course Status Report on dated {}.</p>
                             <p><br></p>
                             <p>Best Regards,</p>
                             <p>eGov Support Team</p>""".format(str(datetime.date.today())),
                  cc="swapnanil.sharmah@pwc.com",
                  filename="MYJBR_COURSE_STATUS.csv")

