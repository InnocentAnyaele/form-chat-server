import time
import os
import shutil
import threading
# import json
from src.utils.config import Config
# use the one below when running on utils.py since it can't access the module as a single file
# from config import Config
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
# from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
# from langchain.vectorstores.redis import Redis
# import redis
import uuid
config = Config()

# sampleData = './src/data/Restaurant.pdf'
sampleData = '../data/Restaurant.pdf'

# redisLocalHost = 'redis://localhost:6379'
redisLocalHost = 'redis://127.0.0.1:6379'

sampleChatHistory =  [{'sender': 'user', 'message': 'What is my name'}, {'sender': 'AI', 'message': 'Your name is Innocent.'}]

#prompt template    
template = """
    You are a Restaurant business having a conversation with a client. Given extracted context from business data and conversation history, provide support to any questions the client may have. 
    
    If the client wants to place an order respond strictly with the word "order". 
    
    Previous Conversation: {chat_history}    
    Business Information: {context}
    Human: {human_input}
    Chatbot:"""
    
#prompt template
prompt = PromptTemplate(
        input_variables=["chat_history", "human_input", "context"],
        template=template
    )
embeddings = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)


#creating chunks
def createChunkFromPdf(path):
    loader = UnstructuredPDFLoader(path)
    data = loader.load()
    # print (f'You have {len(data)} document(s) in your data')
    # print (f'You have {len(data[0].page_content)} characters in your document')
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
    # text_splitter = CharacterTextSplitter(chunk_size=50, chunk_overlap=0)
    texts = text_splitter.split_documents(data)
    # print (f'Now you have {len(texts)} documents')
    # print (texts)
    return texts

def createChunkFromTxt(path):
    with open(path) as f:
        data = f.read()
    text_splitter = CharacterTextSplitter(chunk_size=50, chunk_overlap=0)
    texts = text_splitter.split_text(data)
    # print (texts)
    return texts


#create memory from chathistory
def createMemoryChatHistory(chatHistory):
    memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")
    # for chat in chatHistory:
    #     chat_message = chat['message']
    #     chat_sender = chat['sender']
    #     if chat_sender != 'system':     
    #         # if chat['sender'] == 'AI':
    #         #     memory.chat_memory.add_ai_message(chat_message)
    #         # else:
    #         #     memory.chat_memory.add_user_message(chat_message)
    #         if chat['sender'] == 'human':
    #             memory.chat_memory.add_user_message(chat_message)
    #         else:
    #             memory.chat_memory.add_ai_message(chat_message)
    for chat in chatHistory:
        chat_sender = chat['sender']
        chat_message = chat['data']
        if chat_sender == 'system':
            memory.chat_memory.add_user_message(chat_message)
        elif chat_sender == 'human':
            memory.chat_memory.add_user_message(chat_message)

                
                
    return memory

#load qa chain
def use_load_qa_chain(memory, prompt, query, docs):
    # chain = load_qa_chain(OpenAI(temperature=0, openai_api_key=config.OPENAI_API_KEY, model_name="gpt-3.5-turbo-16k"), chain_type="stuff", memory=memory, prompt=prompt)
    chain = load_qa_chain(ChatOpenAI(temperature=0, openai_api_key=config.OPENAI_API_KEY, model_name="gpt-3.5-turbo-16k"), chain_type="stuff", memory=memory, prompt=prompt)
    chain_output = chain({"input_documents":docs, "human_input": query })
    # print ('conversation history', chain.memory.buffer)
    # print (chain_output['output_text'])
    return chain_output['output_text']



# REDDIS

def createIndexFromRedis(path):
    texts = createChunkFromPdf(path)
    index_name = str(uuid.uuid1())
    rds = Redis.from_documents(texts, embeddings, redis_url = redisLocalHost, index_name=index_name)
    # rds.index_name
    # print (index_name)
    return index_name

def queryRedisIndex(indexName, query, chatHistory):
    try:
        rds = Redis.from_existing_index(embeddings, redis_url=redisLocalHost, index_name=indexName)
        results = rds.similarity_search(query)
        memory = createMemoryChatHistory(chatHistory)
        return use_load_qa_chain(memory, prompt, query, results)
    except Exception as e:
        # print (e)
        # print ('Index name does not exist')
        return (e)
    
    # retriever = rds.as_retriever()
    # docs = retriever.get_relevant_documents(query)
    # retriever = rds.as_retriever(search_type="similarity_limit")
    # retriever.get_relevant_documents("where did ankush go to college?")
    

# CHROMA 

def createIndexWithChroma(path):
    texts = createChunkFromPdf(path)
    new_index = str(uuid.uuid1())
    persistent_directory = 'src/persistent/' + new_index
    vectordb = Chroma.from_documents(documents=texts, embedding=embeddings, persist_directory=persistent_directory)
    vectordb.persist()
    vectordb = None
    # print (new_index)
    return new_index

def queryIndexWithChromaFromPersistent(indexKey, query, chatHistory):
    try:
        persistent_path = 'src/persistent/' + indexKey
        # persistent_path = '../persistent/' + indexKey
        if (os.path.exists(persistent_path)):    
            vectordb = Chroma(persist_directory=persistent_path, embedding_function=embeddings)
            docs = vectordb.similarity_search(query)
            memory = createMemoryChatHistory(chatHistory)
            return use_load_qa_chain(memory, prompt, query, docs)
        else:
            # print ('path does not exist')
            return 'path does not exist'
    except Exception as e:
        print ('queryIndexWithChromaFromPersistent exception', e)
        raise

def queryIndexWithChroma(path, query, chatHistory):
    texts = createChunkFromPdf(path)
    embeddings = OpenAIEmbeddings()
    docsearch = Chroma.from_documents(texts, embeddings)
    docs = docsearch.similarity_search(query)
    memory = createMemoryChatHistory(chatHistory)
    return use_load_qa_chain(memory, prompt, query, docs)


def delete_context(dirName):
    time.sleep(300)
    if os.path.exists(dirName):
        shutil.rmtree(dirName)
    else:
        return ('Path does not exist')
        
    return 'completed'

def startDeleteThread(dirName):
    t = threading.Thread(target=delete_context, args=(dirName,))
    t.start()    

def checkExtension(fileName):
    fileName_split = fileName.split('.') 
    fileExtension = fileName_split[-1]
    return fileExtension

def deleteAllData():
    path = '.src/data/'
    if os.path.exists(path):
        shutil.rmtree(path)


if __name__ == '__main__':
    print(queryIndexWithChromaFromPersistent(config.HARDCODED_INDEX_KEY,'What is this business about?',[]))
    # createIndexWithChroma(sampleData)
    # pass