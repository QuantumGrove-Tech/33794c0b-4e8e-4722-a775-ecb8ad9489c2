# FROM public.ecr.aws/lambda/python:3.10
FROM python:3.13-slim

COPY . /
WORKDIR /

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]