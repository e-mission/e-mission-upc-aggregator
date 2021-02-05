# python 3
FROM continuumio/miniconda3:4.6.14

MAINTAINER K. Shankari (shankari@eecs.berkeley.edu)
# set working directory
WORKDIR /usr/src/app

# Add the contents
ADD . .

# setup python environment.
RUN setup/setup.sh

# install nodejs, npm and bower
RUN apt-get update
RUN apt-get install -y build-essential
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get -y install nodejs
RUN npm install -g bower
WORKDIR /usr/src/app/webapp
RUN bower update --allow-root
WORKDIR /usr/src/app

# install nano and vim for editing
RUN apt-get -y install nano vim

# cleanup
RUN apt-get -y remove --purge build-essential
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#declare environment variables. These environment variables are used as a method to get around docker network issues.
ENV DB_HOST=''
ENV WEB_SERVER_HOST=''

#add start script.
# this is a redundant workdir setting, but it doesn't harm anything and might
# be useful if the other one is removed for some reason
WORKDIR /usr/src/app
ADD start_script.sh /usr/src/app/start_script.sh
RUN chmod u+x /usr/src/app/start_script.sh

CMD ["/bin/bash", "/usr/src/app/start_script.sh"]
