# from pymongo import MongoClient
# from django.conf import settings
# from typing import List, Dict, Optional
# import logging
# from bson import ObjectId

# logger = logging.getLogger(__name__)

# class TalentHubMongoService:
#     """Service class for connecting to TalentHub MongoDB database"""
    
#     def __init__(self):
#         self.client = None
#         self.db = None
#         self.connect()
    
#     def connect(self):
#         """Establish connection to MongoDB"""
#         try:
#             connection_string = settings.MONGO_URI
#             database_name = settings.DATABASE_NAME
            
#             self.client = MongoClient(connection_string)
#             self.db = self.client[database_name]
            
#             # Test connection
#             self.client.admin.command('ping')
#             logger.info(f"Connected to TalentHub MongoDB: {database_name}")
            
#         except Exception as e:
#             logger.error(f"Failed to connect to MongoDB: {str(e)}")
#             raise ConnectionError(f"MongoDB connection failed: {str(e)}")
    
#     def test_connection(self) -> bool:
#         """Test if MongoDB connection is working"""
#         try:
#             if self.client:
#                 self.client.admin.command('ping')
#                 return True
#             return False
#         except Exception as e:
#             logger.error(f"MongoDB connection test failed: {str(e)}")
#             return False
    
#     def get_collections(self) -> List[str]:
#         """Get list of all collections in the database"""
#         try:
#             if self.db:
#                 return self.db.list_collection_names()
#             return []
#         except Exception as e:
#             logger.error(f"Error getting collections: {str(e)}")
#             return []
    
#     def get_all_interns(self) -> List[Dict]:
#         """
#         Retrieve all interns from the database
#         Adjust the collection name and query based on TalentHub's actual structure
#         """
#         try:
#             # Common collection names for users: 'users', 'interns', 'accounts'
#             # Adjust based on actual TalentHub structure
#             collection_names = ['users', 'interns', 'accounts', 'profiles']
            
#             for collection_name in collection_names:
#                 if collection_name in self.db.list_collection_names():
#                     # Try to find interns by role or type
#                     interns = list(self.db[collection_name].find({
#                         "$or": [
#                             {"role": "intern"},
#                             {"userType": "intern"},
#                             {"type": "intern"}
#                         ]
#                     }))
                    
#                     if interns:
#                         # Convert ObjectId to string for JSON serialization
#                         for intern in interns:
#                             intern['_id'] = str(intern['_id'])
#                         return interns
            
#             # If no specific role filter works, try to get all users
#             users = list(self.db.users.find().limit(10))  # Limit for safety
#             for user in users:
#                 user['_id'] = str(user['_id'])
#             return users
            
#         except Exception as e:
#             logger.error(f"Error fetching interns: {str(e)}")
#             return []
    
#     def get_intern_by_id(self, intern_id: str) -> Optional[Dict]:
#         """Get a specific intern by ID"""
#         try:
#             collection_names = ['users', 'interns', 'accounts', 'profiles']
            
#             for collection_name in collection_names:
#                 if collection_name in self.db.list_collection_names():
#                     intern = self.db[collection_name].find_one({
#                         "_id": ObjectId(intern_id)
#                     })
                    
#                     if intern:
#                         intern['_id'] = str(intern['_id'])
#                         return intern
            
#             return None
            
#         except Exception as e:
#             logger.error(f"Error fetching intern {intern_id}: {str(e)}")
#             return None
    
#     def get_logbook_entries(self, intern_id: str, limit: int = 100) -> List[Dict]:
#         """
#         Get logbook entries for a specific intern
#         Adjust collection name based on TalentHub's actual structure
#         """
#         try:
#             # Common collection names for logbooks
#             collection_names = ['logbooks', 'logbook_entries', 'entries', 'logs', 'daily_logs']
            
#             for collection_name in collection_names:
#                 if collection_name in self.db.list_collection_names():
#                     # Try different field names for intern reference
#                     queries = [
#                         {"internId": ObjectId(intern_id)},
#                         {"userId": ObjectId(intern_id)},
#                         {"user_id": ObjectId(intern_id)},
#                         {"intern_id": ObjectId(intern_id)},
#                         {"createdBy": ObjectId(intern_id)}
#                     ]
                    
#                     for query in queries:
#                         entries = list(self.db[collection_name].find(query).limit(limit))
#                         if entries:
#                             # Convert ObjectId to string
#                             for entry in entries:
#                                 entry['_id'] = str(entry['_id'])
#                                 # Convert other ObjectIds if present
#                                 for key, value in entry.items():
#                                     if isinstance(value, ObjectId):
#                                         entry[key] = str(value)
#                             return entries
            
#             return []
            
#         except Exception as e:
#             logger.error(f"Error fetching logbook entries: {str(e)}")
#             return []
    
#     def get_all_logbook_entries(self, limit: int = 500) -> List[Dict]:
#         """Get all logbook entries for general analysis"""
#         try:
#             collection_names = ['logbooks', 'logbook_entries', 'entries', 'logs', 'daily_logs']
            
#             for collection_name in collection_names:
#                 if collection_name in self.db.list_collection_names():
#                     entries = list(self.db[collection_name].find().limit(limit))
#                     if entries:
#                         # Convert ObjectIds to strings
#                         for entry in entries:
#                             entry['_id'] = str(entry['_id'])
#                             for key, value in entry.items():
#                                 if isinstance(value, ObjectId):
#                                     entry[key] = str(value)
#                         return entries
            
#             return []
            
#         except Exception as e:
#             logger.error(f"Error fetching all logbook entries: {str(e)}")
#             return []
    
#     def close_connection(self):
#         """Close MongoDB connection"""
#         try:
#             if self.client:
#                 self.client.close()
#                 logger.info("MongoDB connection closed")
#         except Exception as e:
#             logger.error(f"Error closing MongoDB connection: {str(e)}")

# # Global service instance
# mongo_service = TalentHubMongoService()