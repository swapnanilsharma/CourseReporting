import json
import requests
import logging
import time
import os
import ast


class userManagement():

    def __init__(self, envUrl, bearerToken):
        self.envUrl = envUrl
        self.bearerToken = bearerToken
        self.createUserApi = "api/user/v1/create"
        self.addUsersToOrgApi = "api/org/v1/member/add"
        self.searchUserApi = "api/user/v1/search"
        self.editUserApi = "api/user/v1/update"
        self.assignRoleApi = "api/user/v1/role/assign"
        self.createUserTokenCredential = {
                                          "url": "auth/realms/sunbird/protocol/openid-connect/token",
                                          "client_id": "admin-cli",
                                          "username": "admin",
                                          "password": "password",
                                          "grant_type": "password"
                                         }

    def searchUser(self, searchString=None):
        url = os.path.join(self.envUrl, self.searchUserApi).replace("\\","/")
        payload = json.dumps({"request": {"query": searchString, "filters": {}, "limit": 10000}})
        headers = {
                    'authorization': self.bearerToken,
                    'content-type': 'application/json',
                    'x-authenticated-user-token': self.generateUserToken()
                  }

        response = requests.request("POST", url, data=payload, headers=headers)
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SEARCH USER <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logging.info(f"PAYLOAD: {payload}")
        logging.info(f"HEADERS: {headers}")
        logging.info(f"URL: {url}")
        logging.info(f"RESPONSE_CODE: {response.status_code}")
        logging.info(f"RESPONSE: {response.text}")
        return json.loads(response.text).get("result").get("response")
        
    def searchUserByUserName(self, userName=None):
        url = os.path.join(self.envUrl, self.searchUserApi).replace("\\","/")
        payload = json.dumps({"request": {"query": "", "filters": {"userName": userName}, "limit": 1}})
        headers = {
                    'authorization': self.bearerToken,
                    'content-type': 'application/json',
                    'x-authenticated-user-token': self.generateUserToken()
                  }

        response = requests.request("POST", url, data=payload, headers=headers)
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SEARCH USER <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logging.info(f"PAYLOAD: {payload}")
        logging.info(f"HEADERS: {headers}")
        logging.info(f"URL: {url}")
        logging.info(f"RESPONSE_CODE: {response.status_code}")
        logging.info(f"RESPONSE: {response.text}")
        return json.loads(response.text).get("result").get("response")

    def editUser(self, userId, firstName, dob):
        url = os.path.join(self.envUrl, self.editUserApi).replace("\\","/")
        headers = {
                    'authorization': self.bearerToken,
                    'content-type': 'application/json',
                    'x-authenticated-user-token': self.generateUserToken()
                  }
        payload = ""
        response = requests.request("POST", url, data=payload, headers=headers)
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> EDIT USER <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logging.info(f"PAYLOAD: {payload}")
        logging.info(f"HEADERS: {headers}")
        logging.info(f"URL: {url}")
        logging.info(f"RESPONSE_CODE: {response.status_code}")
        logging.info(f"RESPONSE: {response.text}")
        return json.loads(response.text)

    def generateUserToken(self):
        url = os.path.join(self.envUrl, self.createUserTokenCredential.get('url')).replace("\\","/")

        payload = 'client_id=' + self.createUserTokenCredential.get('client_id') + \
                  '&username=' + self.createUserTokenCredential.get('username') + \
                  '&password=' + self.createUserTokenCredential.get('password') + \
                  '&grant_type=' + self.createUserTokenCredential.get('grant_type')
        headers = {
                   'Content-Type': 'application/x-www-form-urlencoded'
                  }
        response = requests.request("POST", url, headers=headers, data = payload)
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> GENERATE JWT USER TOKEN <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logging.info(f"PAYLOAD: {payload}")
        logging.info(f"HEADERS: {headers}")
        logging.info(f"URL: {url}")
        logging.info(f"RESPONSE_CODE: {response.status_code}")
        logging.info(f"RESPONSE: {response.text}")
        return json.loads(response.text).get('access_token')

    def createSingleUser(self, firstName, lastName, email, channel, phoneNumber=None, password=None):
        url = os.path.join(self.envUrl, self.createUserApi).replace("\\","/")
        headers = {
                   'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'Authorization': self.bearerToken
                  }

        payload = dict()
        d1 = dict()
        d1['firstName'] = firstName
        d1['lastName'] = lastName
        d1['email'] = email
        if phoneNumber is None:
            d1['phone'] = str(random.randint(8700000000, 9999999999))
        else:
            d1['phone'] = str(phoneNumber)
        if password is None:
            pass
        else:
            d1['password'] = password
        d1['userName'] = "_".join(firstName.split()).lower() + "_" + "_".join(lastName.split()).lower()
        d1['emailVerified'] = True
        d1['phoneVerified'] = True
        d1['channel'] = channel

        payload['request'] = d1
        payload =  json.dumps(payload)

        response = requests.request("POST", url, headers=headers, data = payload)
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CREATE USER <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logging.info(f"PAYLOAD: {payload}")
        logging.info(f"HEADERS: {headers}")
        logging.info(f"URL: {url}")
        logging.info(f"RESPONSE_CODE: {response.status_code}")
        logging.info(f"RESPONSE: {response.text}")
        try:
            self.userId = json.loads(response.text)["result"]["userId"] #.get('result').get('userId')
        except:
            self.userId = None
            return "Failed to create new user !!"
        return f"Userid {self.userId} created successfully"

    def addUsertoOrg(self, orgId, roles):
        userToken = self.generateUserToken()
        url = os.path.join(self.envUrl, self.addUsersToOrgApi).replace("\\","/")

        payload = dict()
        d1 = dict()
        if self.userId is None:
            return "User is not created"
        d1['userId'] = self.userId
        d1['organisationId'] = orgId
        d1['roles'] = ast.literal_eval(roles)
        payload['request'] = d1
        payload =  json.dumps(payload)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': self.bearerToken,
            'X-Authenticated-User-Token': userToken
            }
        response = requests.request("POST", url, headers=headers, data = payload)
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> LINK USER TO ORG <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logging.info(f"PAYLOAD: {payload}")
        logging.info(f"HEADERS: {headers}")
        logging.info(f"URL: {url}")
        logging.info(f"RESPONSE_CODE: {response.status_code}")
        logging.info(f"RESPONSE: {response.text}")
        link_status = json.loads(response.text).get('responseCode')
        return link_status

    def assignRole(self, orgId, roles):
        userToken = self.generateUserToken()
        url = os.path.join(self.envUrl, self.assignRoleApi).replace("\\","/")

        payload = dict()
        d1 = dict()
        if self.userId is None:
            return "User is not created"
        d1['userId'] = self.userId
        d1['organisationId'] = orgId
        d1['roles'] = ast.literal_eval(roles)
        payload['request'] = d1
        payload =  json.dumps(payload)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': self.bearerToken,
            'X-Authenticated-User-Token': userToken
            }
        response = requests.request("POST", url, headers=headers, data = payload)
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> LINK USER TO ORG <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logging.info(f"PAYLOAD: {payload}")
        logging.info(f"HEADERS: {headers}")
        logging.info(f"URL: {url}")
        logging.info(f"RESPONSE_CODE: {response.status_code}")
        logging.info(f"RESPONSE: {response.text}")
        link_status = json.loads(response.text).get('responseCode')
        return link_status