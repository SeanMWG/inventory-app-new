#!/bin/bash
cd /home/site/wwwroot
export PYTHONPATH=/home/site/wwwroot
gunicorn --bind=0.0.0.0:8000 "src.app:create_app()"
