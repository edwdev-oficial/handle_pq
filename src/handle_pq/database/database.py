import streamlit as st
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

user = st.secrets['mongo_atlas']['user']
password = st.secrets['mongo_atlas']['password']

uri = f'mongodb+srv://{user}:{password}@sandbox.bfpzo.mongodb.net/'
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['hilti']

def get_database():
    return db

def get_gollection_tlm():
    col_tlm = db['tlm']
    return col_tlm

def get_collection_normal_itens():
    col_normal_itens = db['normal_itens']
    return col_normal_itens
