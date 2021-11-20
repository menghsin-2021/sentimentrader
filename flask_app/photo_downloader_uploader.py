import os
import boto3
import requests


def download_image(url):
    # リクエストを投げる
    response = requests.get(url, timeout=100)
    # ステータスコードがエラー
    if response.status_code != 200:
        raise RuntimeError("取得失敗")
    content_type = response.headers["content-type"]
    # 画像ではない
    if 'image' not in content_type:
        raise RuntimeError("画像ではありません")
    return response.content


def save_file(id, image):
    main_img_mkdir_path = os.path.join('img', id)
    image_name = f'{id}.jpg'
    os.makedirs(main_img_mkdir_path, exist_ok=True)
    main_img_save_path = os.path.join(main_img_mkdir_path, image_name)
    with open(main_img_save_path, "wb") as file:
        file.write(image)

    return image_name

# Upload a new file
def upload_file(uid, file, file_name , bucket_name, object_path=None):

    """Upload a file to an S3 bucket
        :param file: File to upload (body)
        :param bucket: Bucket to upload to
        :param object_path: S3 object name.
    """
    # create client
    s3_client = boto3.client('s3')
    # set main photo or other photos
    object = object_path + '/' + str(uid) + '/' + file_name

    # Upload the files
    try:
        s3_client.put_object(Body=file, Bucket=bucket_name, Key=object, ContentType='image/png')
        print('upload success')
    except:
        print('fail')
        return False

    else:
        return file_name

def delete_file(bucket_name, object_path, uid, file_name):
    try:
        client = boto3.client('s3')
        object = object_path + '/' + str(uid) + '/' + file_name
        client.delete_object(Bucket=bucket_name, Key=object)
        print('delete success')
        return True
    except:
        print('delete fail')
        return False



#
#
# url = "https://pics.meierq.com/meierq/ProductCovers/18e024ed-2055-434b-952f-21e16b3b5923_w310_h389.jpg"
# bucket_name = 'appworksbucket'
# object_path = 'stylish_cowork/products'
# id = '123456'
# category = 'women'
#
# image = download_image(url)
# # local_file_name = save_file(id, image)
# # print(local_file_name)
# upload_file_name = upload_file(id, category, image, bucket_name, object_path)
# print(upload_file_name)




