import os, uuid
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

#postgreSQL DB


def setup_DBconnection():

    #get_blob_service_client_account_key
    account_url = "https://database4images.blob.core.windows.net"
    shared_access_key = os.getenv("kZ4HGDndrs+SNSIQqTIoyMxfMUljGbo/jd0p17NivIc9Z5R0h93rJb/bC2tR3aVeOFasLCAvw6jV+ASthRA4lQ==")

    blob_service_client = BlobServiceClient(account_url, credential=shared_access_key)

    print("Create DB connection...")

    return blob_service_client


def container_client(DBconnection, name):

    connection_string = "DefaultEndpointsProtocol=https;AccountName=database4images;AccountKey=kZ4HGDndrs+SNSIQqTIoyMxfMUljGbo/jd0p17NivIc9Z5R0h93rJb/bC2tR3aVeOFasLCAvw6jV+ASthRA4lQ==;EndpointSuffix=core.windows.net"
    containerClient = DBconnection.from_connection_string(conn_str=connection_string,container_name=name)

    print("Connect to \"{}\" container...".format(name))

    return containerClient


def download_img(containerClient, container_name):

    blob_client = containerClient.get_blob_client(container=container_name, blob="taiwan_power_company.jpg")

    download_stream = blob_client.download_blob()

    downloaded_file_path = "./img_data/download_img.jpg"
    with open(downloaded_file_path, "wb") as file:
        file.write(download_stream.readall())

    return


def list_blobs(blob_service_client: BlobServiceClient, container_name):

    print("List all blobs in\"{}\" container...".format(container_name))

    container_client = blob_service_client.get_container_client(container=container_name)

    blob_list = container_client.list_blobs()

    for blob in blob_list:
        print("-Name: {}".format(blob.name))


if __name__ == '__main__':

    print("[start]\n------------------\n")

    DB_connection = setup_DBconnection()
    containerClient = container_client(DB_connection, "input-data")

    list_blobs(containerClient,"input-data")

    download_img(containerClient, "input-data")


    # containerClient.create_container("test")
    
    print("\n------------------\n[processing end]")