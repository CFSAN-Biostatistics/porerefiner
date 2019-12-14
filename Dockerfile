FROM centos/systemd:latest

LABEL maintainer="justin.payne@fda.hhs.gov"

RUN yum -y update \
 && yum -y install python3 \
 && yum clean all

WORKDIR src

ADD . .

RUN python3 setup.py install
