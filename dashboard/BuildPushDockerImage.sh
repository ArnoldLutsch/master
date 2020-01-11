# !/bin/bash
# set project
gcloud config set project <YOUR-PROJECT>
# build the docker image
docker build --no-cache -t gcr.io/<YOUR-PROJECT>/dashboard-app:latest .
# push the image to the google container registry
docker push gcr.io/<YOUR-PROJECT>/dashboard-app:latest