%global uid 27

# Currently, hevea available only in Fedora and EL-6
%if 0%{?fedora}
# No hevea for ppc64
# see https://bugzilla.redhat.com/bugzilla/show_bug.cgi?id=250253
%ifnarch ppc64 s390 s390x %{arm}
%define with_hevea 1
%endif
%endif

Name:           ejabberd
Version:        2.1.8
Release:        2%{?dist}
Summary:        A distributed, fault-tolerant Jabber/XMPP server

Group:          Applications/Internet
License:        GPLv2+
URL:            http://www.ejabberd.im/
Source0:        http://www.process-one.net/downloads/%{name}/%{version}/%{name}-%{version}.tar.gz
Source1:        ejabberd.init
Source2:        ejabberd.logrotate
Source3:	ejabberd.sysconfig

# PAM support
Source9:        ejabberdctl.pam
Source10:       ejabberdctl.apps
Source11:       ejabberd.pam

# Use ejabberd as an example for PAM service name (fedora/epel-specific)
Patch1: ejabberd-0001-Fix-PAM-service-example-name-to-match-actual-one.patch
# Introducing mod_ctlextra
Patch2: ejabberd-0002-Add-mod_ctlextra-as-an-ejabberd-module.patch
# fixed delays in s2s connections
Patch3: ejabberd-0003-Fixed-delays-in-s2s-connections.patch
# Introducing mod_admin_extra
Patch4: ejabberd-0004-Introducing-mod_admin_extra.patch
# BZ# 439583, 452326, 451554, 465196, 502361 (fedora/epel-specific)
Patch5: ejabberd-0005-Fedora-specific-changes-to-ejabberdctl.patch
# Fix so-lib permissions while installing (fedora/epel-specific)
Patch6:	ejabberd-0006-Install-.so-objects-with-0755-permissions.patch
# Will be proposed for inclusion into upstream
Patch7: ejabberd-0007-Use-versioned-directory-for-storing-docs.patch
# Backported from upstream
Patch8: ejabberd-0008-Support-SASL-GSSAPI-authentication-thanks-to-Mikael-.patch
# Introduce old AD stuff
Patch9: ejabberd-0009-Added-old-modules-for-Active-Directory.patch
# Correct version in configure (DON'T FORGET TO REMOVE IN THE NEXT VERSION)
Patch10: ejabberd-0010-last-minute-fix-correct-version-in-configure-and-in-.patch
# Disable IP restriction for ejabberdctl (seems that it doesn't work well)
Patch11: ejabberd-0011-Disable-INET_DIST_INTERFACE-by-default.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  expat-devel
BuildRequires:  openssl-devel >= 0.9.8
BuildRequires:  pam-devel
#BuildRequires:  erlang
BuildRequires:	fedora-usermgmt-devel
%if 0%{?with_hevea}
BuildRequires:  hevea
%endif

%{?FE_USERADD_REQ}
Requires(post): /sbin/chkconfig
Requires(post): /usr/bin/openssl
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
Requires(postun): /sbin/service

Provides: user(%{name}) = %{uid}
Provides: group(%{name}) = %{uid}

#Requires:       erlang
#Requires:       erlang-esasl
Requires:       usermode
# for flock in ejabberdctl
%if 0%{?el6}%{?fedora}
Requires:	util-linux-ng
%else
Requires:	util-linux
%endif


%description
ejabberd is a Free and Open Source distributed fault-tolerant
Jabber/XMPP server. It is mostly written in Erlang, and runs on many
platforms (tested on Linux, FreeBSD, NetBSD, Solaris, Mac OS X and
Windows NT/2000/XP).

%package doc
Summary: Documentation for ejabberd
%if 0%{?el6}%{?fedora}
BuildArch: noarch
Obsoletes: %{name}-doc < 2.1.4
%endif
# docdir owner
Requires: %{name} = %{version}-%{release}
Group: Documentation

%description doc
Documentation for ejabberd.

%prep
%setup -q

%patch1 -p1 -b .pam_name
%patch2 -p1 -b .mod_ctlextra
%patch3 -p1 -b .s2s_delays
%patch4 -p1 -b .mod_admin_extra
%patch5 -p1 -b .fedora_specific
%patch6 -p1 -b .fix_perms
%patch7 -p1 -b .versioned_docdir
%patch8 -p1 -b .gssapi
%patch9 -p1 -b .ad_stuff
%patch10 -p1 -b .fix_version
%patch11 -p1 -b .disable_ip_restriction_for_ejabberdctl
touch -r src/configure.fix_version src/configure


%build
pushd src
%configure --enable-odbc --enable-pam
# doesn't builds on SMP currently
make
popd
%if 0%{?with_hevea}
pushd doc
# remove pre-built docs
rm -f dev.html features.html features.pdf guide.html guide.pdf
make html pdf
popd
%endif


%install
rm -rf %{buildroot}

pushd src
make install DESTDIR=%{buildroot}
popd

# fix example SSL certificate path to real one, which we created recently (see above)
%{__perl} -pi -e 's!/path/to/ssl.pem!/etc/ejabberd/ejabberd.pem!g' %{buildroot}/etc/ejabberd/ejabberd.cfg

# fix captcha path
%{__perl} -pi -e 's!/lib/ejabberd/priv/bin/captcha.sh!%{_libdir}/%{name}/priv/bin/captcha.sh!g' %{buildroot}/etc/ejabberd/ejabberd.cfg

mkdir -p %{buildroot}/var/log/ejabberd
mkdir -p %{buildroot}/var/lib/ejabberd/spool

mkdir -p %{buildroot}%{_bindir}
ln -s consolehelper %{buildroot}%{_bindir}/ejabberdctl
install -D -p -m 0644 %{S:9} %{buildroot}%{_sysconfdir}/pam.d/ejabberdctl
install -D -p -m 0644 %{S:10} %{buildroot}%{_sysconfdir}/security/console.apps/ejabberdctl
install -D -p -m 0644 %{S:11} %{buildroot}%{_sysconfdir}/pam.d/ejabberd

# install init-script
install -D -p -m 0755 %{S:1} %{buildroot}%{_initrddir}/ejabberd

# install config for logrotate
install -D -p -m 0644  %{S:2} %{buildroot}%{_sysconfdir}/logrotate.d/ejabberd

# install sysconfig file
install -D -p -m 0644  %{S:3} %{buildroot}%{_sysconfdir}/sysconfig/ejabberd

# create room for necessary data
install -d %{buildroot}%{_datadir}/%{name}
# install sql-scripts for creating db schemes for various RDBMS
install -p -m 0644 src/odbc/mssql2000.sql %{buildroot}%{_datadir}/%{name}
install -p -m 0644 src/odbc/mssql2005.sql %{buildroot}%{_datadir}/%{name}
install -p -m 0644 src/odbc/mysql.sql %{buildroot}%{_datadir}/%{name}
install -p -m 0644 src/odbc/pg.sql %{buildroot}%{_datadir}/%{name}

# Clean up false security measure
chmod 755 %{buildroot}%{_sbindir}/ejabberdctl

# Fix permissions for captcha script
# In fact, we can also chown root:ejabberd here, but I'm not sure
# that we should care about the possibility of reading by someone
# for this *default* sript, which is not intended to be changed
chmod 755 %{buildroot}%{_libdir}/%{name}/priv/bin/captcha.sh

%pre
%{__fe_groupadd} %{uid} -r %{name} &>/dev/null || :
%{__fe_useradd} %{uid} -r -s /sbin/nologin -d /var/lib/ejabberd -M \
			-c 'ejabberd' -g %{name} %{name} &>/dev/null || :


if [ $1 -gt 1 ]; then
	# we should backup DB in every upgrade
	if ejabberdctl status >/dev/null ; then
		# Use timestamp to make database restoring easier
		TIME=$(date +%%Y-%%m-%%dT%%H:%%M:%%S)
		BACKUPDIR=$(mktemp -d -p /var/tmp/ ejabberd-$TIME.XXXXXX)
		chown ejabberd:ejabberd $BACKUPDIR
		BACKUP=$BACKUPDIR/ejabberd-database
		ejabberdctl backup $BACKUP
		# Change ownership to root:root because ejabberd user might be
		# removed on package removal.
		chown -R root:root $BACKUPDIR
		chmod 700 $BACKUPDIR
		echo
		echo The ejabberd database has been backed up to $BACKUP.
		echo
	fi

	# fix cookie path (since ver. 2.1.0 cookie stored in /var/lib/ejabberd/spool
	# rather than in /var/lib/ejabberd
	if [ -f /var/lib/ejabberd/.erlang.cookie ]; then
		cp -pu /var/lib/ejabberd/{,spool/}.erlang.cookie
		echo
		echo The ejabberd cookie file was moved.
		echo Please delete old one from /var/lib/ejabberd/.erlang.cookie
		echo
	fi
fi


%post
/sbin/chkconfig --add %{name}

# Create SSL certificate with default values if it doesn't exist
(cd /etc/ejabberd
if [ ! -f ejabberd.pem ]
then
    echo "Generating SSL certificate /etc/ejabberd/ejabberd.pem..."
    HOSTNAME=$(hostname -s 2>/dev/null || echo "localhost")
    DOMAINNAME=$(hostname -d 2>/dev/null || echo "localdomain")
    openssl req -new -x509 -days 365 -nodes -out ejabberd.pem \
                -keyout ejabberd.pem > /dev/null 2>&1 <<+++
.
.
.
$DOMAINNAME
$HOSTNAME
ejabberd
root@$HOSTNAME.$DOMAINNAME
+++
chown ejabberd:ejabberd ejabberd.pem
chmod 600 ejabberd.pem
fi)


%preun
if [ $1 = 0 ]; then
        /sbin/service %{name} stop >/dev/null 2>&1
        /sbin/chkconfig --del %{name}
fi


%postun
if [ "$1" -ge "1" ]; then
        /sbin/service %{name} condrestart >/dev/null 2>&1
fi


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)

%dir %{_docdir}/%{name}-%{version}
%doc %{_docdir}/%{name}-%{version}/COPYING

%attr(750,ejabberd,ejabberd) %dir %{_sysconfdir}/ejabberd
%attr(640,ejabberd,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/ejabberd.cfg
%attr(640,ejabberd,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/ejabberdctl.cfg
%attr(640,ejabberd,ejabberd) %config(noreplace) %{_sysconfdir}/ejabberd/inetrc

%{_initrddir}/ejabberd
%config(noreplace) %{_sysconfdir}/logrotate.d/ejabberd
%config(noreplace) %{_sysconfdir}/sysconfig/ejabberd
%config(noreplace) %{_sysconfdir}/pam.d/ejabberd
%config(noreplace) %{_sysconfdir}/pam.d/ejabberdctl
%config(noreplace) %{_sysconfdir}/security/console.apps/ejabberdctl
%{_bindir}/ejabberdctl
%{_sbindir}/ejabberdctl

%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/ebin
%dir %{_libdir}/%{name}/include
%dir %{_libdir}/%{name}/include/eldap
%dir %{_libdir}/%{name}/include/mod_muc
%dir %{_libdir}/%{name}/include/mod_proxy65
%dir %{_libdir}/%{name}/include/mod_pubsub
%dir %{_libdir}/%{name}/include/web
%dir %{_libdir}/%{name}/priv
%dir %{_libdir}/%{name}/priv/bin
%dir %{_libdir}/%{name}/priv/lib
%dir %{_libdir}/%{name}/priv/msgs

%{_libdir}/%{name}/ebin/%{name}.app
%{_libdir}/%{name}/ebin/*.beam
%{_libdir}/%{name}/include/XmppAddr.hrl
%{_libdir}/%{name}/include/adhoc.hrl
%{_libdir}/%{name}/include/cyrsasl.hrl
%{_libdir}/%{name}/include/ejabberd.hrl
%{_libdir}/%{name}/include/ejabberd_commands.hrl
%{_libdir}/%{name}/include/ejabberd_config.hrl
%{_libdir}/%{name}/include/ejabberd_ctl.hrl
%{_libdir}/%{name}/include/eldap/ELDAPv3.hrl
%{_libdir}/%{name}/include/eldap/eldap.hrl
%{_libdir}/%{name}/include/jlib.hrl
%{_libdir}/%{name}/include/mod_muc/mod_muc_room.hrl
%{_libdir}/%{name}/include/mod_privacy.hrl
%{_libdir}/%{name}/include/mod_proxy65/mod_proxy65.hrl
%{_libdir}/%{name}/include/mod_pubsub/pubsub.hrl
%{_libdir}/%{name}/include/mod_roster.hrl
%{_libdir}/%{name}/include/web/ejabberd_http.hrl
%{_libdir}/%{name}/include/web/ejabberd_web_admin.hrl
%{_libdir}/%{name}/include/web/http_bind.hrl
%{_libdir}/%{name}/priv/bin/captcha.sh
%attr(4750,root,ejabberd) %{_libdir}/%{name}/priv/bin/epam
%{_libdir}/%{name}/priv/lib/ejabberd_zlib_drv.so
%{_libdir}/%{name}/priv/lib/expat_erl.so
%{_libdir}/%{name}/priv/lib/iconv_erl.so
%{_libdir}/%{name}/priv/lib/sha_drv.so
%{_libdir}/%{name}/priv/lib/stringprep_drv.so
%{_libdir}/%{name}/priv/lib/tls_drv.so
%{_libdir}/%{name}/priv/msgs/*.msg

%dir %{_datadir}/%{name}
%{_datadir}/%{name}/mssql2000.sql
%{_datadir}/%{name}/mssql2005.sql
%{_datadir}/%{name}/mysql.sql
%{_datadir}/%{name}/pg.sql

%attr(750,ejabberd,ejabberd) %dir /var/lib/ejabberd
%attr(750,ejabberd,ejabberd) %dir /var/lib/ejabberd/spool
%attr(750,ejabberd,ejabberd) %dir /var/lock/ejabberdctl
%attr(750,ejabberd,ejabberd) %dir /var/log/ejabberd

%files doc
%defattr(-,root,root,-)
%doc %{_docdir}/%{name}-%{version}/*.html
%doc %{_docdir}/%{name}-%{version}/*.png
%doc %{_docdir}/%{name}-%{version}/*.pdf
%doc %{_docdir}/%{name}-%{version}/*.txt

%changelog
* Sat Jun 18 2011 Peter Lemenkov <lemenkov@gmail.com> - 2.1.8-2
- Fix ejabberdctl again

* Fri Jun 03 2011 Peter Lemenkov <lemenkov@gmail.com> - 2.1.8-1
- Ver. 2.1.8 (very urgent bugfix for 2.1.7)

* Wed Jun 01 2011 Peter Lemenkov <lemenkov@gmail.com> - 2.1.7-1
- Ver. 2.1.7 (bugfixes and security)

* Wed Jun 01 2011 Paul Whalen <paul.whalen@senecac.on.ca> - 2.1.6-5
- Added arm to conditional to build without hevea.

* Thu Feb 24 2011 Peter Lemenkov <lemenkov@gmail.com> - 2.1.6-4
- Updated @online@ patch

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.1.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Tue Jan 25 2011 Martin Langhoff <martin@laptop.org> 2.1.6-2
- Apply rebased @online@ patch from OLPC - EJAB-1391

* Tue Dec 14 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.6-1
- Ver. 2.1.6 (Bugfix release)

* Thu Aug 26 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.5-6
- More patches from trunk
- Rebased patches

* Thu Aug 26 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.5-5
- Backported %%patch11 from upstream (fixes LDAP)

* Wed Aug 18 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.5-4
- Add accidentally forgotten changes to ejabberd.logrotate

* Wed Aug 18 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.5-3
- Fixed http-poll (BOSH)
- New version of GSSAPI patch (backported from upstream)
- Fixed logrotate rule

* Wed Aug  4 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.5-2
- Don't require dos2unix for building anymore

* Wed Aug  4 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.5-1
- Ver. 2.1.5
- OpenSSL >= 0.9.8
- Doc-file features.* dropped (just a part of guide.*)
- Dropped upstreamed patches
- Don't use autoreconf

* Fri Jul 16 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.4-3
- Fix for Erlang/OTP R14A
- Added BR: autoconf

* Fri Jun 18 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.4-2
- No hevea for EL-6
- No hevea for s390 and s390x

* Fri Jun  4 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.4-1
- Ver. 2.1.4
- Rebased patches

* Mon Mar 29 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.3-6
- File permissions for captcha.sh were fixed

* Thu Mar 18 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.3-5
- Init-script fixed

* Thu Mar 18 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.3-4
- Really fix issue with "File operation error: eacces".

* Thu Mar 18 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.3-3
- Relax access rights of /usr/sbin/ejabberdctl (from 0550 to 0755)
- Invoke symlinked consolehelper instead of /usr/sbin/ejabberdctl
  in init-script
- Fixed "File operation error: eacces" issue. See rhbz #564686.

* Thu Mar 18 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.3-2
- Init-script enhancements

* Fri Mar 12 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.3-1
- Ver. 2.1.3
- Patches rebased

* Fri Mar  5 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.2-4
- Fixed issue with {erorr,nxdomain}

* Tue Feb 16 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.2-3
- Do not try to backup DB on every fresh install
- Do not force copying old erlang cookie file
- Add missing release notes for ver. 2.1.2
- Require erlang-esasl for krb5 support
- No such %%configure option - --enable-debug
- Patches were rebased and renumbered
- Add new BR util-linux(-ng)

* Fri Jan 29 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.2-2
- Fixed BZ #559925 (EJAB-1173)
- Changed order of rpmbuild targets in this spec to more natural one.

* Mon Jan 18 2010 Peter Lemenkov <lemenkov@gmail.com> 2.1.2-1
- Ver. 2.1.2

* Thu Dec 24 2009 Peter Lemenkov <lemenkov@gmail.com> 2.1.1-1
- Ver. 2.1.1
- Dropped patches 9,11,12,13 (accepted upstream)

* Thu Dec 10 2009 Peter Lemenkov <lemenkov@gmail.com> 2.1.0-2
- DB backups are made on every upgrade/uninstall
- Fixed installation of captcha.sh example helper
- Added patches 9,10,11,12,13 from Debian's package

* Fri Nov 20 2009 Peter Lemenkov <lemenkov@gmail.com> 2.1.0-1
- Ver. 2.1.0
- Upstream no longer providing ChangeLog
- Dropped ejabberd-build.patch (upstreamed)
- Dropped ejabberd-captcha.patch (upstreamed)
- Dropped ejabberd-decrease_buffers_in_mod_proxy65.patch (upstreamed)
- Dropped ejabberd-dynamic_compile_loglevel.patch (upstreamed)
- Dropped ejabberd-turn_off_error_messages_in_mod_caps.patch (upstreamed)
- Docs reorganized and added ability to rebuild them if possible
- Added back ppc64 target
- SQL-scripts moved to %%{_datadir}/%%{name} from %%doc

* Thu Nov  5 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.5-10
- mod_ctlextra was updated from r873 to r1020
- Fix for BZ# 533021

* Wed Sep 16 2009 Tomas Mraz <tmraz@redhat.com> - 2.0.5-9
- Use password-auth common PAM configuration instead of system-auth

* Wed Sep  9 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.5-8
- Fixed possible issue in the config file for logrotate
- Fixed possible issue while creating dummy certificate
- Added patches #5,6,7,8 from Debian

* Thu Aug 27 2009 Tomas Mraz <tmraz@redhat.com> - 2.0.5-7
- rebuilt with new openssl

* Tue Aug 25 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.5-6
- Since now, we using only ejabberdctl in the init-script (bz# 502361)

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Apr 21 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.5-3
- CAPTCHA is back - let's test it.

* Sat Apr  4 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.5-2
- Really disable CAPTCHA

* Fri Apr  3 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.5-1
- Ver. 2.0.5
- Temporarily disabled CAPTCHA support

* Sun Mar 15 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.4-2
- Support for CAPTCHA (XEP-0158)
- Updated mod_ctlextra.erl (fixed EJAB-789, EJAB-864)

* Sun Mar 15 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.4-1
- Ver. 2.0.4

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Jan 26 2009 Peter Lemenkov <lemenkov@gmail.com> 2.0.3-1
- Ver. 2.0.3
- Merged some stuff from git://dev.laptop.org/users/martin/ejabberd-xs.git

* Fri Jan 16 2009 Tomas Mraz <tmraz@redhat.com> 2.0.2-4
- rebuild with new openssl

* Thu Oct  2 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.2-3
- Fixed broken ejabberdctl (BZ# 465196)

* Sat Aug 30 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.2-2
- Added missing Requires

* Fri Aug 29 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.2-1
- Ver. 2.0.2

* Sat Aug  9 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.2-0.3.beta1
- PAM support (BZ# 452803)

* Sat Aug  9 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.2-0.2.beta1
- Fix build with --fuzz=0

* Sat Aug  9 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.2-0.1.beta1
- Version 2.0.2-beta1
- Fixed BZ# 452326
- Fixed BZ# 227270

* Sun Jun 22 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.1-4
- Last minute fix (issue with shortnames/fqdn)

* Sun Jun 22 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.1-3
-Fixed BZ# 439583, 452326, 451554

* Thu May 29 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.1-2
- Fixed BZ# 439583

* Sat May 24 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.1-1
- Ver. 2.0.1
- Upstreamed patches dropped
- No longer uses versioned libdir (/usr/lib/ejabberd-x.x.x)
- Added sql-scripts in docs-directory

* Mon May  5 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.0-3
- Fix build against R11B-2

* Sat Feb 23 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.0-2
- Disable docs again for EPEL (we haven't hevea for EPEL)

* Sat Feb 23 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.0-1
- Version 2.0.0

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 2.0.0-0.4.rc1
- Autorebuild for GCC 4.3

* Wed Jan 23 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.0-0.3.rc1
- Really enabled some previously disabled modules

* Wed Jan 23 2008 Peter Lemenkov <lemenkov@gmail.com> 2.0.0-0.2.rc1
- Enabled some previously disabled modules

* Sat Jan 19 2008 Matej Cepl <mcepl@redhat.com> 2.0.0-0.1.rc1
- Upgrade to the current upsteram version.
- Make ejabberd.init LSB compliant (missing Provides: tag)

* Thu Dec 27 2007 Matej Cepl <mcepl@redhat.com> 2.0.0-0.beta1.mc.1
- Experimental build from the upstream betaversion.

* Tue Dec 11 2007 Matej Cepl <mcepl@redhat.com> 1.1.4-2.fc9
- rebuild against new ssl library.
- rebuild against the newest erlang (see Patch
- fix %%changelog

* Wed Sep  5 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.4-1
- Drop LDAP patch
- Update mod_ctlextra
- Update to 1.1.4

* Tue Sep  4 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-11
- Fix ejabberdctl wrapper script - #276071

* Wed Aug 22 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-10
- Re-exclude ppc64

* Wed Aug 22 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-9
- Fix license
- Don't exclude ppc64

* Wed Aug 22 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-8
- Bump & rebuild to build against latest erlang package.

* Tue Jul 31 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-7
- Bump release and rebuild due to Koji hiccups.

* Tue Jul 31 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-6
- Don't try building on PPC64 since hevea isn't available on PPC64.

* Tue Jul 31 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-5
- Sigh...

* Tue Jul 31 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-4
- Don't forget to add patch.

* Thu Jul 26 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-3
- Add ejabberdctl (#199873)
- Add patch to fix LDAP authentication. (#248268)
- Add a sleep in init script between stop/start when restarting.
- LSB compliance cleanups for init script. (#246917)
- Don't mention "reload" in the init script usage string. (#227254)

* Tue Jul 24 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-2
- Update mod_ctlextra

* Fri Feb  2 2007 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.3-1
- Update to 1.1.3

* Wed Oct 11 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.2-2
- Fix logrotate script (BZ#210366)

* Mon Aug 28 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-10
- Bump release and rebuild.

* Mon Jul 3 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-9
- Updated init script - should hopefully fix some problems with status & stop commands.

* Mon Jun 26 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-8
- Bump release to that tagging works on FC-5.

* Thu Jun 22 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-7
- Oops drop bad patch.

* Thu Jun 22 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-6
- Split documentation off to a subpackage.
- Own %%{_libdir}/ejabberd-%{version}
- Mark %%{_sysconfdir}/logrotate.d/ejabberd as %%config

* Thu Jun  8 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-5
- Patch the makefile so that it adds a soname to shared libs.

* Fri May 26 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-4
- Modify AD modules not to check for group membership.

* Thu May 25 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-3
- Add some extra modules

* Wed May 24 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-2
- Munge Makefile.in a bit more...
- Change ownership/permissions - not *everything* needs to be owned by ejabberd

* Wed May 24 2006 Jeffrey C. Ollie <jeff@ocjtech.us> - 1.1.1-1
- First version for Fedora Extras
