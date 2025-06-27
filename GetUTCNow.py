
from datetime import datetime, timezone

def getUtcNow():
    now = datetime.now(timezone.utc)
    return now.strftime("%m/%d/%Y %H:%M:%S")

def lambda_handler(event, context):
    now = getUtcNow()
    return {
        'statusCode': 200,
        'body' : now
    }

#--------------------------- testing ----------------------------- 

print(getUtcNow())

