FROM python:3.10.5-slim-buster

# Create a working directory.
RUN mkdir wd
WORKDIR wd

# Install Python dependencies.
COPY ../requirements.txt .

RUN mkdir packages
ADD ./packages ./packages
# RUN pip install -r requirements.txt
# RUN pip install -r requirements.txt --no-index --find-links ./packages
RUN pip install -r requirements.txt

# Copy the rest of the codebase into the image
COPY .. ./

EXPOSE 8020

# Finally, run gunicorn.
# gunicorn --workers=5 --threads=1 -b 0.0.0.0:8000 app:server
CMD [ "gunicorn", "--workers=5", "--threads=1", "-b 0.0.0.0:8020", "app:task_manager"]

