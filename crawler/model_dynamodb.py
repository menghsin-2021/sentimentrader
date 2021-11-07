import boto3

def main():
    # create client
    ddb = boto3.resource('dynamodb',
                         endpoint_url='http://localhost:8000',
                         region_name='sentimentrader',
                         aws_access_key_id='XXXX',
                         aws_secret_access_key='XXXX'
                         )

    # create the table
    # ddb.create_table(TableName='Sentimentrader',
    #                  AttributeDefinitions=[
    #                      {
    #                          'AttributeName': 'SentimentraderId',
    #                          'AttributeType': 'S'
    #                      }
    #                  ],
    #                  KeySchema=[
    #                      {
    #                          'AttributeName': 'SentimentraderId',
    #                          'KeyType': 'HASH',
    #                      }
    #                  ],
    #                  ProvisionedThroughput={
    #                      'ReadCapacityUnits': 10,
    #                      'WriteCapacityUnits': 10
    #                  }
    #                  )
    # print('Successfully created Table')

    table = ddb.Table('Sentimentrader')

    input = {'SentimentraderId': "kkk", "State": "PENDING", "Amount": 50}

    # # insert data
    # table.put_item(Item=input)
    # print('successfully put item')

    # scan table
    scan_response = table.scan(TableName='Sentimentrader')
    items = scan_response['Items']
    for item in items:
        print(item)




main()

