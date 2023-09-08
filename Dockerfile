FROM alpine:3.18.3 as alpine-gcc
RUN apk update && apk add gcc git make autoconf automake libtool build-base

### building SequoiaBackend
FROM rust:alpine3.18 as sequoiaBuilder
# ENV SEQUOIA_BRANCH=v1.1.0
ENV SEQUOIA_BRANCH=giulio/time_t
RUN apk update && apk add git pkgconf openssl-dev make bzip2-dev sqlite-dev musl-dev botan-libs
WORKDIR /root/planckCoreSequoiaBackend
RUN git clone --depth=1 --branch=$SEQUOIA_BRANCH https://git.planck.security/foundation/planckCoreSequoiaBackend.git .
COPY ./docker/planckCoreSequoiaBackend.conf local.conf
COPY ./docker/planckCoreSequoiaBackendMakefile Makefile
RUN make install

### building yml2
FROM python:3.9-alpine as yml2Builder
ENV YML2_BRANCH=v2.7.6
RUN apk update && apk add git build-base
WORKDIR /root/yml2
RUN git clone --depth=1 --branch=$YML2_BRANCH https://git.planck.security/foundation/yml2.git .
RUN make dist

### building libetpan
FROM alpine-gcc as libetpanBuilder
ENV LIBETPAN_BRANCH=v3.3.1
WORKDIR /root/libetpan
RUN git clone --depth=1 --branch=$LIBETPAN_BRANCH https://git.planck.security/foundation/libetpan.git .
RUN ./autogen.sh --prefix=/opt/planck
RUN make install

### building ASN1C
FROM alpine-gcc as asn1cBuilder
ENV ASN1C_BRANCH=v0.9.28
WORKDIR /root/asn1c
RUN git clone --depth=1 --branch=$ASN1C_BRANCH https://github.com/vlm/asn1c.git .
RUN autoreconf -iv
RUN ./configure --prefix=/opt/planck
RUN make install

### building libPlanckTransport
FROM alpine-gcc as libPlanckTransportBuilder
ENV LIBPLANCKTRANSPORT_BRANCH=v3.3.0-RC9
RUN apk update && apk add python3 py3-pip
COPY --from=yml2Builder /root/yml2/dist/yml2-2.7.4.tar.gz /root/
RUN python3 -m venv /opt/tools/virtualenv
RUN . /opt/tools/virtualenv/bin/activate && pip install /root/yml2-2.7.4.tar.gz
WORKDIR /root/libPlanckTransport
RUN git clone --depth=1 --branch=$LIBPLANCKTRANSPORT_BRANCH https://git.planck.security/foundation/libPlanckTransport.git .
COPY ./docker/libPlanckTransport.conf local.conf
RUN . /opt/tools/virtualenv/bin/activate && export PATH="$PATH:/opt/tools/virtualenv/bin" && \
    export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && make && make install

### building libPlanckCxx
FROM alpine-gcc as libPlanckCxxBuilder
# ENV LIBPLANCKCXX_BRANCH=v3.2.0
ENV LIBPLANCKCXX_BRANCH=david/alpine_compat_v3.3.0-RC8
WORKDIR /root/libPlanckCxx11
RUN git clone --depth=1 --branch=$LIBPLANCKCXX_BRANCH https://git.planck.security/foundation/libPlanckCxx11.git .
RUN echo 'PREFIX=/opt/planck' > local.conf
RUN make install

### build core
FROM python:3.9-alpine as planckCoreBuilder
ENV PLANCKCORE_BRANCH=v3.3.2
RUN apk update && apk add git build-base util-linux-dev sqlite-dev boost-dev boost-python3 botan-libs botan-dev
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

### build libplanck adapter
FROM alpine-gcc as libWrapperBuilder
ENV LIBPLANCKWRAPPER_BRANCH=v3.3.0-RC9
RUN apk update && apk add python3 py3-pip e2fsprogs-dev
WORKDIR /root/libPlanckWrapper/
COPY --from=planckCoreBuilder /opt/planck /opt/planck
RUN git clone --depth=1 --branch=$LIBPLANCKWRAPPER_BRANCH https://git.planck.security/foundation/libPlanckWrapper.git .
RUN echo 'PREFIX=/opt/planck' > local.conf
RUN make install

### build pywrapper
FROM python:3.9-alpine as pyWrapperBuilder
ENV PYTHONWRAPPER_BRANCH=v3.3.0-RC8
RUN apk update && apk add git boost-dev make gcc build-base e2fsprogs-dev
COPY --from=sequoiaBuilder /opt/planck /opt/planck
COPY --from=libetpanBuilder /opt/planck /opt/planck
COPY --from=asn1cBuilder /opt/planck /opt/planck
COPY --from=libPlanckTransportBuilder /opt/planck /opt/planck
COPY --from=libPlanckCxxBuilder /opt/planck /opt/planck
COPY --from=planckCoreBuilder /opt/planck /opt/planck
COPY --from=libWrapperBuilder /opt/planck /opt/planck
ENV LD_LIBRARY_PATH=/opt/planck/lib
ENV DYLD_LIBRARY_PATH=/opt/planck/lib
WORKDIR /root/planckPythonWrapper/
RUN git clone --depth=1 --branch=$PYTHONWRAPPER_BRANCH https://git.planck.security/foundation/planckPythonWrapper.git .
RUN echo 'PREFIX=/opt/planck' > local.conf
RUN ln -s /usr/lib/libboost_python311.so /usr/lib/libboost_python3.so
RUN make dist-whl

### build proxy
FROM python:3.9-alpine as proxyBuilder
RUN apk update && apk add python3 py3-pip
WORKDIR /root/proxy/
COPY . /root/proxy/
RUN pip install build
RUN python -m build

### build runner
FROM python:3.9-alpine as runner
RUN apk update && apk add python3 py3-pip postfix boost-dev boost-python3 botan-libs botan-dev sqlite
WORKDIR /root/
RUN ln -s /usr/lib/libboost_python311.so /usr/lib/libboost_python3.so
ENV LD_LIBRARY_PATH=/opt/planck/lib
ENV DYLD_LIBRARY_PATH=/opt/planck/lib
COPY --from=sequoiaBuilder /opt/planck /opt/planck
COPY --from=libetpanBuilder /opt/planck /opt/planck
COPY --from=asn1cBuilder /opt/planck /opt/planck
COPY --from=libPlanckTransportBuilder /opt/planck /opt/planck
COPY --from=libPlanckCxxBuilder /opt/planck /opt/planck
COPY --from=planckCoreBuilder /opt/planck /opt/planck
COPY --from=libWrapperBuilder /opt/planck /opt/planck
COPY --from=pyWrapperBuilder /opt/planck /opt/planck
COPY --from=pyWrapperBuilder /root/planckPythonWrapper/dist /opt/planck/dist/wrapper
COPY --from=proxyBuilder /root/proxy/dist/ /opt/planck/dist/proxy
RUN pip install /opt/planck/dist/wrapper/*.whl
RUN pip install /opt/planck/dist/proxy/*.whl
RUN rm -rf /opt/planck/dist

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
