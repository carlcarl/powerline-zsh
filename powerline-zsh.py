#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import re
import argparse


def warn(msg):
    print '[powerline-zsh] ', msg


class Color:
    # The following link is a pretty good resources for color values:
    # http://www.calmar.ws/vim/color-output.png

    PATH_BG = 237  # dark grey
    PATH_FG = 250  # light grey
    CWD_FG = 254  # nearly-white grey
    SEPARATOR_FG = 244

    REPO_CLEAN_BG = 148  # a light green color
    REPO_CLEAN_FG = 0  # black
    REPO_DIRTY_BG = 161  # pink/red
    REPO_DIRTY_FG = 15  # white

    CMD_PASSED_BG = 236
    CMD_PASSED_FG = 15
    CMD_FAILED_BG = 161
    CMD_FAILED_FG = 15

    SVN_CHANGES_BG = 148
    SVN_CHANGES_FG = 22  # dark green

    VIRTUAL_ENV_BG = 35  # a mid-tone green
    VIRTUAL_ENV_FG = 22


class Powerline:
    symbols = {
        'compatible': {
            'separator': u'\u25B6',
            'separator_thin': u'\u276F'
        },
        'patched': {
            'separator': u'\u2B80',
            'separator_thin': u'\u2B81'
        },
        'default': {
            'separator': '⮀',
            'separator_thin': '⮁'
        }
    }
    LSQESCRSQ = '\\[\\e%s\\]'
    reset = ' %f%k'

    def __init__(self, mode='default'):
        self.separator = Powerline.symbols[mode]['separator']
        self.separator_thin = Powerline.symbols[mode]['separator_thin']
        self.segments = []

    def color(self, prefix, code):
        if prefix == '38':
            return '%%F{%s}' % code
        elif prefix == '48':
            return '%%K{%s}' % code

    def fgcolor(self, code):
        return self.color('38', code)

    def bgcolor(self, code):
        return self.color('48', code)

    def append(self, segment):
        self.segments.append(segment)

    def draw(self):
        return (''.join((s[0].draw(self, s[1]) for s in zip(self.segments, self.segments[1:] + [None])))
                + self.reset)


class Segment:
    def __init__(self, powerline, content, fg, bg, separator=None, separator_fg=None):
        self.powerline = powerline
        self.content = content
        self.fg = fg
        self.bg = bg
        self.separator = separator or powerline.separator
        self.separator_fg = separator_fg or bg

    def draw(self, powerline, next_segment=None):
        if next_segment:
            separator_bg = powerline.bgcolor(next_segment.bg)
        else:
            separator_bg = powerline.reset

        return ''.join((
            powerline.fgcolor(self.fg),
            powerline.bgcolor(self.bg),
            self.content,
            separator_bg,
            powerline.fgcolor(self.separator_fg),
            self.separator))


def add_cwd_segment(powerline, cwd, maxdepth, cwd_only=False):
    #powerline.append(' \\w ', 15, 237)
    home = os.getenv('HOME')
    cwd = os.getenv('PWD')

    if cwd.find(home) == 0:
        cwd = cwd.replace(home, '~', 1)

    if cwd[0] == '/':
        cwd = cwd[1:]

    names = cwd.split('/')
    if len(names) > maxdepth:
        names = names[:2] + ['⋯ '] + names[2 - maxdepth:]

    if not cwd_only:
        for n in names[:-1]:
            powerline.append(Segment(powerline, ' %s ' % n, Color.PATH_FG, Color.PATH_BG, powerline.separator_thin, Color.SEPARATOR_FG))
    powerline.append(Segment(powerline, ' %s ' % names[-1], Color.CWD_FG, Color.PATH_BG))


def get_hg_status():
    has_modified_files = False
    has_untracked_files = False
    has_missing_files = False
    output = subprocess.Popen(['hg', 'status'], stdout=subprocess.PIPE).communicate()[0]
    for line in output.split('\n'):
        if line == '':
            continue
        elif line[0] == '?':
            has_untracked_files = True
        elif line[0] == '!':
            has_missing_files = True
        else:
            has_modified_files = True
    return has_modified_files, has_untracked_files, has_missing_files


def add_hg_segment(powerline, cwd):
    branch = os.popen('hg branch 2> /dev/null').read().rstrip()
    if len(branch) == 0:
        return False
    bg = Color.REPO_CLEAN_BG
    fg = Color.REPO_CLEAN_FG
    has_modified_files, has_untracked_files, has_missing_files = get_hg_status()
    if has_modified_files or has_untracked_files or has_missing_files:
        bg = Color.REPO_DIRTY_BG
        fg = Color.REPO_DIRTY_FG
        extra = ''
        if has_untracked_files:
            extra += '+'
        if has_missing_files:
            extra += '!'
        branch += (' ' + extra if extra != '' else '')
    powerline.append(Segment(powerline, ' %s ' % branch, fg, bg))
    return True


def get_git_status():
    has_pending_commits = True
    has_untracked_files = False
    detached_head = False
    origin_position = ""
    current_branch = ''
    output = subprocess.Popen(['git', 'status', '-unormal'], stdout=subprocess.PIPE).communicate()[0]
    for line in output.split('\n'):
        origin_status = re.findall("Your branch is (ahead|behind).*?(\d+) comm", line)
        if len(origin_status) > 0:
            origin_position = " %d" % int(origin_status[0][1])
            if origin_status[0][0] == 'behind':
                origin_position += '⇣'
            if origin_status[0][0] == 'ahead':
                origin_position += '⇡'

        if line.find('nothing to commit (working directory clean)') >= 0:
            has_pending_commits = False
        if line.find('Untracked files') >= 0:
            has_untracked_files = True
        if line.find('Not currently on any branch') >= 0:
            detached_head = True
        if line.find('On branch') >= 0:
            current_branch = re.findall('On branch ([^ ]+)', line)[0]
    return has_pending_commits, has_untracked_files, origin_position, detached_head, current_branch


def add_git_segment(powerline, cwd):
    #cmd = "git branch 2> /dev/null | grep -e '\\*'"
    p1 = subprocess.Popen(['git', 'branch'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', '-e', '\\*'], stdin=p1.stdout, stdout=subprocess.PIPE)
    output = p2.communicate()[0].strip()
    if len(output) == 0:
        return False

    has_pending_commits, has_untracked_files, origin_position, detached_head, current_branch = get_git_status()

    if len(current_branch) > 0:
      branch = current_branch
    elif detached_head:
       branch = subprocess.Popen(['git', 'describe', '--all', '--contains', '--abbrev=4', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
       branch = '((' + branch.communicate()[0].strip() + '))'
    else:
      return 'master'

    branch += origin_position

    if has_untracked_files:
        branch += ' +'

    bg = Color.REPO_CLEAN_BG
    fg = Color.REPO_CLEAN_FG

    if has_pending_commits:
        bg = Color.REPO_DIRTY_BG
        fg = Color.REPO_DIRTY_FG

    powerline.append(Segment(powerline, ' %s ' % branch, fg, bg))
    return True


def add_svn_segment(powerline, cwd):
    if not os.path.exists(os.path.join(cwd, '.svn')):
        return
    '''svn info:
        First column: Says if item was added, deleted, or otherwise changed
        ' ' no modifications
        'A' Added
        'C' Conflicted
        'D' Deleted
        'I' Ignored
        'M' Modified
        'R' Replaced
        'X' an unversioned directory created by an externals definition
        '?' item is not under version control
        '!' item is missing (removed by non-svn command) or incomplete
         '~' versioned item obstructed by some item of a different kind
    '''
    #TODO: Color segment based on above status codes
    try:
        #cmd = '"svn status | grep -c "^[ACDIMRX\\!\\~]"'
        p1 = subprocess.Popen(['svn', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p2 = subprocess.Popen(['grep', '-c', '^[ACDIMRX\\!\\~]'], stdin=p1.stdout, stdout=subprocess.PIPE)
        output = p2.communicate()[0].strip()
        if len(output) > 0 and int(output) > 0:
            changes = output.strip()
            powerline.append(Segment(powerline, ' %s ' % changes, Color.SVN_CHANGES_FG, Color.SVN_CHANGES_BG))
    except OSError:
        return False
    except subprocess.CalledProcessError:
        return False
    return True


def add_repo_segment(powerline, cwd):
    for add_repo_segment in [add_git_segment, add_svn_segment, add_hg_segment]:
        try:
            if add_repo_segment(p, cwd):
                return
        except subprocess.CalledProcessError:
            pass
        except OSError:
            pass


def add_virtual_env_segment(powerline, cwd):
    env = os.getenv("VIRTUAL_ENV")
    if env is None:
        return False
    env_name = os.path.basename(env)
    bg = Color.VIRTUAL_ENV_BG
    fg = Color.VIRTUAL_ENV_FG
    powerline.append(Segment(powerline, ' %s ' % env_name, fg, bg))
    return True


def add_root_indicator(powerline, error):
    bg = Color.CMD_PASSED_BG
    fg = Color.CMD_PASSED_FG
    if int(error) != 0:
        fg = Color.CMD_FAILED_FG
        bg = Color.CMD_FAILED_BG
    powerline.append(Segment(powerline, ' $ ', fg, bg))


def get_valid_cwd():
    try:
        cwd = os.getcwd()
    except:
        cwd = os.getenv('PWD')  # This is where the OS thinks we are
        parts = cwd.split(os.sep)
        up = cwd
        while parts and not os.path.exists(up):
            parts.pop()
            up = os.sep.join(parts)
        try:
            os.chdir(up)
        except:
            warn("Your current directory is invalid.")
            sys.exit(1)
        warn("Your current directory is invalid. Lowest valid directory: " + up)
    return cwd

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--cwd-only', action="store_true")
    arg_parser.add_argument('prev_error', nargs='?', default=0)
    args = arg_parser.parse_args()

    p = Powerline(mode='default')
    cwd = get_valid_cwd()
    add_virtual_env_segment(p, cwd)
    #p.append(Segment(' \\u ', 250, 240))
    #p.append(Segment(' \\h ', 250, 238))
    add_cwd_segment(p, cwd, 5, args.cwd_only)
    add_repo_segment(p, cwd)
    add_root_indicator(p, args.prev_error)
    sys.stdout.write(p.draw())

# vim: set expandtab:
