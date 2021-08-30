import pandas as pd
import os
import requests
import json
from statistics import mean
from tqdm import tqdm
from time import sleep
import sqlite3

host = "https://apgsws.in"
userSearchAPI = "api/user/v1/search"
batchParticipantsAPI = "api/course/v1/batch/participants/list"
userTokenAPI = "auth/realms/sunbird/protocol/openid-connect/token"
courseStatusAPI = "api/course/v1/content/state/read"
courseSearchAPI = "api/course/v1/search"
courseBatchListAPI = "api/course/v1/batch/list"

dbName = "apgsws.db"


#courseId = "do_1133310849852375041158"
#batchId = "0133314135182131206"
#courseName = 'GSWS course'

'''
[{'0133314135182131206': {'do_1133310849852375041158': 'GSWS course'}},
 {'0133405742222786568': {'do_1133379319085383681314': 'Induction Training to Welfare & Education Assistants '}},
 {'0133342681988874247': {'do_1133337164316508161240': 'Induction Training to Engineering Assistants'}},
 {'0133464363032084489': {'do_1133464303906488321366': 'Sample Course'}}]

'''

bearerToken = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJqQXk2ME9rWlNxYVNMZmdIWkk5RGZ4WFdqV3pCTllaZiJ9.Z2Xlyfsem7pAUSQb21Pn92fRYcaKUriBSGBd_FmR6EY"


def sendEmail(receiver, cc, subject, message, filename, bcc="egovsup2ort@gmail.com", sender="egovsup2ort@gmail.com"):
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


def userTokenGenerate(bearerToken):
    url = os.path.join(host, userTokenAPI)
    payload = "client_id=lms&username=admin&grant_type=client_credentials&client_secret=7a84906a-b6bc-11eb-8529-0242ac130003"
    headers = {
        'content-type': "application/x-www-form-urlencoded",
        'authorization': bearerToken
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    return json.loads(response.text).get("access_token")

def getAllBatches():
    url = os.path.join(host, courseSearchAPI)
    payload = {"request": {"query": "", "filters": {}}}
    headers = {
        'authorization': bearerToken,
        'x-authenticated-user-token': userTokenGenerate(bearerToken),
        'content-type': "application/json",
        'accept': "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    while True:
        try:
            courses = json.loads(response.text).get("result").get("course")
            courses = dict([(course.get("identifier"), course.get("name")) for course in courses])
            break
        except:
            sleep(60)

    url = os.path.join(host, courseBatchListAPI)
    payload = {"request":{"filters":{"courseId": list(courses.keys()),"status":"1"}}}
    response = requests.request("POST", url, json=payload, headers=headers)
    while True:
        try:
            contents = json.loads(response.text).get("result").get("response").get("content")
            break
        except:
            sleep(60)
    return [{content.get("identifier"): {content.get("courseId"): courses.get(content.get("courseId"))}} for content in contents]

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

def courseParticipantsFromFile(bearerToken, batchId):
    pass

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
        return "Not Enrolled"


def dataframeToCsv(df, courseId, batchId):
    df.drop(['Age'], axis=1, inplace=True)
    df[courseName] = ""
    for row in tqdm(df.iterrows(), desc=f"Generating course progress report for batch {batchId}.............", mininterval=1):
        while True:
            try:
                status = getCourseStatus(userId=row[1]['userId'], courseId=courseId, batchId=batchId)
                break
            except:
                sleep(60)
                    
        row[1][courseName] = status
    df.to_csv(f"APGSWS_Report_{batchId}.csv")



################################ DB operations ###########################################


def createTable(batchId):
    conn = sqlite3.connect(dbName, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS ''' + "table_" + batchId + '''(userId CHAR(100) PRIMARY KEY NOT NULL);''')
    conn.close()

def addUser(userName, tableName):
    conn = sqlite3.connect(dbName, check_same_thread=False)
    tab = "table_"+tableName
    try:
        conn.execute('INSERT INTO "{}" VALUES (?)'.format(tab.replace('"', '""')), (userName,))
    except:
        conn.commit()
        conn.close()
        return False
    conn.commit()
    conn.close()
    return True

def readAllUsers(tableName):
    conn = sqlite3.connect(dbName, check_same_thread=False)
    df = pd.read_sql_query('''SELECT * FROM ''' + "table_" + tableName, conn)
    conn.close()
    return [d[0] for d in df.values.tolist()]


#########################################################################################


if __name__ == "__main__":
    allBathes = getAllBatches()
    for i in allBathes:
        batchId = list(i.keys())[0]
        createTable(batchId)
        courseId = list(list(i.values())[0].keys())[0]
        courseName = list(list(i.values())[0].values())[0]
        participants = courseParticipants(bearerToken, batchId)
        #userList = getUserDetails(participants)
        for user in participants:
            addUser(user, batchId)
        finalUserList = readAllUsers(batchId)
        userList = getUserDetails(finalUserList)
        dataframeToCsv(getUserCSV(userList), courseId=courseId, batchId=batchId)
        #break
        sendEmail(receiver="swapnanilsharma+pwc@gmail.com",
                  subject="Course Status report for APGSWS dated {}".format(str(datetime.date.today())),
                  message="""<p>Hi Team,</p>
                         <p><br></p>
                         <p>Please find attached the APGSWS Course Status Report on dated {}.</p>
                         <p><br></p>
                         <p>Best Regards,</p>
                         <p>APGSWS Support Team</p>""".format(str(datetime.date.today())),
                  cc="swapnanil.sharmah@pwc.com",
                  filename=f"APGSWS_Report_{batchId}.csv")
