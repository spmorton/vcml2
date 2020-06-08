# sample usage:
#    docker build -t rmb/vcml2 .


FROM ubuntu

MAINTAINER Scott P Morton <spm3c@mtmail.mtsu.edu>

## RMB COMMENTED OUT
# ENV HOME /root

RUN apt-get update
RUN apt-get install -y openssh-server \
                            bash \
                            csh \
                            ksh \
                            tcsh \
                            vim-tiny \
                            nano \
                            ssh \
                            libxml2
# RUN mkdir /var/run/sshd

RUN echo 'root:outcast' | chpasswd

## RMB ADDED
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

## RMB ADDED
# SSH login fix. Otherwise user is kicked off after login
## RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

## RMB ADDED
EXPOSE 22  

CMD ["/bin/bash","--login"]

