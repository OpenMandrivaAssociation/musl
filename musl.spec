# FIXME LTO currently results in undefined reference to __dls2 on x86_64
%global _disable_lto 1

%global targets aarch64-linux armv7hnl-linux i686-linux x86_64-linux x32-linux riscv64-linux aarch64-linuxmusl armv7hnl-linuxmusl i686-linuxmusl x86_64-linuxmusl x32-linuxmusl riscv64-linuxmusl ppc64-linuxmusl ppc64le-linuxmusl
%global long_targets %(
        for i in %{targets}; do
                CPU=$(echo $i |cut -d- -f1)
                OS=$(echo $i |cut -d- -f2)
                echo -n "$(rpm --target=${CPU}-${OS} -E %%{_target_platform}) "
        done
)

Name: musl
Version: 1.2.5
Release: 2
Source0: http://musl.libc.org/releases/%{name}-%{version}.tar.gz
Source1: import-mimalloc.sh
%define mimalloc_version 3.0.3
Source2: https://github.com/microsoft/mimalloc/archive/refs/tags/v%{mimalloc_version}.tar.gz
Source10: %{name}.rpmlintrc
Summary: The musl C library
URL: https://musl.libc.org/
License: MIT
Group: System/Libraries
# Add crtbegin.o and crtend.o from ellcc
#Patch1: musl-1.1.10-crtstuff.patch
%if "%_lib" == "lib64"
Provides: libc.so()(64bit)
%else
Provides: libc.so
%endif
# for hardlink
BuildRequires: util-linux
# Patches from upstream git
Patch0: https://www.openwall.com/lists/musl/2025/02/13/1/1#/CVE-2025-26519-1.patch
Patch1: https://www.openwall.com/lists/musl/2025/02/13/1/2#/CVE-2025-26519-2.patch
# OpenMandriva additions
Patch1000: musl-1.2.3-mimalloc-glue.patch

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
%{name} statically (users of the resulting binary will not need %{name}
installed with static linking).

%(
for i in %{long_targets}; do
	ARCH="$(echo $i |cut -d- -f1)"
	echo $ARCH |grep -q 'i.86' && ARCH=i386
	echo $ARCH |grep -q arm && ARCH=armhf
	echo $i |grep -q x32 && ARCH=x32
	echo $ARCH |grep -q ppc && ARCH="$(echo ${ARCH} |sed -e 's,ppc,powerpc,')"
	if [ "$i" = "%{_target_platform}" ]; then
		echo "%%files"
		echo "/lib/ld-musl-$ARCH.so*"
		if echo ${i} |grep -q musl; then
			# System libc...
			echo "%{_libdir}/libc.so"
			echo "/%{_lib}/libc.so"
		else
			echo "%%dir %{_libdir}/musl"
			echo "%%dir %{_libdir}/musl/lib"
			echo "%{_libdir}/musl/lib/libc.so"
			echo "%{_sysconfdir}/ld-musl-*.path"
		fi
		echo "/%{_lib}/ld-musl-*.so.1"
		echo
		echo "%%files devel"
		if echo ${i} |grep -q musl; then
			# System libc...
			echo "%{_includedir}/*"
			echo "%{_libdir}/*.o"
			echo "%{_libdir}/musl-gcc.specs"
		else
			echo "%{_libdir}/musl/include"
			echo "%{_libdir}/musl/lib/*.o"
			echo "%{_libdir}/musl/lib/musl-gcc.specs"
		fi
		echo "%{_bindir}/musl-gcc"
		echo "%{_bindir}/musl-clang"
		echo "%{_bindir}/ld.musl-clang"
		echo
		echo "%%files static-devel"
		if echo ${i} |grep -q musl; then
			# System libc...
			echo "%{_libdir}/*.a"
		else
			echo "%{_libdir}/musl/lib/*.a"
		fi
	else
		cat <<EOF
%%package -n cross-${i}-musl
Summary: Musl libc for crosscompiling to ${i} targets
BuildRequires: cross-${i}-gcc-bootstrap
BuildRequires: cross-${i}-binutils
Group: Development/Other
EOF
		main_libc=false
		if echo $i |grep -q musl; then
			# musl is the main libc for this platform...
			main_libc=true
			echo "Provides: cross-${i}-libc"
		fi
		echo
		cat <<EOF
%%description -n cross-${i}-musl
Musl libc for crosscompiling to ${i} targets.
EOF
		echo
		echo "%%files -n cross-${i}-musl"
		echo "/lib/ld-musl-$ARCH.so*"
		if $main_libc; then
			echo "%{_prefix}/${i}/lib/*"
			echo "%{_prefix}/${i}/include/*"
		else
			echo "%{_prefix}/${i}/musl"
		fi
	fi
done
)

%prep
%autosetup -p1
cd ..
tar xf %{S:2}
cd -
cp %{S:1} .
sh import-mimalloc.sh ../mimalloc-%{mimalloc_version}

for i in %{long_targets}; do
	if [ "$i" = "%{_target_platform}" ]; then
		# Native build...
		unset CROSS_COMPILE || :
		export CFLAGS="%{optflags}"
		# Set CC a variable to make it easier to force gcc
		# for musl-gcc's sake
		export CC=%{__cc}
		if echo $i |grep musl; then
			# Main libc, native
			EXTRA_ARGS="--prefix=%{_prefix} --exec-prefix=%{_prefix} --libdir=%{_libdir} --includedir=%{_includedir}"
		else
			# Secondary libc, native
			EXTRA_ARGS="--prefix=%{_libdir}/musl --exec-prefix=%{_libdir}/musl --libdir=%{_libdir}/musl/lib --includedir=%{_libdir}/musl/include"
		fi
	else
		# Set up for crosscompiling...
		export CFLAGS="-O2"
		export CROSS_COMPILE="${i}-"
		if %{__cc} --version 2>&1 |grep -q clang; then
			export CC="%{__cc} -target ${i}"
%ifarch %{aarch64}
			if echo $i |grep -qE 'i.86'; then
				# FIXME the clang aarch64->i686 crosscompiler
				# seems to be broken -- it barfs with
				# ld.lld: error: undefined symbol: __muldc3 [...]
				export CC="${i}-gcc -U__FLT_EVAL_METHOD__"
			fi
%endif
			if echo $i |grep -q x32; then
				export CC="$CC -mx32 -Wa,--x32"
			elif echo $i |grep -q x86_64; then
				export CC="$CC -m64"
			elif echo $i |grep -q aarch64; then
				export CC="$CC -m64"
			elif echo $i |grep -qE 'i.86'; then
				export CFLAGS="$CFLAGS -march=i686 -m32 -mmmx -msse -mfpmath=sse -fasynchronous-unwind-tables -mstackrealign"
			fi
		else
			export CC="${i}-gcc"
		fi
		export AS="${i}-as"
		if echo $i |grep musl; then
			# Main libc, cross
			EXTRA_ARGS="--prefix=%{_prefix}/${i} --exec-prefix=%{_prefix}/${i} --libdir=%{_prefix}/${i}/lib --includedir=%{_prefix}/${i}/include"
		else
			# Secondary libc, cross
			EXTRA_ARGS="--prefix=%{_prefix}/${i}/musl --exec-prefix=%{_prefix}/${i}/musl --libdir=%{_prefix}/${i}/musl/lib --includedir=%{_prefix}/${i}/musl/include"
		fi
	fi

	if echo ${i} |grep -q arm; then
		# FIXME currently forcing gcc to work around
		# confusion over hard-float vs. soft-float
		export CC="${i}-gcc"
	elif echo ${i} |grep -q x32; then
		# FIXME (in clang)
		# clang -target x86_64-linux-gnux32 thinks
		# x86_64-linux-gnu-ld is the best fitting linker
		export CC="${i}-gcc"
	fi

	if echo $CC |grep -q gcc; then
		export CFLAGS="$CFLAGS -fno-toplevel-reorder"
		if echo $CC |grep -q ppc; then
			export CFLAGS="$CFLAGS -fuse-ld=lld"
		fi
	else
		export CFLAGS="$CFLAGS -fuse-ld=lld"
	fi

	mkdir -p build-${i}
	cd build-${i}
	# Looks like autoconf, but isn't...
	../configure \
		$EXTRA_ARGS \
		--bindir=%_bindir \
		--syslibdir=/%{_lib} \
		--enable-shared \
		--enable-static \
		--enable-wrapper=all
	cd ..
done


%build
for i in %{long_targets}; do
	cd build-${i}
	%make_build
	cd ..
done

%install
mkdir -p %{buildroot}/%{_lib} %{buildroot}/lib
cat >>Makefile <<'EOF'

ldsoname:
	echo $(LDSO_PATHNAME)
EOF

for i in %{long_targets}; do
	[ "$i" = "%{_target_platform}" ] && continue

	cd build-${i}
	%make_install

	ldsoname=$(make --quiet ldsoname)

	cd ..

	[ -e %{buildroot}/lib/$(basename $ldsoname) ] || ln %{buildroot}%{_prefix}/$i/lib/libc.so %{buildroot}/lib/$(basename $ldsoname) || ln %{buildroot}%{_prefix}/$i/musl/lib/libc.so %{buildroot}/lib/$(basename $ldsoname)
done

cd build-%{_target_platform}
rm -f %{buildroot}%{_bindir}/*
%make_install

ldsoname=$(make --quiet ldsoname)
# The dynamic linker must be available at boot time...
# In the musl case, libc.so actually is the dynamic linker,
# so we have to move it to /%{_lib}/ld-musl-* and symlink
# its regular name there, not vice versa (as musl's build
# system does)
ARCH=$(echo $ldsoname |cut -d- -f3 |cut -d. -f1)

if echo %{_target_platform} |grep -q musl; then
	# System libc...
	mv %{buildroot}%{_libdir}/libc.so %{buildroot}$ldsoname
	ln -s $ldsoname %{buildroot}/%{_lib}/libc.so
	ln -s /%{_lib}/libc.so %{buildroot}%{_libdir}/libc.so
else
	mv %{buildroot}%{_libdir}/musl/lib/libc.so %{buildroot}$ldsoname
	ln -s $ldsoname %{buildroot}%{_libdir}/musl/lib/libc.so
	mkdir -p %{buildroot}%{_sysconfdir}
	echo %{_libdir}/musl/lib >%{buildroot}%{_sysconfdir}/ld-musl-$ARCH.path
fi

# Musl always expects its dynamic loader in /lib -- since, unlike
# glibc, the arch name is part of the file name, this doesn't
# cause conflicts.
[ -e %{buildroot}/lib/$(basename $ldsoname) ] || ln %{buildroot}$ldsoname %{buildroot}/lib
cd ..

# Hardlink identical files together -- no need to waste separate space
# on e.g. x86_64-openmandriva-linux-gnu/musl/lib/libc.so and
# x86_64-openmandriva-linux-musl/lib/libc.so
hardlink %{buildroot}
