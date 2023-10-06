import os, json
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient


def setup_client():

    endpoint = os.getenv("FormRecognizer_Endpoint")
    credential = AzureKeyCredential(os.getenv("AImodel_Credential"))
    
    document_analysis_client = DocumentAnalysisClient(endpoint, credential)

    print("Create form_recognizer_service client... ")

    return document_analysis_client



def recognizer_process(document_analysis_client, process_fileName):

    print("Recognizer processing... ")


    form_data_localUrl = "./OCR_main_code/current_file/{}".format(process_fileName)

    with open(form_data_localUrl, "rb") as f:
        poller = document_analysis_client.begin_analyze_document("TaiwanPowerCompanyForm_model_v2", document=f, locale="zh-tw")

    form_result = poller.result()


    result_json = {}

    try:
        for idx, document in enumerate(form_result.documents):
            for title, field in document.fields.items():

                field_value = field.value if field.value else field.content

                if field.value_type == "string":
                    result_json[title] = field_value
                    
                elif field.value_type == "list":
                    result_json[title] = {}

                    for item in field_value:
                        item = item.to_dict()

                        try:
                            sub_title = item["value"]['欄位名稱']['content']
                        except:
                            sub_title = ""

                        try:
                            sub_content = item["value"]['內容or數值']['content']
                        except:
                            sub_content = ""

                        result_json[title][sub_title] = sub_content
    except:
        return "false"


    result_json = json.dumps(result_json, ensure_ascii=False)
    return result_json




# if __name__ == '__main__':

#     print("[start]\n------------------\n")

#     document_analysis_client = setup_client()

#     recognizer_process(document_analysis_client)

#     print("\n------------------\n[processing end]")

    
