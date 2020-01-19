Summary: Software version of a PKCS#11 Hardware Security Module
Name: softhsm
Version: 2.0.0rc1
Release: 3%{?dist}
License: BSD
Url: http://www.opendnssec.org/
Source: http://dist.opendnssec.org/source/testing/%{name}-%{version}.tar.gz
Source1: http://dist.opendnssec.org/source/testing/%{name}-%{version}.tar.gz.sig
Source2: softhsm.module
# taken from coolkey which is not build on all arches we build on
Source3: softhsm2-pk11install.c
Group: Applications/System
BuildRequires: openssl-devel >= 1.0.1e-42.el7_1.2, sqlite-devel >= 3.4.2, cppunit-devel
BuildRequires: gcc-c++, pkgconfig, p11-kit-devel, nss-devel

Requires(pre): shadow-utils
Requires: p11-kit, nss-tools
Requires: openssl-libs >= 1.0.1e-42.el7_1.2

%global _hardened_build 1

%global softhsm_module "SoftHSM PKCS #11 Module"
%global nssdb %{_sysconfdir}/pki/nssdb

%description
NOTE: This package is experimental and is only suported for use with
Identity Management.

OpenDNSSEC is providing a software implementation of a generic
cryptographic device with a PKCS#11 interface, the SoftHSM. SoftHSM is
designed to meet the requirements of OpenDNSSEC, but can also work together
with other cryptographic products because of the PKCS#11 interface.

%package devel
Summary: Development package of softhsm that includes the header files
Group: Development/Libraries
Requires: %{name} = %{version}-%{release}, openssl-devel, sqlite-devel

%description devel
The devel package contains the libsofthsm include files

%prep
%setup -q
# remove softhsm/ subdir auto-added to --libdir
sed -i "s:full_libdir/softhsm:full_libdir:g" configure
sed -i "s:libdir)/@PACKAGE@:libdir):" Makefile.in

%build
%configure --libdir=%{_libdir}/pkcs11 --with-openssl=%{_prefix} --enable-ecc --disable-gost \
           --with-migrate --enable-visibility

make %{?_smp_mflags}
# install our copy of pk11install taken from coolkey package
cp %{SOURCE3} .
gcc $(pkg-config --cflags nss) %{optflags} -c softhsm2-pk11install.c
gcc $(pkg-config --libs nss) -lpthread  -lsoftokn3 -ldl -lz %{optflags} softhsm2-pk11install.o -o softhsm2-pk11install

%check
make check

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
install -D %{SOURCE2} %{buildroot}/%{_datadir}/p11-kit/modules/softhsm.module

rm %{buildroot}/%{_sysconfdir}/softhsm2.conf.sample
rm -f %{buildroot}/%{_libdir}/pkcs11/*a
mkdir -p %{buildroot}%{_includedir}/softhsm
cp src/lib/*.h %{buildroot}%{_includedir}/softhsm
mkdir -p %{buildroot}/%{_sharedstatedir}/softhsm/tokens
install -m0755 -D softhsm2-pk11install %{buildroot}/%{_bindir}/softhsm2-pk11install

%files
%config(noreplace) %{_sysconfdir}/softhsm2.conf
%{_bindir}/*
%{_libdir}/pkcs11/libsofthsm2.so
%attr(0664,root,root) %{_datadir}/p11-kit/modules/softhsm.module
%attr(0770,ods,ods) %dir %{_sharedstatedir}/softhsm
%attr(0770,ods,ods) %dir %{_sharedstatedir}/softhsm/tokens
%doc LICENSE README.md NEWS
%{_mandir}/*/*

%files devel
%attr(0755,root,root) %dir %{_includedir}/softhsm
%{_includedir}/softhsm/*.h

%pre
getent group ods >/dev/null || groupadd -r ods
getent passwd ods >/dev/null || \
    useradd -r -g ods -d /%{_sharedstatedir}/softhsm -s /sbin/nologin \
    -c "softhsm private keys owner" ods
exit 0

%post
isThere=`modutil -rawlist -dbdir %{nssdb} | grep %{softhsm_module} || echo NO`
if [ "$isThere" == "NO" ]; then
      softhsm2-pk11install -p %{nssdb} 'name=%{softhsm_module} library=libsofthsm2.so'
fi

if [ $1 -eq 0 ]; then
   modutil -delete %{softhsm_module} -dbdir %{nssdb} -force || :
fi

%changelog
* Fri Jun 26 2015 Petr Spacek <pspacek@redhat.com> - 2.0.0rc1-3
- Dependency on OpenSSL libraries with fix for bug #1193942 was added.

* Mon Jun 01 2015 Petr Spacek <pspacek@redhat.com> - 2.0.0rc1-1
- Resolves: rhbz#1193892 Rebase to latest upstream version
- i686/ppc/s390 architectures are now included in the build

* Tue Nov 11 2014 Paul Wouters <pwouters@redhat.com> - 2.0.0b1-4
- Resolves: rhbz#1117157 Add warning to package description

* Tue Sep 30 2014 Paul Wouters <pwouters@redhat.com> - 2.0.0b1-3
- Fix softhsm2-pk11install buid and post call
- Do not use --with-objectstore-backend-db (causes issues on i686)

* Tue Sep 23 2014 Paul Wouters <pwouters@redhat.com> - 2.0.0b1-2
- Change install directory to /usr/lib*/pkcs11/
- Install pkcs11 module file
- Use official upstream tar ball
- Create ods user to own softhsm/token files
- Enable migration tools (for epel6 softhsm-v1 installs)
- Require p11-kit, nss-tools, for SoftHSM PKCS #11 Module file
- Copy pk11install.c from coolkey package which is not built on all arches
- Enable hardened build
- Add upstream official source url
- Add devel package
- Excluding i686/ppc (make check fails and we are a leave package)
- (thanks to Petr for jumping in for the initial build while I was too busy)

* Thu Sep 11 2014 Petr Spacek <pspacek@redhat.com> - 2.0.0b1-1
- Initial package for RHEL
