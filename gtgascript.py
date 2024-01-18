#!/usr/bin/env python3
"""
gtgascript.py -- Generate GrADS scripts to open GTOOL3 files.
"""
import argparse
import glob
import os
import pathlib
import re
import sys


## GTOOL header items
HEADER_ITEMS = {'dset':  (1,  16, bytes.decode),
                'item':  (2,  16, bytes.decode),
                'title': (13, 32, bytes.decode),
                'units': (15, 16, bytes.decode),
                'tdur':  (27, 16, int),
                'aitm1': (28, 16, bytes.decode),
                'astr1': (29, 16, int),
                'aend1': (30, 16, int),
                'aitm2': (31, 16, bytes.decode),
                'astr2': (32, 16, int),
                'aend2': (33, 16, int),
                'aitm3': (34, 16, bytes.decode),
                'astr3': (35, 16, int),
                'aend3': (36, 16, int)}


EXCLUDED_FILES = [
    'Restart',
    'RSTA',
    'RSTO',
    'RSTEO',
    'RSTV',
]


DATE_PATTERNS = [ # (re-pattern, glob-pattern, grads-pattern)
    (re.compile(r'y[0-9]{4}'), 'y[0-9][0-9][0-9][0-9]', 'y%y4'),
    (re.compile(r'm[01][0-9]'), 'm[01][0-9]', 'm%m2'),
]


ENS_PATTERNS = [
    re.compile(r'\b(run|ens)(?P<enum>0*1)\b'),
]


def match_ensemble_paths(path):
    """
    Search 'run1', 'run01', ...
    """
    tmpl_path = str(path)
    ndigits = 0
    num_ens = 1
    for pat in ENS_PATTERNS:
        mat = pat.search(tmpl_path)
        if mat:
            prefix = mat.group(1)
            ndigits = len(mat.group('enum'))
            path0 = path[:mat.start()]
            path1 = path[mat.end():]

            tmpl_path = ''.join((path0, prefix, '%e', path1))
            glob_path = ''.join((path0, prefix, '[0-9]' * ndigits, path1))

            num_ens = len(glob.glob(glob_path))
            break

    return tmpl_path, ndigits, num_ens


def match_date_paths(path):
    """
    Match with grads's template pattern.
    """
    tmpl_path = str(path)
    matched = False
    for pat, _, tmpl in DATE_PATTERNS:
        mat = pat.search(tmpl_path)
        if mat:
            matched = True
            tmpl_path = re.sub(pat, tmpl, tmpl_path)

    num_matched = 1
    if matched:
        glob_path = str(path)
        for pat, wild, _ in DATE_PATTERNS:
            mat = pat.search(glob_path)
            if mat:
                glob_path = re.sub(pat, wild, glob_path)

        num_matched = len(glob.glob(glob_path))

    return tmpl_path, num_matched


def size_of_time(num_tmpls, tdur):
    """
    The size of T-axis (including time-template).
    This is a very rough estimate.

    -num_tmpls: the number of matched template paths (e.g., y????)
    -tdur: time duration in hour.
    """
    if 30 * 24  <= tdur <= 31 * 24:
        return 12 * num_tmpls

    if tdur <= 24:
        return int(24. * 365.25 * num_tmpls / max(tdur, 1))

    if tdur >= 360 * 24 and num_tmpls == 1:
        return 500

    return max(num_tmpls, 2)


def write_open_commands(output, filelist, common_len, command_format):
    """
    Write `gtopen` and/or `vgtopen` for each file.
    """
    def _sortkey(meta):
        return meta['aend3'] - meta['astr3']

    def _varname(path):
        return path.name.replace('-', '_') \
                        .replace('+', '_') \
                        .replace('.', '_')

    # Sort by the number of z-level (reverse).
    # Use `gtopen` for the variable having the largest z-level.
    vlist = sorted([(_sortkey(meta), path, meta) for (path, meta) in filelist],
                   reverse=True)

    # Comments for each variable.
    output.write('* {:>12s} {:>8s}    {}\n'.format('Var', 'Zlev', 'Title'))
    output.write('* ' + '-' * 62 + '\n')
    for _, path, meta in vlist:
        output.write('* {:>12s} {:>8d}    {} [{}]\n'
                     .format(_varname(path),
                             meta['aend3'] - meta['astr3'] + 1,
                             meta['title'],
                             meta['units']))
    output.write('\n')

    # `gtopen`, `vgtopen`, .... command.
    command = ' gtopen'
    for _, path, _ in vlist:
        pathstr = str(path)
        pathstr = pathstr[common_len:]

        output.write(command_format.format(command, pathstr))
        command = 'vgtopen'


def write_script(output, use_template, filelist):
    """
    Write a script for each group.

    -filelist: a list of [(path0, meta0), (path1, meta1), ...]
    """
    output.write('****  GrADS script (gtopen/vgtopen)\n\n')

    attr = filelist[0][1]

    common_path = os.path.commonpath([path for (path, _) in filelist])
    output.write(f'dir0 = "{common_path}"\n')

    # Ensembles
    tmpldir = common_path
    ndigits = 0
    num_ens = 1
    if use_template and len(common_path) > 0:
        tmpldir, ndigits, num_ens = match_ensemble_paths(common_path)

    # Time series
    time_count = 1
    if use_template and len(common_path) > 0:
        _, time_count = match_date_paths(common_path)

    if time_count > 1 or num_ens > 1:
        tmpldir, _ = match_date_paths(tmpldir)
        output.write(f'tmpl = "{tmpldir}"\n')

        tdur = attr['tdur']
        tsize = size_of_time(time_count, tdur)

        output.write('\n* tsize: The size of T-axis (fix if incorrect).\n')
        output.write(f'tsize = {tsize}\n')
        command_format = "'{0} ' dir0'{1} ' tmpl'{1} ' tsize\n"
    else:
        command_format = "'{0} ' dir0'{1}'\n"

    # edef (ensemble def)
    if num_ens > 1:
        efmt = f' %0{ndigits}d' if ndigits > 1 else ''
        output.write(f'\n* The number of ensembles: {num_ens}\n')
        output.write(f"'gtoptions edef {num_ens}{efmt}'\n")

    # gtopen/vgtopen
    output.write('\n')
    write_open_commands(output, filelist, len(common_path), command_format)

    # Extra
    if (attr['xsize'], attr['ysize'], attr['zsize']).count(1) >= 2:
        output.write("\n'set t 1 last'\n")


def metadata_in_gtool3(path):
    """
    Get some attributes for grouping.

    Return None if not valid GTOOL3 format.
    """
    rbuf = []
    with open(path, 'rb') as fp:
        fp.seek(4)
        rbuf = fp.read(1024)

    if len(rbuf) != 1024:
        return None

    meta = {}
    try:
        for key, (idx, size, func) in HEADER_ITEMS.items():
            off = 16 * idx
            value = rbuf[off:off + size].strip()
            meta[key] = func(value)
    except ValueError:
        return None

    meta['xsize'] = meta['aend1'] - meta['astr1'] + 1
    meta['ysize'] = meta['aend2'] - meta['astr2'] + 1
    meta['zsize'] = meta['aend3'] - meta['astr3'] + 1
    return meta


def merge_groups(groups):
    """
    groups: [(key0, [value,...]), (key1, [value,...]), ...]

    grouping_key: (tdur, aitm1, aitm2, aitm3, nx, ny, nz)
    """
    def movable(key):
        return key[3] in ('NULL', 'NUMBER1000')

    def acceptable(dest, src):
        return (dest[0:3] == src[0:3]
                and dest[4:6] == src[4:6]
                and dest[6] >= src[6])

    newgroups = []

    # Copy except for the movable.
    for key, vlist in groups:
        if not movable(key):
            newgroups.append((key, vlist))

    if len(newgroups) == 0:
        return groups

    # Merge into the acceptable.
    for key, vlist in groups:
        if movable(key):
            merged = False
            for dest_key, dest_list in newgroups:
                if acceptable(dest_key, key):
                    dest_list.extend(vlist)
                    merged = True

            if not merged:
                newgroups.append((key, vlist))

    return newgroups


def grouping_key(meta):
    """
    Return the key for grouping.
    """
    # Rename axis for better grouping.
    def _rename_axis(axis):
        axis = axis.replace('OCLONTPV', 'OCLONTPT') \
                   .replace('OCLATTPV', 'OCLATTPT') \
                   .replace('OCLONV', 'OCLONT') \
                   .replace('OCLATV', 'OCLATT') \
                   .replace('OCDEPM', 'OCDEPT') \
                   .replace('WLEV', 'GLEV') \
                   .replace('SFC1', 'NULL')

        return axis or 'NULL'

    return (meta['tdur'],
            _rename_axis(meta['aitm1']),
            _rename_axis(meta['aitm2']),
            _rename_axis(meta['aitm3']),
            meta['xsize'],
            meta['ysize'],
            meta['zsize'])


def grouping(filelist, keyfunc):
    """
    -filelist: a list of [(path0, meta0), (path1, meta1), ...]
    -keyfunc: a function of key.

    Generate a grouped item (key, alist).
    """
    zlist = sorted([(keyfunc(x[1]), x) for x in filelist])

    kprev = None
    output = []
    for key, value in zlist:
        if key != kprev:
            if len(output) > 0:
                yield (kprev, output)
                output = []
            kprev = key

        output.append(value)

    if len(output) > 0:
        yield (kprev, output)


def input_yesno(prompt, default='n'):
    """
    Return True or False from user input.
    """
    ans = '?'
    try:
        while ans not in ('y', 'n', ''):
            ans = input(prompt)
            ans = ans.strip().lower()
    except EOFError:
        ans = ''

    if ans == '':
        ans = default

    return ans == 'y'


def normal_files(top):
    """
    Generate each path (only normal file) under `top`.
    """
    if os.path.isdir(top):
        for root, _, filenames in os.walk(top):
            for name in filenames:
                if name not in EXCLUDED_FILES:
                    yield os.path.join(root, name)
    elif os.path.isfile(top):
        yield top


def list_groups(tops):
    """
    List groups.

    -tops: a list of (top) directories and/or files.
    """
    allfiles = []
    for top in tops:
        for path in normal_files(top):
            meta = metadata_in_gtool3(path)
            if meta:
                allfiles.append((pathlib.Path(path).absolute(), meta))

    groups = list(grouping(allfiles, grouping_key))
    groups = merge_groups(groups)
    return groups


def create_scripts(tops, use_tmpl, dryrun, outdir):
    """
    Create scripts for each group.
    """
    # gkey: (tdur, aitm1, ...)
    # filelist: [(path0, meta0), (path1, meta1), ...]
    for gkey, filelist in list_groups(tops):
        if dryrun:
            write_script(sys.stdout, use_tmpl, filelist)
        else:
            name = '{1}-{2}-{3}-{0}hr-X{4}-Y{5}-Z{6}.gs'.format(*gkey)
            name = outdir.joinpath(name)

            if (os.path.exists(name)
                and not input_yesno(f'overwrite {name} [y/N]? ')):
                continue

            with open(name, 'w', encoding='latin-1') as output:
                print(f'Writing a script to {name} ...', end='')
                write_script(output, use_tmpl, filelist)
                print(' done', end='\n')


def main():
    """
    Options:
      -n: Dry run
      -o: Output directory
      -s: Do not use templates
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('files',
                        type=str,
                        help='input files...',
                        nargs='*',
                        action='store')

    parser.add_argument('-n', '--dryrun',
                        help='Dry run',
                        dest='dryrun',
                        action='store_true')

    parser.add_argument('-o', '--outdir',
                        help='Output directory',
                        dest='outdir',
                        default='',
                        action='store')

    parser.add_argument('-s',
                        help='Do not use templates',
                        dest='use_tmpl',
                        action='store_false')

    args = parser.parse_args()

    try:
        outdir = pathlib.Path(args.outdir)
        if not outdir.is_dir():
            raise RuntimeError(f'{outdir}: No such a directory')

        create_scripts(args.files, args.use_tmpl, args.dryrun, outdir)
    except Exception as err:
        print(err, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
