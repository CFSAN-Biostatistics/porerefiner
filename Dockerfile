FROM centos/systemd:latest

LABEL maintainer="justin.payne@fda.hhs.gov"

RUN yum -y update \
 && yum -y install python3 \
 && yum clean all

# RUN useradd -ms /bin/bash porerefiner
# USER porerefiner

WORKDIR src

ADD . .
ADD porerefiner/porerefiner.service /usr/lib/systemd/user/
ADD porerefiner/porerefiner.app.service /usr/lib/systemd/user/
# RUN ls /usr/lib/systemd/user/
RUN systemctl --user enable porerefiner.service
RUN systemctl --user enable porerefiner.app.service

RUN python3 setup.py install --user


FROM jrei/systemd-debian:latest

LABEL maintainer="justin.payne@fda.hhs.gov"

RUN apt-get -y update \
 && apt-get -y install python3 python3-setuptools python3-pip \
 && apt-get clean all

WORKDIR src

ADD . .
ADD porerefiner/porerefiner.service /usr/lib/systemd/user/
ADD porerefiner/porerefiner.app.service /usr/lib/systemd/user/
# RUN ls /usr/lib/systemd/user/
RUN systemctl --user enable porerefiner.service
RUN systemctl --user enable porerefiner.app.service

RUN python3 setup.py install --user
