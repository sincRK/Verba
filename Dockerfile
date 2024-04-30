FROM python:3.10
WORKDIR /Verba
COPY ./setup.py /Verba/setup.py
COPY ./requirements.txt /Verba/requirements.txt 
COPY ./README.md /Verba/README.md
RUN pip install -e '.[huggingface]'
COPY . /Verba
EXPOSE 8000
CMD ["verba", "start"]
