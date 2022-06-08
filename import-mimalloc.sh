#!/bin/sh
if [ -z "$1" ]; then
	echo "Usage: $0 /path/to/mimalloc"
	echo "	Where /path/to/mimalloc is the path to the mimalloc source,"
	echo "	with the tag/branch you want to import already checked out."
	exit 1
fi
cd "$(realpath $(dirname $0))"
cp $1/src/* $1/include/* .
# We don't need the overrides, given we're system malloc
rm alloc-override*
sed -i -e '/alloc-override.c/d' alloc.c
# Name functions the way musl likes it
# glue code must come after mimalloc.h because
# of __attribute__((malloc))
sed -i -e '/mimalloc.h/a#include "glue.h"' alloc.c
sed -i -e '/mimalloc.h/i#include "glue.h"' alloc-aligned.c alloc-posix.c heap.c
# page-queue.c is supposed to be #included by page.c and not
# built standalone (but musl's build system builds $MALLOC/*.c)
mv page-queue.c page-queue.inc
sed -i -e 's,page-queue.c,page-queue.inc,' page.c
# musl's define weak clashes with mimalloc's use of
# __attribute((weak))
sed -i -e 's,__attribute((weak)),weak,g' *.c
# This seems to be obsolete -- not referenced in mimalloc's
# CMake files and not included by anything
rm region.c
# Helper for including mimalloc into a project. Not useful
# in our context.
rm static.c
# musl aligned_alloc() is the same as mimalloc's mi_malloc_aligned... but
# with parameters reversed
cat >>alloc.c <<EOF
void *aligned_alloc(size_t align, size_t len) {
	return mi_malloc_aligned(len, align);
}
EOF
# FIXME malloc_donate() is currently not implemented for mimalloc. Implement a
# stub so ldso doesn't freak out, but it would be nice to implement this
# properly to allow reclaiming the wasted space from shared libraries...
cat >>alloc.c <<EOF
void __malloc_donate(char *start, char *end) {
}
EOF
