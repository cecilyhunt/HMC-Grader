import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLES=True
SECRET_KEY="Grutors <3 SPAM"

MONGODB_SETTINGS = {'DB': 'submissionsite'}

DATABASE_QUERY_TIMEOUT = 0.5

GROODY_HOME="/home/plenk/GroodyGrader"

MARKABLE_FILES = ['.py','.rkt', '.java', '.txt', '.pl']