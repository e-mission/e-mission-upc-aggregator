# python 3
#FROM continuumio/anaconda3
FROM emission-server-base
MAINTAINER Alvin Ghouas

ENV DB_HOST=''
ENV WEB_SERVER_HOST=''
# set working directory
#WORKDIR /usr/src/app

# clone from repo
#RUN git clone https://github.com/alvinalexander/e-mission-server.git .
#COPY . /usr/src/app
# setup python environment. TODO: set this to the correct environment. Using alvin_env for testing purposes
#RUN conda env update --name emission --file setup/environment36.yml
#RUN /bin/bash -c "source activate emission; pip install six --upgrade"

#RUN apt-get -y install nano
# start the server
#RUN export $DB_URL
#RUN export $WEB_SERVER_HOST

ADD docker/start_script.sh /usr/src/app/start_script.sh
RUN chmod u+x /usr/src/app/start_script.sh

EXPOSE 8080

CMD ["/bin/bash", "/usr/src/app/start_script.sh"]