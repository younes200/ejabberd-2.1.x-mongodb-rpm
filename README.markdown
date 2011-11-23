# A Recipe for a Packaging Ejabberd-2.1.8-mongodb RPM on CentOS

Perform the following on a build box as root.

## Create an RPM Build Environment

    yum install rpmdevtools
    rpmdev-setuptree

## Install Prerequisites for RPM Creation

    yum groupinstall 'Development Tools'

# Edit .rpmmacros file
    vi ~/.rpmmacros
    %_topdir      %(echo $HOME)/rpmbuild
