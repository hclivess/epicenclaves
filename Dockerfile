FROM python:3.10-alpine
EXPOSE 8888

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./enclaves.py" ]