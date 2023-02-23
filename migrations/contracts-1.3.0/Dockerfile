FROM --platform=linux/amd64 tezos/tezos:9.1.0

USER root
WORKDIR /app

RUN apk add curl python3 py3-pip bash nodejs npm pkgconfig libusb-dev libusb linux-headers eudev-dev make build-base

RUN npm -g config set user root

RUN npm i -g typescript ts-node @tacoinfra/harbinger-cli @hover-labs/tezos-msig-cli

RUN curl -s https://smartpy.io/releases/20210708-4662b0f8b1fe2186a243078f9f1ba0a4aa1c6f16/cli/install.sh > /tmp/install.sh

RUN echo 'y' | bash /tmp/install.sh

ENTRYPOINT []
