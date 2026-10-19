FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV DB_PATH=/data/tasks.db
EXPOSE 5000
CMD ["python","app.py"]
