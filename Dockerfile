# Alpine Docker build
# SEQUOIA_BRANCH=giulio/time_t (v1.1.0)
# YML2_BRANCH=v2.7.5
# BOTAN_BRANCH=3.0.0
# LIBETPAN_BRANCH=v3.3.1
# ASN1C_BRANCH=v0.9.28
# LIBPLANCKTRANSPORT_BRANCH=v1.0.0
# LIBPLANCKCXX_BRANCH=v3.2.0
# PLANCKCORE_BRANCH=v3.2.1
# LIBPLANCKWRAPPER_BRANCH=david/alpine_compat (v3.2.0)
# PYTHONWRAPPER_BRANCH=v3.2.1

### building SequoiaBackend
FROM rust:alpine3.18 as sequoiaBuilder
# ENV SEQUOIA_BRANCH=v1.1.0
ENV SEQUOIA_BRANCH=giulio/time_t
RUN apk update && apk add git pkgconf openssl-dev make bzip2-dev sqlite-dev musl-dev
WORKDIR /root/
RUN git clone --depth=1 --branch=$SEQUOIA_BRANCH https://git.planck.security/foundation/planckCoreSequoiaBackend.git
WORKDIR /root/planckCoreSequoiaBackend
COPY ./docker/planckCoreSequoiaBackend.conf local.conf
COPY ./docker/planckCoreSequoiaBackendMakefile Makefile
RUN make install

### building yml2
FROM python:3.9-alpine as yml2Builder
ENV YML2_BRANCH=v2.7.5
WORKDIR /root/
RUN apk update && apk add git build-base
RUN git clone --depth=1 --branch=$YML2_BRANCH https://git.planck.security/foundation/yml2.git
WORKDIR /root/yml2
RUN make dist

FROM alpine:3.18.3 as alpine-gcc
RUN apk update && apk add gcc git make autoconf automake libtool build-base

### building botan
FROM alpine-gcc as botanBuilder
ENV BOTAN_BRANCH=3.0.0
RUN apk update && apk add python3
WORKDIR /root/
RUN git clone --depth=1 --branch=$BOTAN_BRANCH https://github.com/randombit/botan.git
WORKDIR /root/botan
RUN ./configure.py --prefix=/opt/planck
RUN make install

### building libetpan
FROM alpine-gcc as libetpanBuilder
ENV LIBETPAN_BRANCH=v3.3.1
WORKDIR /root/
RUN git clone --depth=1 --branch=$LIBETPAN_BRANCH https://git.planck.security/foundation/libetpan.git
WORKDIR /root/libetpan
RUN ./autogen.sh --prefix=/opt/planck
RUN make install

### building ASN1C
FROM alpine-gcc as asn1cBuilder
ENV ASN1C_BRANCH=v0.9.28
WORKDIR /root/
RUN git clone --depth=1 --branch=$ASN1C_BRANCH https://github.com/vlm/asn1c.git
WORKDIR /root/asn1c
RUN autoreconf -iv
RUN ./configure --prefix=/opt/planck
RUN make install

### building libPlanckTransport
FROM alpine-gcc as libPlanckTransportBuilder
ENV LIBPLANCKTRANSPORT_BRANCH=v1.0.0
RUN apk update && apk add python3 py3-pip
WORKDIR /root/
COPY --from=yml2Builder /root/yml2/dist/yml2-2.7.4.tar.gz /root/
RUN python3 -m venv /opt/tools/virtualenv
RUN . /opt/tools/virtualenv/bin/activate && pip install /root/yml2-2.7.4.tar.gz
RUN git clone --depth=1 --branch=$LIBPLANCKTRANSPORT_BRANCH https://git.planck.security/foundation/libPlanckTransport.git
WORKDIR /root/libPlanckTransport
COPY ./docker/libPlanckTransport.conf local.conf
RUN . /opt/tools/virtualenv/bin/activate && export PATH="$PATH:/opt/tools/virtualenv/bin" && \
    export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && make && make install

### building libPlanckCxx
FROM alpine-gcc as libPlanckCxxBuilder
# ENV LIBPLANCKCXX_BRANCH=v3.2.0
ENV LIBPLANCKCXX_BRANCH=david/alpine_compat
WORKDIR /root/
RUN git clone --depth=1 --branch=$LIBPLANCKCXX_BRANCH https://git.planck.security/foundation/libPlanckCxx11.git
WORKDIR /root/libPlanckCxx11
RUN echo 'PREFIX=/opt/planck' > local.conf
RUN make install

### build python wrapper
FROM python:3.9-alpine as pyWrapperBuilder
ENV PLANCKCORE_BRANCH=v3.2.1
ENV LIBPLANCKWRAPPER_BRANCH=v3.2.0
ENV PYTHONWRAPPER_BRANCH=v3.2.1

RUN apk update && apk add git build-base util-linux-dev sqlite-dev boost-dev boost-python3
WORKDIR /root/
COPY --from=sequoiaBuilder /opt/planck /opt/planck
COPY --from=yml2Builder /root/yml2/dist/yml2-2.7.4.tar.gz /root/
RUN python3 -m venv /opt/tools/virtualenv
RUN . /opt/tools/virtualenv/bin/activate && pip install /root/yml2-2.7.4.tar.gz
RUN pip install -t /opt/tools/yml2/ /root/yml2-2.7.4.tar.gz
COPY --from=libetpanBuilder /opt/planck /opt/planck
COPY --from=asn1cBuilder /opt/planck /opt/planck
COPY --from=libPlanckTransportBuilder /opt/planck /opt/planck
COPY --from=libPlanckCxxBuilder /opt/planck /opt/planck

WORKDIR /root/planckCore/
RUN git clone --depth=1 --branch=$PLANCKCORE_BRANCH https://git.planck.security/foundation/planckCoreV3.git .
COPY ./docker/planckCore.conf local.conf
ENV LD_LIBRARY_PATH=/opt/planck/lib
ENV DYLD_LIBRARY_PATH=/opt/planck/lib
RUN . /opt/tools/virtualenv/bin/activate && export PATH="$PATH:/opt/tools/virtualenv/bin" && \
    export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && make && make install

WORKDIR /root/libPlanckWrapper/
RUN git clone --depth=1 --branch=$LIBPLANCKWRAPPER_BRANCH https://git.planck.security/foundation/libPlanckWrapper.git .
RUN echo 'PREFIX=/opt/planck' > local.conf
RUN make install

WORKDIR /root/planckPythonWrapper/
RUN git clone --depth=1 --branch=$PYTHONWRAPPER_BRANCH https://git.planck.security/foundation/planckPythonWrapper.git .
RUN echo 'PREFIX=/opt/planck' > local.conf
RUN ln -s /usr/lib/libboost_python311.so /usr/lib/libboost_python3.so
RUN make dist-whl

### build runner
FROM python:3.9-alpine as runner
RUN apk update && apk add python3 py3-pip postfix boost-dev boost-python3
WORKDIR /root/
COPY --from=sequoiaBuilder /opt/planck /opt/planck
COPY --from=libetpanBuilder /opt/planck /opt/planck
COPY --from=botanBuilder /opt/planck /opt/planck
COPY --from=asn1cBuilder /opt/planck /opt/planck
COPY --from=libPlanckTransportBuilder /opt/planck /opt/planck
COPY --from=libPlanckCxxBuilder /opt/planck /opt/planck
COPY --from=pyWrapperBuilder /opt/planck /opt/planck
COPY --from=pyWrapperBuilder /root/planckPythonWrapper/dist /opt/planck/dist
ENV LD_LIBRARY_PATH=/opt/planck/lib
ENV DYLD_LIBRARY_PATH=/opt/planck/lib
RUN ln -s /usr/lib/libboost_python311.so /usr/lib/libboost_python3.so
RUN pip install /opt/planck/dist/pEp-3.2.1-cp39-cp39-linux_x86_64.whl

# Copy the proxy files
COPY ./src/* /opt/planck-proxy/

# Copy the postfix configuration files
COPY ./docker/postfix/* /etc/postfix/
RUN postmap /etc/postfix/transport
RUN postmap /etc/postfix/transport-proxy

# Add the "proxy" user without a password
RUN adduser --disabled-password proxy

# Create the workdir and set permissions
RUN mkdir /home/proxy/work
WORKDIR /home/proxy/work
RUN chown proxy:proxy . -R

# Copy the settings file
COPY ./docker/docker-settings.json /home/proxy/settings.json
