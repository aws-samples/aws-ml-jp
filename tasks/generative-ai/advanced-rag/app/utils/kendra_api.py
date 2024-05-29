import boto3

def search_kendra(query, settings):
    # Amazon Kendraを使用して検索を実行する
    kendra = boto3.client("kendra", region_name=settings["aws_region"])
    response = kendra.query(
        QueryText=query,
        IndexId=settings["kendra_index_id"],
        AttributeFilter={
            "EqualsTo": {
                "Key": "_language_code",
                "Value": {"StringValue": "ja"},
            },
        },
    )
    
    search_results = response["ResultItems"]
    return search_results
