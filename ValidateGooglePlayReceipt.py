
# require library: pip install google-auth google-auth-oauthlib google-api-python-client -t ./package
# filename: lambda_function.py

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

#how to get services account file:
# 1. go to google cloud console
# 2. create project and enable google play developer API
# 3. create service account and download json file
# 4. go to google play console => users and permissions => add service account

#if you got insufficient permission issue:
# 1. in google play console, change something about list IAP, like change desc of a particular product
# 2. wait for some minutes

def validateGooglePlayReceipt(packageName, productId, purchaseToken, isSubscription, serviceAccountFile):
    
    SCOPES = ['https://www.googleapis.com/auth/androidpublisher']
    credentials = service_account.Credentials.from_service_account_file(serviceAccountFile, scopes=SCOPES)
    service = build('androidpublisher', 'v3', credentials=credentials)

    try:
        if isSubscription:
            return validateGooglePlayReceipt_subscription(service, packageName, productId, purchaseToken)
        else:
            return validateGooglePlayReceipt_consumable(service, packageName, productId, purchaseToken)
    except Exception as e:
        #watch out for throttling exception

        errorMsg = e.reason
        return False
    
def validateGooglePlayReceipt_subscription(service, packageName, productId, purchaseToken):
    result = service.purchases().subscriptions().get(
        packageName=packageName,
        subscriptionId=productId,
        token=purchaseToken).execute()
            
    # 0. Payment pending 1. Payment received 2. Free trial 3. Pending deferred upgrade/downgrade
    paymentState = result['paymentState']
    if paymentState != 1:
        return False 

    # 0. Yet to be acknowledged 1. Acknowledged
    acknowledgementState = result['acknowledgementState']
    if acknowledgementState == 0:
        return True
    else:
        return False

def validateGooglePlayReceipt_consumable(service, packageName, productId, purchaseToken):
    result = service.purchases().products().get(
        packageName=packageName,
        productId=productId,
        token=purchaseToken).execute()
            
    # 0. Purchased 1. Canceled 2. Pending
    purchaseState = result['purchaseState']
    if purchaseState != 0:
        return False
    
    # after you buy a consumable product, you need to 'consume' it so that it can be purchased again
    # you must not consume a non-consumable product.
    # 
    # - after buy consumable product: need consume and acknowledge
    # - after buy non-consumable product: need acknowledge 

    # 0. Yet to be consumed 1. Consumed
    consumptionState = result['consumptionState']
    # no need to check this state

    # 0. Yet to be acknowledged 1. Acknowledged
    acknowledgementState = result['acknowledgementState']
    if acknowledgementState == 0:
        return True
    else:
        return False
    
def lambda_handler(event, context):
    params = event.get('queryStringParameters')
    productId = params.get('productId')
    purchaseToken = params.get('purchaseToken')
    isSubscription = params.get('isSubscription')
    packageName = os.environ.get('package_name')
    serviceAccountFile = "service_account.json"

    isValid = validateGooglePlayReceipt(packageName, productId, purchaseToken, isSubscription, serviceAccountFile)

    return {
        'statusCode': 200,
        'body' : isValid
    }

#--------------------------- testing -----------------------------    

token = "hpkbbhhpojcjeodeloncmpck.AO-J1OzNsy_gTRI7xEykFgi7IxFbBg7hAYyfgxfyVynf79NnBU82xS1ITjd5BmdQRBEekxSX3LHKirDkGg7cbyU70GJupADcI2DZirH0uP9Zydj-Sf5rGnk"
serviceAccountFile = 'D:/test/idyllic-anvil-463906-m6-b216df26d27e.json'
result = validateGooglePlayReceipt("com.nguyenhoainam.TestIAP", "com.nguyenhoainam.testiap.gem1", token, False, serviceAccountFile)
print(result)