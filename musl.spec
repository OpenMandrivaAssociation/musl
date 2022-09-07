# Doesn't work because of mixed clang/gcc use
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
Version: 1.2.3
Release: 1
Source0: http://musl.libc.org/releases/%{name}-%{version}.tar.gz
Source1: import-mimalloc.sh
Source2: https://github.com/microsoft/mimalloc/archive/refs/tags/v2.0.6.tar.gz
Source10: %{name}.rpmlintrc
Summary: The musl C library
URL: http://musl.libc.org/
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
Patch0001: 0001-fix-incorrect-parameter-name-in-internal-netlink.h-R.patch
Patch0002: 0002-add-missing-POSIX-confstr-keys-for-pthread-CFLAGS-LD.patch
Patch0003: 0003-remove-ARMSUBARCH-relic-from-configure.patch
Patch0004: 0004-don-t-remap-internal-use-syscall-macros-to-nonexiste.patch
Patch0005: 0005-only-use-getrlimit-setrlimit-syscalls-if-they-exist.patch
Patch0006: 0006-only-fallback-to-gettimeofday-settimeofday-syscalls-.patch
Patch0007: 0007-drop-use-of-stat-operation-in-temporary-file-name-ge.patch
Patch0008: 0008-drop-direct-use-of-stat-syscalls-in-fchmodat.patch
Patch0009: 0009-provide-an-internal-namespace-safe-__fstatat.patch
Patch0010: 0010-drop-direct-use-of-stat-syscalls-in-internal-__map_f.patch
Patch0011: 0011-only-use-fstatat-and-others-legacy-stat-syscalls-if-.patch
Patch0012: 0012-provide-an-internal-namespace-safe-__fstat.patch
Patch0013: 0013-use-__fstat-instead-of-__fstatat-with-AT_EMPTY_PATH-.patch
Patch0014: 0014-fix-constraint-violation-in-qsort-wrapper-around-qso.patch
Patch0015: 0015-mntent-fix-parsing-lines-with-optional-fields.patch
Patch0016: 0016-mntent-fix-potential-mishandling-of-extremely-long-l.patch
Patch0017: 0017-ensure-distinct-query-id-for-parallel-A-and-AAAA-que.patch
Patch0018: 0018-remove-random-filename-obfuscation-that-leaks-ASLR-i.patch
Patch0019: 0019-avoid-limited-space-of-random-temp-file-names-if-clo.patch
Patch0020: 0020-in-early-stage-ldso-before-__dls2b-call-mprotect-wit.patch
Patch0021: 0021-early-stage-ldso-remove-symbolic-references-via-erro.patch
Patch0022: 0022-fix-mishandling-of-errno-in-getaddrinfo-AI_ADDRCONFI.patch
Patch0023: 0023-aarch64-add-vfork.patch
Patch0024: 0024-fix-ESRCH-error-handling-for-clock_getcpuclockid.patch
Patch0025: 0025-fix-strings.h-feature-test-macro-usage-due-to-missin.patch
Patch0026: 0026-use-syscall_arg_t-and-__scc-macro-for-arguments-to-_.patch
Patch0027: 0027-ldso-support-DT_RELR-relative-relocation-format.patch
Patch0028: 0028-ldso-process-RELR-only-for-non-FDPIC-archs.patch
Patch0029: 0029-freopen-reset-stream-orientation-byte-wide-and-encod.patch
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
sh import-mimalloc.sh ../mimalloc-2.0.6

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
		if [ "`basename %{__cc}`" = "clang" ]; then
			# FIXME remove once Clang supports RISC-V properly
			if echo $i |grep -qE '(riscv|x86_64)'; then
				export CROSS_COMPILE="${i}-"
				export CC="${i}-gcc"
			else
				export CROSS_COMPILE="${i}-"
				export CC="%{__cc} -target ${i}"
			fi
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
			export CROSS_COMPILE="${i}-"
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
	cd build-${i}
	%make_install

	ldsoname=$(make --quiet ldsoname)

	if [ "${i}" = "%{_target_platform}" ]; then
		# The dynamic linker must be available at boot time...
		# In the musl case, libc.so actually is the dynamic linker,
		# so we have to move it to /%{_lib}/ld-musl-* and symlink
		# its regular name there, not vice versa (as musl's build
		# system does)
		ARCH=$(echo $ldsoname |cut -d- -f3 |cut -d. -f1)

		if echo ${i} |grep -q musl; then
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

	else
		[ -e %{buildroot}/lib/$(basename $ldsoname) ] || ln %{buildroot}%{_prefix}/$i/lib/libc.so %{buildroot}/lib/$(basename $ldsoname) || ln %{buildroot}%{_prefix}/$i/musl/lib/libc.so %{buildroot}/lib/$(basename $ldsoname)
	fi

	cd ..
done

# Hardlink identical files together -- no need to waste separate space
# on e.g. x86_64-openmandriva-linux-gnu/musl/lib/libc.so and
# x86_64-openmandriva-linux-musl/lib/libc.so
hardlink %{buildroot}
