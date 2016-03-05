# This Dockerfile will build an image that is configured
# to run Fluentd with an Elasticsearch plug-in and the
# provided configuration file.
# TODO(a-robinson): Use a lighter base image, e.g. some form of busybox.
# The image acts as an executable for the binary /usr/sbin/td-agent.
# Note that fluentd is run with root permssion to allow access to
# log files with root only access under /var/log/containers/*
# Please see http://docs.fluentd.org/articles/install-by-deb for more
# information about installing fluentd using deb package.

FROM ubuntu:14.04
MAINTAINER Guruprasad Sridharan guruprasad.sridharan@olacabs.com

# Ensure there are enough file descriptors for running Fluentd.
RUN ulimit -n 65536

# Disable prompts from apt.
ENV DEBIAN_FRONTEND noninteractive

# Install prerequisites.
RUN apt-get update && \
    apt-get install -y -q curl make g++ ruby-dev patch && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Fluentd.
RUN /usr/bin/curl -L https://td-toolbelt.herokuapp.com/sh/install-ubuntu-trusty-td-agent2.sh | sh

# Change the default user and group to root.
# Needed to allow access to /var/log/docker/... files.
RUN sed -i -e "s/USER=td-agent/USER=root/" -e "s/GROUP=td-agent/GROUP=root/" /etc/init.d/td-agent

# Install the Kafka Fluentd plug-in.
RUN td-agent-gem install fluent-plugin-kafka

# Copy the Fluentd configuration file.
COPY conf/td-agent.conf /etc/td-agent/td-agent.conf

# Copy the Logrotate configuration file.
COPY logrotate/docker /etc/logrotate.d/docker

RUN rm /etc/logrotate.d/td-agent

# Force stupid logrotate to run for the first time and suppress non-zero error code
RUN logrotate -vf /etc/logrotate.d || :

RUN sed -i -e "s/#cron\.\*/cron\.\*/" /etc/rsyslog.d/50-default.conf
COPY logrotate/root_crontab /tmp/root_crontab

RUN apt-get install -y -q python supervisor python-pip && \
    pip install pyformance potsdb docker-py supervisor-stdout
COPY conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY scripts/docker-stats.py /tmp/docker-stats.py

# Run the Fluentd service.
CMD /etc/init.d/rsyslog start && /usr/sbin/cron start && crontab /tmp/root_crontab && /usr/sbin/td-agent
