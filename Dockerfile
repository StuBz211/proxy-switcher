FROM python:3.6


ENV HOST 0.0.0.0
ENV PORT 4000

COPY . /
WORKDIR /

# install requirements
RUN pip install -r requirements.txt

# expose the app port
EXPOSE 5000

CMD python proxy_switcher.py
# run the app server
# CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "3", "app:app"]
