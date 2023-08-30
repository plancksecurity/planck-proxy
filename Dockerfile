FROM alpine:3.18.3

# Install necessary packages and dependencies
RUN apk update && apk --no-cache add curl git build-base python3 py3-pip pkgconf nettle-dev capnproto libressl-dev py3-lxml libtool autoconf libuuid sqlite-libs sqlite-dev

# CREATE A SYMLINK BETWEEN LOCAL/LIB and /USR/BIN
RUN mkdir ~/local
RUN mkdir ~/local/lib
RUN ln -s /usr/lib ~/local/lib
RUN chmod 777 ~/local/lib

# Install Clang 14
RUN apk add clang14 llvm
RUN cp /usr/bin/clang++-14 /usr/bin/clang++ \
    && cp /usr/bin/clang-14 /usr/bin/clang \
    && cp /usr/bin/cpp /usr/bin/clang-cpp

#Install BOTAN
RUN mkdir -p /home/src/botan
WORKDIR /home/src/botan
RUN git clone https://github.com/randombit/botan.git . && git checkout 3.1.1
RUN ./configure.py --cc=clang --prefix=$HOME/local
RUN make
RUN make install

#Install Rust
WORKDIR /home/
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

#Download Sequoia Backend
RUN mkdir -p /home/src/pEpEngineSequoiaBackend
WORKDIR /home/src/pEpEngineSequoiaBackend
RUN git clone https://gitea.pep.foundation/pEp.foundation/pEpEngineSequoiaBackend.git .
RUN git checkout v1.0.0
RUN echo ' \
    PREFIX="$(HOME)"/local \
    DEBUG=release \
    ' > local.conf

#Copy Sequoia-Botan Files
COPY ./docker/build.rs /home/src/pEpEngineSequoiaBackend
COPY ./docker/Cargo.toml /home/src/pEpEngineSequoiaBackend

#Install Sequoia
WORKDIR /home/src/pEpEngineSequoiaBackend
# Set the RUST_BACKTRACE environment variable
ENV RUST_BACKTRACE=1
ENV LD_LIBRARY_PATH=/usr/lib/llvm14/lib
# RUN source $HOME/.cargo/env && make install


# # Install project dependencies
# RUN apk update && apk --no-cache add docker python3 postfix vim


# # Copy the proxy files
# COPY ./src/* /opt/planck-proxy/

# # Copy the postfix configuration files
# COPY ./docker/postfix/* /etc/postfix/
# RUN postmap /etc/postfix/transport
# RUN postmap /etc/postfix/transport-proxy

# # Add the "proxy" user without a password
# RUN adduser --disabled-password proxy

# # Create the workdir and set permissions
# RUN mkdir /home/proxy/work
# WORKDIR /home/proxy/work
# RUN chown proxy:proxy . -R

# # Copy the settings file
# COPY ./docker/docker-settings.json /home/proxy/settings.json

# # Start Postfix service
# # CMD ["postfix", "start-fg"]
