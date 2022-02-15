FROM python:3.9.10

RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
RUN apt-get install -y nodejs
RUN useradd --create-home --shell /bin/bash jenkins
RUN mkdir /home/pip_lib & chown jenkins:jenkins /home/pip_lib
USER jenkins
WORKDIR /home/jenkins
RUN mkdir -p /home/jenkins/resources
ADD resources/requirements.txt resources/.
RUN pip install -r resources/requirements.txt
RUN mv ./.local /home/pip_lib/.
# test note