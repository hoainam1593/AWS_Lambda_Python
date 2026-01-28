# require library: pip install google-auth google-auth-oauthlib google-api-python-client firebase-admin google-cloud-firestore -t ./package

# on ubuntu, must specify python version in lambda: 
# python3.14 -m pip install google-auth google-auth-oauthlib google-api-python-client firebase-admin google-cloud-firestore -t ./package

# filename: lambda_function.py

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

#how to get services account file:
# 1. go to google cloud console
# 2. create project and enable google play developer API
# 3. create service account and download json file
# 4. go to google play console => users and permissions => add service account

#if you got insufficient permission issue:
# 1. in google play console, change something about list IAP, like change desc of a particular product
# 2. wait for some minutes

def logDebug(isDebug, msg):
    if isDebug:
        print(msg)

def logToDatabase(serviceAccountFile, verifyResult, verifyMsg, isDebug, orderNumber, productId, price, currency, userId):
    try:
        cred = credentials.Certificate(serviceAccountFile)
        app = firebase_admin.initialize_app(cred)

        store = firestore.client()
        doc_ref = store.collection('iap_history')

        now = datetime.now(timezone.utc)

        props = {
            'timestamp': now,
            'platform': 'googleplay',
            'verify_result': verifyResult,
            'verify_msg': verifyMsg,
            'order_number': orderNumber,
            'product_id': productId,
            'price': price,
            'currency': currency,
            'user_id': userId,
        }
        doc_ref.add(props)
    except Exception as e:
        errorMsg = str(e)
        logDebug(isDebug, "Exception when logging to database: " + errorMsg)

def validateGooglePlayReceipt(packageName, productId, purchaseToken, isSubscription, serviceAccountGooglePlay, serviceAccountFirebase, isDebug, orderNumber, price, currency, userId):
    verifyResult = {}
    try:
        SCOPES = ['https://www.googleapis.com/auth/androidpublisher']
        credentials = service_account.Credentials.from_service_account_file(serviceAccountGooglePlay, scopes=SCOPES)
        service = build('androidpublisher', 'v3', credentials=credentials)

        if isSubscription:
            verifyResult = validateGooglePlayReceipt_subscription(service, packageName, productId, purchaseToken, isDebug)
        else:
            verifyResult = validateGooglePlayReceipt_consumable(service, packageName, productId, purchaseToken, isDebug)
    except Exception as e:
        errorMsg = str(e)
        logDebug(isDebug, "Exception when validating google play receipt: " + errorMsg)
        verifyResult = {
            'success': False,
            'message': errorMsg
        }

    logToDatabase(serviceAccountFirebase, verifyResult['success'], verifyResult['message'], isDebug, orderNumber, productId, price, currency, userId)
    
    return verifyResult['success']
    
def validateGooglePlayReceipt_subscription(service, packageName, productId, purchaseToken, isDebug):
    result = service.purchases().subscriptions().get(
        packageName=packageName,
        subscriptionId=productId,
        token=purchaseToken).execute()
    
    logDebug(isDebug, f"Response from Google Play: {result}")
            
    # 0. Payment pending 1. Payment received 2. Free trial 3. Pending deferred upgrade/downgrade
    paymentStateDict = {
        0: "this item is pending payment",
        2: "this item is in free trial",
        3: "this item is pending deferred upgrade/downgrade"
    }
    paymentState = result['paymentState']
    if paymentState != 1:
        return {
            'success': False,
            'message': paymentStateDict.get(paymentState, "unknown payment state")
        }

    # 0. Yet to be acknowledged 1. Acknowledged
    acknowledgementState = result['acknowledgementState']
    if acknowledgementState == 0:
        return {
            'success': True,
            'message': "this item is valid"
        }
    else:
        return {
            'success': False,
            'message': "this item was already acknowledged"
        }

def validateGooglePlayReceipt_consumable(service, packageName, productId, purchaseToken, isDebug):
    result = service.purchases().products().get(
        packageName=packageName,
        productId=productId,
        token=purchaseToken).execute()
    
    logDebug(isDebug, f"Response from Google Play: {result}")
            
    # 0. Purchased 1. Canceled 2. Pending
    purchaseStateDict = {
        1: "this item was canceled",
        2: "this item is pending"
    }
    purchaseState = result['purchaseState']
    if purchaseState != 0:
        return {
            'success': False,
            'message': purchaseStateDict.get(purchaseState, "unknown purchase state")
        }
    
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
        return {
            'success': True,
            'message': "this item is valid"
        }
    else:
        return {
            'success': False,
            'message': "this item was already acknowledged"
        }
    
def lambda_handler(event, context):

    # if invoked by HTTP request, parameters are in event['queryStringParameters']
    # if invoked in lambda test, parameters are in event
    if 'queryStringParameters' in event and event['queryStringParameters'] is not None:
        params = event['queryStringParameters']
    else:
        params = event

    productId = params.get('productId')
    purchaseToken = params.get('purchaseToken')
    isSubscription = params.get('isSubscription')
    orderNumber = params.get('orderNumber')
    price = params.get('price')
    currency = params.get('currency')
    userId = params.get('userId')
    packageName = os.environ.get('package_name')
    serviceAccountGooglePlay = "service_account_google_play.json"
    serviceAccountFirebase = "service_account_firebase.json"

    isValid = validateGooglePlayReceipt(packageName, productId, purchaseToken, isSubscription, serviceAccountGooglePlay, serviceAccountFirebase, False, orderNumber, price, currency, userId)

    return {
        'statusCode': 200,
        'body' : isValid
    }

#--------------------------- testing -----------------------------    

token = "kgdmilkldhihkkeklkfechhe.AO-J1OwMDEHnIp5y-Mv9xgWyr6DN65wxO5SUWUKwcCgiBJIp134oYy8evjHzLZ3xzeyW4P78TXX1pnz_fCij4vd98ds_RS38Ug"
serviceAccountGooglePlay = 'D:/merge-cat-town-49d98-0d0703482d92.json'
serviceAccountFirebase = 'D:/merge-cat-town-49d98-firebase-adminsdk-fbsvc-88de428f72.json'
orderNumber = "order_0001"
price = 0
currency = "USD"
userId = 'user_0001'
result = validateGooglePlayReceipt("com.mobirix.mgct", "shop_gem_0002", token, False, serviceAccountGooglePlay, serviceAccountFirebase, True, orderNumber, price, currency, userId)
print(result)