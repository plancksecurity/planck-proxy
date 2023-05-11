FROM debian:11-slim

#Update // Upgrade // Install system packages
RUN apt update && apt -y upgrade
RUN apt -y install sudo curl git build-essential python3 python3-pip clang pkg-config nettle-dev capnproto libssl-dev python3-lxml libtool autoconf uuid-dev sqlite3 libsqlite3-dev

#Config timezone below


#Download Sequoia Backend
RUN mkdir -p ~/src/pEpEngineSequoiaBackend
RUN cd ~/src/pEpEngineSequoiaBackend
RUN git clone https://gitea.pep.foundation/pEp.foundation/pEpEngineSequoiaBackend.git .
RUN git checkout v1.0.0
RUN echo ' \
    PREFIX="$(HOME)"/local \
    DEBUG=release \
    ' > local.conf

#Install Clang13
RUN apt -y install clang-13 && apt -y remove clang clang-11 && apt -y autoremove
RUN cp /usr/bin/clang++-13 /usr/bin/clang++ && cp /usr/bin/clang-13 /usr/bin/clang && cp /usr/bin/clang-cpp-13 /usr/bin/clang-cpp

#Copy Sequoia-Botan Files
COPY ./docker/Build.rs ~/src/pEpEngineSequoiaBackend
COPY ./docker/cargo.TOML ~/src/pEpEngineSequoiaBackend

#Install BOTAN
RUN mkdir ~/src/botan
RUN cd ~/src/botan
RUN git clone https://github.com/randombit/botan.git .
RUN ./configure.py --cc=clang --cpu=aarch64
RUN make
RUN make install

#Install Rust
RUN cd ~
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
RUN source $HOME/.cargo/env

#Install Sequoia
RUN cd ~/src/pEpEngineSequoiaBackend
RUN make install

#Install YML2
RUN mkdir -p ~/src/yml2
RUN cd ~/src/yml2
RUN git clone https://gitea.pep.foundation/fdik/yml2 .
RUN git checkout v2.7.5
RUN make install
RUN echo 'export PATH=$PATH:$HOME/src/yml2' >> ~/.bash_profile
RUN source ~/.bash_profile

#Install LibEtPan
RUN mkdir -p ~/src/libetpan
RUN cd ~/src/libetpan
RUN git clone https://gitea.pep.foundation/pEp.foundation/libetpan .
RUN mkdir build
RUN ./autogen.sh --prefix=$HOME/local
RUN make install

#Install ASN1C
RUN mkdir -p ~/src/asn1c
RUN cd ~/src/asn1c
RUN git clone https://github.com/vlm/asn1c.git .
RUN git checkout tags/v0.9.28 -b pep-engine
RUN autoreconf -iv
RUN ./configure --prefix=$HOME/local
RUN make install

#Install LibEpTransport
RUN mkdir -p ~/src/libpEpTransport
RUN cd ~/src/libpEpTransport
RUN git clone https://gitea.pep.foundation/pEp.foundation/libpEpTransport .
RUN echo 'PREFIX=$(HOME)/local' > local.conf
RUN echo 'YML2_PATH=$(HOME)/src/yml2' >> local.conf
RUN echo 'YML2_PROC=$(YML2_PATH)/yml2proc $(YML2_OPTS)' >> local.conf
RUN echo 'YML2_OPTS=--encoding=utf8' >> local.conf
RUN make 
RUN make install

#Install Planckcore
RUN mkdir -p ~/src/pEpEngine
RUN cd ~/src/pEpEngine
RUN git clone https://gitea.pep.foundation/pEp.foundation/pEpEngine .
RUN echo 'PREFIX=$(HOME)/local' > local.conf
RUN echo 'YML2_PATH=$(HOME)/src/yml2' >> local.conf
RUN echo 'ASN1C=$(PREFIX)/bin/asn1c' >> local.conf
RUN echo 'DEBUG = release' >> local.conf
RUN make install
RUN make dbinstall

#Install Python Adapter
RUN mkdir -p ~/src/pEpPythonAdapter/
RUN cd ~/src/pEpPythonAdapter/
RUN git clone https://gitea.pep.foundation/pEp.foundation/pEpPythonAdapter .

# copy planck-proxy source to user binaries
COPY . /usr/bin/planck-proxy

#Execute proxy
CMD /usr/bin/planck-proxy #CREATE CMD for EXECUTION