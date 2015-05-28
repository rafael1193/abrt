import os
import sys
import subprocess

import argcomplete
from argh import ArghParser, named, arg, aliases
import problem
import report as libreport

from abrtcli import config
from abrtcli.match import match_completer, match_get_problem

from abrtcli.filtering import (filter_non_reported,
                               filter_since_timestamp,
                               filter_until_timestamp)

from abrtcli.utils import (fmt_problems,
                           query_yes_no,
                           remember_cwd,
                           run_event,
                           sort_problems)


@named('list')
@aliases('ls')
@arg('--since', type=int,
     help='List only the problems more recent than specified timestamp')
@arg('--until', type=int,
     help='List only the problems older than specified timestamp')
@arg('--fmt', type=str,
     help='Output format')
@arg('--pretty', choices=config.FORMATS, default='medium',
     help='Built-in output format')
@arg('-a', '--auth', default=False,
     help='Authenticate and show all problems on this machine')
@arg('-n', '--non-reported', default=False,
     help='List only non-reported problems')
def list_problems(since, until, fmt, pretty, auth, non_reported=False):
    probs = sort_problems(problem.list(auth=auth))

    if since:
        probs = filter_since_timestamp(probs, since)

    if until:
        probs = filter_until_timestamp(probs, until)

    if non_reported:
        probs = filter_non_reported(probs)

    if not fmt:
        fmt = config.MEDIUM_FMT

    if pretty != 'medium':
        fmt = getattr(config, '{}_FMT'.format(pretty.upper()))

    out = fmt_problems(probs, fmt=fmt)

    if out:
        print(out)
    else:
        print('No problems')


@arg('-b', '--bare',
     help='Print only the problem count without any message')
@arg('-s', '--since', type=int,
     help='Print only the problems more recent than specified timestamp')
@arg('-n', '--non-reported', default=False,
     help='List only non-reported problems')
def status(since, bare=False, non_reported=False):
    probs = problem.list()

    since_append = ''
    if since:
        probs = filter_since_timestamp(probs, since)
        since_append = ' --since {}'.format(since)

    if non_reported:
        probs = filter_non_reported(probs)

    if bare:
        print(len(probs))
        return

    print('ABRT has detected {} problem(s). For more info run: abrt list{}'
          .format(len(probs), since_append))


@aliases('show')
@arg('--fmt', type=str,
     help='Output format')
@arg('--pretty', choices=config.FORMATS, default='full',
     help='Built-in output format')
@arg('MATCH', nargs='?', default='last', completer=match_completer)
def info(MATCH, fmt, pretty):
    prob = match_get_problem(MATCH)
    if not fmt:
        fmt = config.FULL_FMT

    if pretty != 'full':
        fmt = getattr(config, '{}_FMT'.format(pretty.upper()))

    print(fmt_problems(prob, fmt=fmt))


@arg('MATCH', nargs='?', default='last', completer=match_completer)
@arg('-i', help='Prompt before removal', default=False)
def rm(MATCH, i):
    prob = match_get_problem(MATCH)
    print(fmt_problems(prob, fmt=config.FULL_FMT))

    if MATCH == 'last':  # force prompt to avoid accidents
        i = True

    ret = True
    if i:
        ret = query_yes_no('Are you sure you want to delete this problem?')

    if ret:
        prob.delete()
        print('\nRemoved')


@aliases('bt')
@arg('MATCH', nargs='?', default='last', completer=match_completer)
def backtrace(MATCH, debuginfo_install=False):
    prob = match_get_problem(MATCH)
    if hasattr(prob, 'backtrace'):
        print(fmt_problems(prob, fmt=config.BACKTRACE_FMT))
    else:
        print('Problem has no backtrace')
        if isinstance(prob, problem.Ccpp):
            ret = query_yes_no('Start retracing process?')
            if ret:
                retrace(MATCH)


@arg('-l', '--local', action='store_true')
@arg('-r', '--remote', action='store_true')
@arg('-f', '--force', action='store_true')
@arg('MATCH', nargs='?', default='last', completer=match_completer)
def retrace(MATCH, local=False, remote=False, force=False):
    prob = match_get_problem(MATCH)
    if hasattr(prob, 'backtrace') and not force:
        print('Problem already has a backtrace')
        print('Run abrt retrace with -f/--force to retrace again')
        ret = query_yes_no('Show backtrace?')
        if ret:
            print(fmt_problems(prob, fmt=config.BACKTRACE_FMT))
    elif not isinstance(prob, problem.Ccpp):
        print('No retracing possible for this problem type')
    else:
        if not (local or remote):  # ask..
            ret = query_yes_no('Upload core dump and perform remote'
                               ' retracing? (It may contain sensitive data).'
                               ' If your answer is \'No\', a stack trace will'
                               ' be generated locally. Local retracing'
                               ' requires downloading potentially large amount'
                               ' of debuginfo data', default='no')

            if ret:
                remote = True
            else:
                local = True

        if remote:
            print('Remote retracing')
            run_event('analyze_RetraceServer', prob)
        else:
            print('Local retracing')
            run_event('analyze_LocalGDB', prob)


@arg('MATCH', nargs='?', default='last', completer=match_completer)
def report(MATCH):
    prob = match_get_problem(MATCH)
    libreport.report_problem_in_dir(prob.path,
                                    libreport.LIBREPORT_WAIT |
                                    libreport.LIBREPORT_RUN_CLI)


@arg('-d', '--debuginfo-install', help='Install debuginfo prior launching gdb')
@arg('MATCH', nargs='?', default='last', completer=match_completer)
def gdb(MATCH, debuginfo_install=False):
    prob = match_get_problem(MATCH)
    if not isinstance(prob, problem.Ccpp):
        which = 'This'
        if MATCH == 'last':
            which = 'Last'

        print('{} problem is not of a C/C++ type. Can\'t run gdb'
              .format(which))
        sys.exit(1)

    if debuginfo_install:
        di_install(MATCH)

    cmd = config.GDB_CMD.format(di_path=config.DEBUGINFO_PATH)

    with remember_cwd():
        os.chdir(prob.path)
        subprocess.call(cmd, shell=True)


@named('debuginfo-install')
@aliases('di')
@arg('MATCH', nargs='?', default='last', completer=match_completer)
def di_install(MATCH):
    prob = match_get_problem(MATCH)
    if not isinstance(prob, problem.Ccpp):
        which = 'This'
        if MATCH == 'last':
            which = 'Last'

        print('{} problem is not of a C/C++ type. Can\'t install debuginfo'
              .format(which))
        sys.exit(1)

    # if user is not root we have to use libexec helper
    libexec_or_not = ''
    if os.geteuid() != 0:
        libexec_or_not = config.LIBEXEC_DIR

    cmd = config.DEBUGINFO_INSTALL_CMD.format(libexec_or_not=libexec_or_not)
    with remember_cwd():
        os.chdir(prob.path)
        subprocess.call(cmd, shell=True)


def main():
    parser = ArghParser()
    parser.add_commands([
        backtrace,
        di_install,
        gdb,
        info,
        list_problems,
        report,
        retrace,
        rm,
        status,
    ])

    argcomplete.autocomplete(parser)

    try:
        parser.dispatch()
    except KeyboardInterrupt:
        sys.exit(1)
