import os, csv, io
from datetime import datetime, timezone, timedelta

from flask import Flask, Response
from flask import redirect, render_template, send_from_directory, url_for, request
from flask_socketio import SocketIO

from werkzeug.utils import secure_filename
import PyPDF2



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'


socketio = SocketIO(app)


# index page----------------------------------------------------------

@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')



@app.route('/OCR_dashboard', methods=['GET', 'POST'])
def OCR_dashboard():
    if request.method == 'POST':
        user_name = request.form.get('name')

        if user_name:
            print('Request for OCR_dashboard page received with name=%s' % user_name)
            return render_template('OCR_dashboard.html', user_name=user_name)
        else:
            print('Request for OCR_dashboard page received with no name or blank name -- redirecting')
            return redirect(url_for('index'))

    elif request.method == 'GET':
        return render_template('OCR_dashboard.html')



# upload file---------------------------------------------------

def allowed_file(filename):
    allowed_extensions = set(['pdf','jpg', 'jpeg', 'png'])   #'png', 'jpg', 'jpeg'
    return '.' in filename and filename.rsplit('.', 1)[1] in allowed_extensions


@app.route('/upload_file', methods=['GET','POST'])
def upload_file():
    if request.method == 'POST':

        file = request.files['upload_file']
        Recognition_opt = request.form.get('Recognition_opt')

        if file and allowed_file(file.filename):

            # print(os.getcwd())
            process_fileName = file.filename.split('.')
            process_fileName = "process_file.{}".format(process_fileName[1])

            file.save(os.path.join("./static/current_file/", secure_filename(process_fileName)))        #for web check
            file.seek(0)    #reset file point
            

            if Recognition_opt == "single":

                progress_message = {'total_pages': 1,'current_page': 1}
                socketio.emit('update_progress', progress_message)

                file.save(os.path.join("./OCR_main_code/current_file/", secure_filename(process_fileName)))     #for main code process

                formInfo_data = OCR_service_process(process_fileName)

                if formInfo_data == "false":
                    return render_template('OCR_dashboard.html', flag_error = "true")
                
                formInfo_data = json.loads(formInfo_data)

                formInfoData_lengths = {
                    "total_length": len(formInfo_data),
                    "sub_lengths": [len(v) for k, v in formInfo_data.items() if isinstance(v, dict)]
                }


                return render_template('OCR_dashboard.html',
                                       formInfo_data = formInfo_data,
                                       formInfoData_lengths = formInfoData_lengths,
                                       process_fileName = process_fileName,
                                       Recognition_opt="single",
                                       flag_error = "false")
            

            elif Recognition_opt == "batch":

                check_type = file.filename.split('.')[1]
                if check_type != 'pdf':
                    return render_template('OCR_dashboard.html', flag_error = "true")
                

                file.save(os.path.join("./OCR_main_code/current_file/batch_files", secure_filename(process_fileName)))     #for main code process

                #檔案分割
                total_pages = 0
                with open('./OCR_main_code/current_file/batch_files/{}'.format(process_fileName), 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    total_pages = len(reader.pages)

                    if total_pages > 12:  #最大上傳限制              
                        return render_template('OCR_dashboard.html', flag_error="true")

                    for page_num in range(total_pages):
                        writer = PyPDF2.PdfWriter()
                        writer.add_page(reader.pages[page_num])
                        with open('./OCR_main_code/current_file/batch_files/page_{}.pdf'.format(page_num), 'wb') as output_file:
                            writer.write(output_file)

                #檔案逐一辨識
                formInfo_data_ary = []
                formInfoData_lengths_ary = []
                for page_num in range(total_pages):

                    #向前端傳送進度
                    progress_message = {'total_pages': total_pages,'current_page': page_num+1}
                    socketio.emit('update_progress', progress_message)

                    formInfo_data = OCR_service_process("batch_files/page_{}.pdf".format(page_num))
                    if formInfo_data == "false":
                        return render_template('OCR_dashboard.html', flag_error = "true")
                    
                    formInfo_data = json.loads(formInfo_data)
                    formInfo_data_ary.append(formInfo_data)

                    formInfoData_lengths = {
                        "total_length": len(formInfo_data),
                        "sub_lengths": [len(v) for k, v in formInfo_data.items() if isinstance(v, dict)]
                    }
                    formInfoData_lengths_ary.append(formInfoData_lengths)


                return render_template('OCR_dashboard.html', 
                                       formInfo_data_ary = formInfo_data_ary, 
                                       formInfoData_lengths_ary = formInfoData_lengths_ary, 
                                       process_fileName = process_fileName, 
                                       Recognition_opt="batch", 
                                       flag_error = "false")
        
        else:
            return render_template('OCR_dashboard.html', flag_error = "true")



# OCR service process (form recognizer)---------------------------------
from OCR_main_code.form_recognizer import *

def OCR_service_process(process_fileName):

    print("[start]\n------------------\n")

    # print(os.getcwd())

    document_analysis_client = setup_client()
    result_json = recognizer_process(document_analysis_client, process_fileName)

    print("[print result]")
    print(result_json)


    print("\n------------------\n[processing end]")

    return result_json


# downloading data in a CSV file && form data to DB-------------------------------------------------------
@app.route('/api', methods=['POST'])
def api():
    if request.method == 'POST':

        form_data = request.form.items()

        return generate_csv(form_data)


def generate_csv(form_data):

    # 當天日期和時間
    tz = timezone(timedelta(hours=+8))  #UTC+8
    now = datetime.now(tz)
    date_time = now.strftime("%Y%m%d_%H%M")

    # 創建CSV資料
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    all_title = []
    all_value = []
    row_title = []
    row_value = []

    next_page = 2
    for key, value in form_data:

        curr_page = int(key[0])     #正常初始值為1

        if curr_page == next_page:
            next_page = curr_page+1
            all_title.append(row_title)
            all_value.append(row_value)
            row_title = []
            row_value = []

        if key.find("title") != -1:
            row_title.append(value)
        if key.find("value") != -1:
            row_value.append(value)

    #補上最後一次
    all_title.append(row_title)
    all_value.append(row_value)

    # writer.writerow(all_title[0])   #tmp
    for i in range(len(all_title)):
        writer.writerow(all_title[i])   # 表頭
        writer.writerow(all_value[i])   # 資料


    csv_output = output.getvalue().encode('utf-8-sig')
    output.close()

    filename = f"{date_time}_result.csv"

    response = Response(csv_output, mimetype="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"

    return response




if __name__ == '__main__':
    #app.run(debug=True)
    socketio.run(app, debug=True)
