#!D:\Python311\python.exe
from wfastcgi import WSGIHandler
from src.app import create_app

app = create_app()
WSGIHandler(app).run()
