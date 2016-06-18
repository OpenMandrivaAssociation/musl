# Debug package generation isn't compatible with musl at the moment
%define debug_package %{nil}

%bcond_with system_libc

Name: musl
Version: 1.1.14
Release: 1
Source0: http://www.musl-libc.org/releases/%{name}-%{version}.tar.gz
Source10: %{name}.rpmlintrc
Summary: The musl C library
URL: http://www.musl-libc.org/
License: MIT
Group: System/Libraries
# Add crtbegin.o and crtend.o from ellcc
Patch1: musl-1.1.10-crtstuff.patch
%if "%_lib" == "lib64"
Provides: libc.so()(64bit)
%else
Provides: libc.so
%endif

%track
prog %{name} = {
	url = http://www.musl-libc.org/download.html
	regex = "%{name}-(__VER__)\.tar\.gz"
	version = %{version}
}

%description
musl is a “libc”, an implementation of the standard library functionality
described in the ISO C and POSIX standards, plus common extensions, intended
for use on Linux-based systems. Whereas the kernel (Linux) governs access
to hardware, memory, filesystems, and the privileges for accessing these
resources, the C library is responsible for providing the actual C function
interfaces userspace applications see, and for constructing higher-level
buffered stdio, memory allocation management, thread creation and
synchronization operations, and so on using the lower-level interfaces the
kernel provides, as well as for implementing pure library routines of the C
language like strstr, snprintf, strtol, exp, sqrt, etc. 

%package devel
Summary: Development files for %{name}
Group: Development/C
Requires: %{name} = %{EVRD}

%description devel
Development files (Headers etc.) for %{name}.

%package static-devel
Summary: Static libraries for linking to %{name}
Group: Development/C
Requires: %{name}-devel = %{EVRD}

%description static-devel
Static libraries for linking to %{name}.

Install this package if you wish to develop or compile applications using
%{name} statically (users of the resulting binary won't need %{name} installed
with static linking).

%prep
%setup -q
%apply_patches
%if %{cross_compiling}
if [ "`basename %{__cc}`" = "clang" ]; then
	export CROSS_COMPILE="%{_target_platform}-"
	export CC="%{__cc} -target %{_target_platform}"
else
	export CROSS_COMPILE="`echo %{__cc} |cut -d- -f1-4`-"
	export CC=%{__cc}
fi
%else
# Setting as a variable to make it easier to force gcc
# for musl-gcc's sake
export CC=%{__cc}
%endif

if echo $CC |grep -q gcc; then
	export CFLAGS="-O2 -fuse-ld=bfd -fno-toplevel-reorder"
else
	export CFLAGS="-O2 -fuse-ld=bfd"
fi
%ifarch %arm
# fenv.s uses neon registers
echo %{__cc} |grep -q clang && export CFLAGS="$CFLAGS -no-integrated-as"
%endif

# Looks like autoconf, but isn't...
./configure \
%if ! %{with system_libc}
	--prefix=%_libdir/musl \
	--exec-prefix=%_libdir/musl \
	--libdir=%_libdir/musl/lib \
	--includedir=%_libdir/musl/include \
%else
	--prefix=%_prefix \
	--exec-prefix=%_prefix \
	--libdir=%_libdir \
	--includedir=%_includedir \
%endif
	--bindir=%_bindir \
	--syslibdir=/%{_lib} \
	--enable-shared \
	--enable-static \
	--enable-gcc-wrapper

%build
%if %{cross_compiling}
if [ "`basename %{__cc}`" = "clang" ]; then
	export CROSS_COMPILE="%{_target_platform}-"
	export CC="%{__cc} -target %{_target_platform}"
else
	export CROSS_COMPILE="`echo %{__cc} |cut -d- -f1-3`-"
fi
%endif
%make

%install
mkdir -p %{buildroot}/%{_lib}
%makeinstall_std

# The dynamic linker should be available at boot time...
# In the musl case, libc.so actually is the dynamic linker,
# so we have to move it to /%{_lib}/ld-musl-* and symlink
# its regular name there, not vice versa (as musl's build
# system does)
case %{_target_cpu} in
i?86|athlon|pentium?)
	ARCH=i386
	;;
x86_64|amd64|intel64)
	ARCH=x86_64
	;;
arm*|xscale)
	ARCH=arm
	;;
powerpc*)
	ARCH=powerpc
	;;
mips*)
	ARCH=mips
	;;
microblaze*)
	ARCH=microblaze
	;;
esac
[ -z "$ARCH" ] && exit 1

rm -f %{buildroot}/%{_lib}/ld-musl-$ARCH.so.1
%if %{with system_libc}
mv %{buildroot}%{_libdir}/libc.so %{buildroot}/%{_lib}/ld-musl-$ARCH.so.1
ln -s ld-musl-$ARCH.so.1 %{buildroot}/%{_lib}/libc.so
ln -s /%{_lib}/libc.so %{buildroot}%{_libdir}/libc.so
%else
mv %{buildroot}%{_libdir}/musl/lib/libc.so %{buildroot}/%{_lib}/ld-musl-$ARCH.so.1
ln -s /%{_lib}/ld-musl-$ARCH.so.1 %{buildroot}%{_libdir}/musl/lib/libc.so
mkdir -p %{buildroot}%{_sysconfdir}
echo %{_libdir}/musl/lib >%{buildroot}%{_sysconfdir}/ld-musl-$ARCH.path
%endif

%files
%if %{with system_libc}
%{_libdir}/libc.so
/%{_lib}/libc.so
%else
%dir %{_libdir}/musl
%dir %{_libdir}/musl/lib
%{_libdir}/musl/lib/libc.so
%{_sysconfdir}/ld-musl-*.path
%endif
/%{_lib}/ld-musl-*.so.1

%files devel
%if %{with system_libc}
%{_includedir}/*
%{_libdir}/*.o
%{_libdir}/musl-gcc.specs
%else
%{_libdir}/musl/include
%{_libdir}/musl/lib/*.o
%{_libdir}/musl/lib/musl-gcc.specs
%endif
%{_bindir}/musl-gcc

%files static-devel
%if %{with system_libc}
%{_libdir}/*.a
%else
%{_libdir}/musl/lib/*.a
%endif
