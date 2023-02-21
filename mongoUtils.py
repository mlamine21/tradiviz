#!/usr/bin/env python
# coding: utf-8
import pymongo
from bson.objectid import ObjectId
from datetime import datetime

def connectDB(host="127.0.0.1", port="27018", username="amine", password = "password"):
    cient = None
    print("server_started")
    try:
        #Connection to the server
        client = pymongo.MongoClient(host=host,
        port=port,
        username=username,
        password=password,
        serverSelectionTimeoutMS=1000,
        connect=False)

        
    except pymongo.errors.ServerSelectionTimeoutError as err:
        # do whatever you need
        print(err)
        
    return client

def alreadyExists(client, database, session_id, annotator_id, role_id, scheme_id):
    #Selection of the database
    db = client[database]
    annotations = db["Annotations"]
    check_existing = annotations.find({
    "session_id":session_id,
    "annotator_id":annotator_id, 
    "role_id" : role_id,
    "scheme_id":scheme_id})
    
    exists = False if(len(list(check_existing))==0) else True

    return exists

def getCollectionNamesIds(collection, display=False):
    names = []
    ids = []
    if(display) : print(collection)
    for c in collection.find():
        if(display):
            print(c["name"])
            print(c["_id"])
        names.append(c["name"])
        ids.append(c["_id"])

    return names,ids

def getEntryId(entry, display=False):
    id = entry["_id"]
    if(display) : print(id)
    return id


def createAnnotationEntry(session_id, role_id, scheme_id, annotator_id, data_id,streams):
    # {
#   "data_id": {"_id": {"$oid":"63b8434d927c90811ed86515"},
#   "annotator_id": {"_id": "637f47ad5ff2df55edbea5aa"},
#   "role_id": {"_id": "637f48625ff2df55edbea811"},
#   "scheme_id": {"_id": "63a191adef98f36792860328"},
#   "session_id": {"_id": "63b559a2ef98f3679287a1ee"},
#   "isFinished": false,
#   "isLocked": false,
#   "date": {},
#   "streams": [
#     "Client.video.mp4"
#   ]
# }
    entry =  {
    "data_id": ObjectId(data_id),
    "annotator_id": ObjectId(annotator_id),
    "role_id": ObjectId(role_id),
    "scheme_id": ObjectId(scheme_id),
    "session_id": ObjectId(session_id),
    "isFinished":False,
    "isLocked": False,
    "date": datetime.utcnow(),
    "streams": streams
    }
    return entry


def createAnnotationDataEntry(annotation_data, entry=[]):

#   "labels": [
#     {
#       "from": 196.04,
#       "to": 198.96,
#       "id": 0,
#       "conf": 1,
#       "meta": ""
#     }, {...},{...}

#   ]
    data_list = []
    for element in annotation_data:
        line = element.strip()
        start_time = line[:line.index(';')]
        line = line[line.index(';')+1:]
        end_time = line[:line.index(';')]
        line = line[line.index(';')+1:]
        label = line[:line.index(';')]
        line = line[line.index(';')+1:]
        confidence = line[0] if ';' not in line else line[:line.index(';')]
        element_entry = {
        "from": round(float(start_time),2),
        "to": round(float(end_time),2),
        "id" : int(label),
        "conf" : int(confidence),
        "meta" : ""
        }
        data_list.append(element_entry)    
    entry = {
    "labels": data_list
    }
    return entry


def importAnnotationFileToDatabase(client, path_annotation, annotation_file, database, session, annotator, role_name, scheme, streams, display_debug=False):
    if(display_debug): print(session, annotation_file)
    #Selection of the database
    db = client[database]
    # database_names = client.list_database_names()

    # print("Databases :")
    # print(client.list_database_names())
    #Get "AnnotationData" collection
    annotation_data = db["AnnotationData"] 

    #Get "Sessions" collection
    sessions = db["Sessions"]
    sessions_names,sessions_ids = getCollectionNamesIds(sessions)
    #Get ObjectID of the selected session for the annotation to add
    session_id = sessions_ids[sessions_names.index(session)]
    #Get "Roles" collection
    roles = db["Roles"]
    roles_names,roles_ids = getCollectionNamesIds(roles)
    #Get ObjectID of the selected role for the annotation to add
    role_id = roles_ids[roles_names.index(role_name)]
    #Get "Schemes" collection
    schemes = db["Schemes"]
    schemes_names,schemes_ids = getCollectionNamesIds(schemes)
    if(scheme in schemes_names):
        #Get ObjectID of the selected scheme for the annotation to add
        scheme_id = schemes_ids[schemes_names.index(scheme)]
    else:
        if(display_debug) : print("   Scheme : "+scheme+" does not exists, aborting")
        return 0
    #Get "Annotators" collection
    annotators = db["Annotators"]
    annotators_names,annotators_ids = getCollectionNamesIds(annotators)
    #Get ObjectID of selected annotator for the annotation to add
    annotator_id = annotators_ids[annotators_names.index(annotator)]
    
    
    if(alreadyExists(client, database, session_id, annotator_id, role_id, scheme_id)):
        if(display_debug): print("   Annotation entry already exists.")
        return 0
    else:
        if(display_debug): print("   Creating annotation entry")
        # sys.exit(0)
        #Open annotation file to get annotation blocks 
        with open(path_annotation+annotation_file,'r') as data_annotation:
            labels = []   
            #Create AnnotationData entry from annotation blocks 
            data_entry  = createAnnotationDataEntry(data_annotation.readlines())
            #Insert the created entry to the database 
            annotation_data.insert_one(data_entry)
        #Get the ObjectId (automatically created by mongo) of the inserted AnnotationData entry (most recent entry in the database) 
        last_entry = (annotation_data.find().limit(1).sort([('$natural',-1)]))[0]
        data_id = getEntryId(last_entry)      
        
        #Create Annotation entry 
        annotation_entry = createAnnotationEntry(session_id, role_id,scheme_id, annotator_id, data_id,streams)
        if(display_debug) : print("Added")
        annotations = db["Annotations"]
        #Insert Annotation entry to the database 
        annotations.insert_one(annotation_entry)

        return 1
