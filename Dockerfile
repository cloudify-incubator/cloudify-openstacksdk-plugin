FROM amd64/centos:latest
MAINTAINER Trammell (hello@cloudify.co)
WORKDIR /build
RUN echo "manylinux1_compatible = False" > "/usr/lib64/python2.7/_manylinux.py"
RUN yum -y install python-devel gcc openssl git libxslt-devel libxml2-devel openldap-devel libffi-devel openssl-devel libvirt-devel
RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
RUN python get-pip.py
RUN pip install --upgrade pip==9.0.1
RUN pip install wagon==0.3.2
ENTRYPOINT ["wagon"]
CMD ["create", "-s", ".", "-v", "-f"]
