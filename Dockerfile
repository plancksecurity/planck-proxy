
# # building SequoiaBackend
# FROM rust:alpine3.18 as sequoiaBuilder
# RUN apk update && apk add git clang-dev nettle-dev pkgconf openssl-dev make bzip2-dev sqlite-dev musl-dev llvm-dev
# WORKDIR /root/
# RUN git clone --depth=1 --branch=v1.0.0 https://git.planck.security/foundation/planckCoreSequoiaBackend.git
# WORKDIR /root/planckCoreSequoiaBackend
# COPY ./docker/planckCoreSequoiaBackend.conf local.conf
# RUN make install
# FIXME: thread 'main' panicked at 'Unable to find libclang: "the `libclang` shared library at /usr/lib/llvm16/lib/libclang.so.16.0.6 could not be opened: Dynamic loading not supported"',

# building yml2
FROM python:3.9-alpine as yml2Builder
WORKDIR /root/
RUN apk update && apk add git build-base
RUN git clone --depth=1 --branch=v2.7.5 https://git.planck.security/foundation/yml2.git
WORKDIR /root/yml2
RUN make dist

FROM alpine:3.18.3 as alpine-gcc
RUN apk update && apk add gcc git make autoconf automake libtool build-base

# building libetpan
FROM alpine-gcc as libetpanBuilder
WORKDIR /root/
RUN git clone --depth=1 --branch=master https://git.planck.security/foundation/libetpan.git
WORKDIR /root/libetpan
RUN ./autogen.sh --prefix=/opt/planck
RUN make install
WORKDIR /root/

#building ASN1C
FROM alpine-gcc as asn1cBuilder
WORKDIR /root/
RUN git clone --depth=1 --branch=v0.9.28 https://github.com/vlm/asn1c.git
WORKDIR /root/asn1c
RUN autoreconf -iv
RUN ./configure --prefix=/opt/planck
RUN make install


#building libPlanckTransport
FROM alpine-gcc as libPlanckTransportBuilder
RUN apk update && apk add python3 py3-pip
WORKDIR /root/
COPY --from=yml2Builder /root/yml2/dist/yml2-2.7.4.tar.gz /root/
RUN python3 -m venv /opt/tools/virtualenv
RUN . /opt/tools/virtualenv/bin/activate && pip install /root/yml2-2.7.4.tar.gz
RUN git clone --depth=1 --branch=v1.0.0 https://git.planck.security/foundation/libPlanckTransport.git
WORKDIR /root/libPlanckTransport
COPY ./docker/libPlanckTransport.conf local.conf
RUN . /opt/tools/virtualenv/bin/activate && export PATH="$PATH:/opt/tools/virtualenv/bin" && \
    export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 && make && make install


# building final runner
FROM alpine-gcc as runner

# COPY --from=sequoiaBuilder /opt/planck /opt/planck

# # WARNING: even if version v2.7.5 is checked out, the version is still 2.7.4
COPY --from=yml2Builder /root/yml2/dist/yml2-2.7.4.tar.gz /root/
RUN apk update && apk add python3 py3-pip
RUN python3 -m venv /opt/tools/virtualenv
RUN . /opt/tools/virtualenv/bin/activate && pip install /root/yml2-2.7.4.tar.gz

COPY --from=libetpanBuilder /opt/planck /opt/planck

COPY --from=asn1cBuilder /opt/planck /opt/planck

COPY --from=libPlanckTransportBuilder /opt/planck /opt/planck


ENV LD_LIBRARY_PATH=/opt/planck/lib
WORKDIR /root/planckCoreV3
