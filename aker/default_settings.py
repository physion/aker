# Configuration
COUCH_HOST = 'http://localhost:5995'
COUCH_USER = 'couch-user'
COUCH_PASSWORD = 'password'
UNDERWORLD_DATABASE = 'underworld_dev'
DB_UPDATES_SQS_QUEUE = 'underworld_dev_db_updates'
REGION = 'us-east-1'  # Get the region we're running in
SECRET_KEY = b'\xd7c\x08La\xcd\xbf\x16*\x82\x99\x8b\x92M\xfc\x1b\xaa\x07\x0e\x85M5e\xf6' # You must override this in production! `os.urandom(24)`
JSON_AS_ASCII = False
RAYGUN_API_KEY = 'api-key'
