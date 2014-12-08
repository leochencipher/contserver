FROM centos:latest
MAINTAINER Shuo Chen <leo.chen.cipher@outlook.com>

RUN useradd -m geohe

RUN yum -y update 
RUN yum install -y python-flask python-gevent python-matplotlib
ADD get-pip.py /root/get-pip.py
RUN python /root/get-pip.py
RUN yum install -y scipy --disableplugin=fastestmirror

RUN pip install geojson

ADD contourserv /home/geohe/contourserv
RUN chown -R geohe:geohe /home/geohe

WORKDIR /home/geohe/contourserv

EXPOSE 5000
ENTRYPOINT ["/bin/su", "geohe", "-c","python /home/geohe/contourserv/gateway.py"]

