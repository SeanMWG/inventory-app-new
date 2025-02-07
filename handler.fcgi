#!%HOME%\Python311\python.exe
from wfastcgi import WSGIHandler
from app import app

WSGIHandler(app).run()
