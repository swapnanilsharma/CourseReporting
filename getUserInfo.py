from UserManagement import userManagement
import sys
envUrl="https://myjbr.flexresourcemanagement.com"
bearerToken="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3NWM2MjU2OGI0NDQ0MTRmODdmZTljM2M3MWE0NTdlMSJ9.0bKHF_wWZiMoqhkcB6TZsmpZGNLhCg3xr-N9OPDTi9I"


def getUserInfo(userName, envUrl=envUrl, bearerToken=bearerToken):
    user = userManagement(envUrl, bearerToken)
    userToken = user.generateUserToken()
    results = user.searchUserByUserName(userName=userName).get("content")
    try:
        temp = results[0]['firstName']
        print("=================================================================================================")
        print("\n")
        print(f"Hi {results[0]['firstName']},")
        print("\n")
        print("Please go to https://myjbr.flexresourcemanagement.com  (use google chrome) -> Sign In -> Forgot.")
        print("After that enter below email id and name and click on email id option to generate a password.")
        print("\n")
        print("Email:  " + results[0]["userName"])
        print("Name:  " + results[0]["firstName"])
        print("\n")
        print("You can follow this demo video to proceed with the courses: https://myjbr.flexresourcemanagement.com/resources/play/content/do_113117650142248960151")
        print("\n")
        print("================================================================================================")
    except:
        print("=================================================================================================")
        print("\n")
        print(f"Hi Shivam,")
        print("\n")
        print(f"The user email id {userName} is not present in MyJBR database. Please confirm.")
        print("\n")
        print("=================================================================================================")

if __name__=="__main__":
    userName = sys.argv[1]
    getUserInfo(userName=userName, envUrl=envUrl, bearerToken=bearerToken)
