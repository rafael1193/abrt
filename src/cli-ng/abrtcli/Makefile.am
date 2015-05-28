PYFILES= \
	__init__.py \
	cli.py \
	config.py \
	filtering.py \
	l18n.py \
	match.py \
	utils.py

abrtcli_PYTHON = $(PYFILES)
abrtclidir = $(pyexecdir)/abrtcli

config.py: config.py.in
	sed -e s,\@LIBEXEC_DIR\@,$(libexecdir),g \
	$< >$@

EXTRA_DIST = config.py.in

all-local: config.py
