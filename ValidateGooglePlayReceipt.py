
# require library: pip install google-auth google-auth-oauthlib google-api-python-client -t ./package
# filename: lambda_function.py

from google.oauth2 import service_account
from googleapiclient.discovery import build

def validateGooglePlayReceipt(packageName, productId, purchaseToken, isSubscription):
    SCOPES = ['https://www.googleapis.com/auth/androidpublisher']

    #how to get services account file:
    # 1. go to google cloud console
    # 2. create project and enable google play developer API
    # 3. create service account and download json file
    # 4. go to google play console => users and permissions => add service account

    #if you got insufficient permission issue:
    # 1. in google play console, change something about list IAP, like change desc of a particular product
    # 2. wait for some minutes

    #if local test: path on drive
    #if run on lambda: ???????
    SERVICE_ACCOUNT_FILE = 'D:/test/idyllic-anvil-463906-m6-b216df26d27e.json'

    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('androidpublisher', 'v3', credentials=credentials)

    try:
        if isSubscription:
            return validateGooglePlayReceipt_subscription(service)
        else:
            return validateGooglePlayReceipt_consumable(service)
    except Exception as e:
        #watch out for throttling exception

        print(f"An error occurred: {e}")
        
        print("------begin-------")
        print(e.reason)
        print("------begin-------")
        return "ERROR!!!!!!!!!!!!"
    
def validateGooglePlayReceipt_subscription(service):
    result = service.purchases().subscriptions().get(
        packageName=packageName,
        subscriptionId=productId,
        token=purchaseToken).execute()
            
    # 0. Payment pending 1. Payment received 2. Free trial 3. Pending deferred upgrade/downgrade
    paymentState = result['paymentState']

    # 0. Yet to be acknowledged 1. Acknowledged
    acknowledgementState = result['acknowledgementState']

def validateGooglePlayReceipt_consumable(service):
    result = service.purchases().products().get(
        packageName=packageName,
        productId=productId,
        token=purchaseToken).execute()
            
    # 0. Purchased 1. Canceled 2. Pending
    purchaseState = result['purchaseState']

    # 0. Yet to be consumed 1. Consumed
    consumptionState = result['consumptionState']

    # 0. Yet to be acknowledged 1. Acknowledged
    acknowledgementState = result['acknowledgementState']
    
def lambda_handler(event, context):

#--------------------------- testing -----------------------------    

token = "hpkbbhhpojcjeodeloncmpck.AO-J1OzNsy_gTRI7xEykFgi7IxFbBg7hAYyfgxfyVynf79NnBU82xS1ITjd5BmdQRBEekxSX3LHKirDkGg7cbyU70GJupADcI2DZirH0uP9Zydj-Sf5rGnk"
result=validateGooglePlayReceipt("com.nguyenhoainam.TestIAP", "com.nguyenhoainam.testiap.gem1", token, False)
print(result)