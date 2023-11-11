from flask import Flask, request, make_response
# from config import DevelopmentConfig
from src.utils.config import DevelopmentConfig
from functools import wraps
import os
import uuid
from werkzeug.utils import secure_filename
from src.utils.utils import checkExtension, startDeleteThread, queryIndexWithChromaFromPersistent
from flask_cors import CORS
import json


def create_app(config = DevelopmentConfig()):
    
    app = Flask(__name__)
    CORS(app)
    # CORS(app, origins="*")
    app.config.from_object(config)
        
    def token_required(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            token = request.headers['Authorization']
            if not token:
                response = make_response('Authorization is required')
                response.status_code = 500
                return response
            
            if app.config['BEARER_TOKEN'] != token:
                response = make_response('Invalid Token')
                response.status_code = 500
                return response
            
            return func(*args, **kwargs)
        
        return decorated_function

    @app.route('/')
    def index():
        # print ('hello world')
        return "Hello, World"


    # @app.route('/api/addData', methods=['POST'])
    # @token_required
    # def add_data():
    #     if request.method == 'POST':
    #         # response = make_response('testIndexKey')
    #         # response.status_code = 200 
    #         # return response
            
    #         try:
    #             uniqueDirectoryName = str(uuid.uuid1())
    #             uniqueDirName = os.path.join('./src//data/', uniqueDirectoryName)
    #             os.makedirs(uniqueDirName)
    #             fileNamesArray = []
    #             for i in range(int(request.form['fileLength'])):
    #                 currFile = request.files['file'+str(i)]
    #                 currFileName = secure_filename(currFile.filename)
    #                 save_file_to_dir = os.path.join(uniqueDirName,currFileName)
    #                 fileNamesArray.append(currFileName)
    #                 currFile.save(save_file_to_dir)
                    
    #             startDeleteThread(uniqueDirName)
                
    #             extension = checkExtension(fileNamesArray[-1]) 
                
    #             if extension == 'pdf':
    #                 path_to_pdf = os.path.join(uniqueDirName,fileNamesArray[-1])
    #                 indexKey = createIndex(path_to_pdf)
    #                 response = make_response(indexKey)
    #                 response.status_code = 200
    #                 # print (indexKey)
    #                 return response
    #             else:
    #                 response = make_response(extension , 'is not accepted')
    #                 response.status_code = 400
    #                 # print (extension, 'is not accepted')
    #                 return (response)
    #         except Exception as e:
    #             # print (e)
    #             response = make_response('Something went wrong')
    #             response.status_code = 500
    #             return response
            
    # @app.route('/api/queryIndex', methods=['POST'])
    # def queryIndex():
    #     return 'Reached here'        
            
    @app.route('/api/queryIndex', methods=['POST'])
    @token_required 
    def queryIndex():
        if request.method == 'POST':
            try:
                # print('request', request)
                data = request.get_json()
                print ('request data', data)
                chatHistory = data['chatHistory']
                query = data['prompt']
                indexKey = config.HARDCODED_INDEX_KEY
                print ('chatHistory', chatHistory)
                print ('prompt', query)
                # chatHistory = json.loads(request.form['chatHistory'])
                
                # print ('this is the index key',indexKey)
                # print ('this is the chat history',chatHistory)
                # print (chatHistory[0])
                # print (chatHistory[0]['sender'])
                # print (chatHistory[0]['message'])
                
                output = queryIndexWithChromaFromPersistent(indexKey,query,chatHistory)
                
                response = make_response(output)
                response.status_code = 200
                # print (output)
                return response
                
            except Exception as e:
                print ('error', e)
                response = make_response('Something went wrong')
                response.status_code = 500
                return response
   
    return app
