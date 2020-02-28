FROM python:3.7-buster

WORKDIR /root

ADD requirements.txt /root/
RUN pip install -r requirements.txt

ADD app.py /root/

ENV FLASK_APP app.py
CMD ["flask", "run", "--host=0.0.0.0"]

