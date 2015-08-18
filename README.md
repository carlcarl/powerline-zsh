Powerline style prompt for Zsh
===============================

*This is a fork from https://github.com/milkbikis/powerline-bash*

A [Powerline](https://github.com/Lokaltog/vim-powerline) like prompt for Zsh:

![Powerline-Zsh Screenshot](http://i.imgur.com/QfDe3yP.png)
![Powerline-Zsh Screenshot2](http://i.imgur.com/f1kQcLv.png)

*  Shows some important details about the git branch:
    *  Displays the current git branch which changes background color when the branch is dirty
    *  A '+' appears when untracked files are present
    *  When the local branch differs from the remote, the difference in number of commits is shown along with '⇡' or '⇣' indicating whether a git push or pull is pending
*  Changes color if the last command exited with a failure code
*  If you're too deep into a directory tree, shortens the displayed path with an ellipsis
*  Shows the current Python [virtualenv](http://www.virtualenv.org/) environment
*  It's all done in a Python script, so you could go nuts with it

# Setup

* This script uses ANSI color codes to display colors in a terminal. These are notoriously non-portable, so may not work for you out of the box, but try setting your $TERM to xterm-256color, because that works for me.
i.e. edit your `.zshrc` file to add:

    ```shell
    export TERM='xterm-256color'
    ```

If you still face problems seeing colors then read this: https://gist.github.com/3749830#file_powerline_zsh_instructions.md

* Patch the font you use for your terminal.
Download the font from: https://github.com/Lokaltog/vim-powerline/wiki/Patched-fonts
Follow the instructions: https://github.com/Lokaltog/vim-powerline/tree/develop/fontpatcher#font-patching-guide


* Clone this repository somewhere:

    ```shell
    git clone https://github.com/carlcarl/powerline-zsh
    ```

* Create a symlink to the python script in your home:
   
    ```shell
    ln -s <path/to/powerline-zsh.py> ~/powerline-zsh.py
    ```

If you don't want the symlink, just modify the path in the `.zshrc` command below

* Now add the following to your `.zshrc`:

```shell
function _update_ps1()
{
    export PROMPT="$(~/powerline-zsh.py $?)"
}
precmd()
{
    _update_ps1
}
```

* powerline-zsh.py usage:

	optional arguments:
	-h, --help  show this help message and exit
	--cwd-only  Hide parent directory
	--hostname  Show hostname at the begin
	-m <mode>   Choose icon font: default, compatible, patched or konsole.
				Default is "default"

# Python version note

Most of the distros use `Python2` as default, however, Some distros like `Archlinux` use `Python3`. The earlier version of `powerline-zsh` is not compatible with `Python3`. With such condition, you have two ways to solve this issue.

1. Use the newest version of `powerline-zsh`. Just download from the `master` branch.
2. Modify the `.zshrc` content, use `python2` to execute it.

```shell
function _update_ps1()
{
    export PROMPT="$(python2 ~/powerline-zsh.py $?)"
}
precmd()
{
    _update_ps1
}
```


# Pypy note

You can use `pypy` to speed up your script execution, in your `.zshrc`:


```shell
function _update_ps1()
{
    error=$?
    if [[ -s "/usr/local/bin/pypy" ]]; then
        export PROMPT="$(pypy ~/powerline-zsh.py $error)"
    else
        export PROMPT="$(~/powerline-zsh.py $error)"
    fi
}
precmd()
{
    _update_ps1
}
```


# konsole user note

You may not see the icons when using konsole. To solve this problem, you can use `-m` option:


```shell
function _update_ps1()
{
    export PROMPT="$(~/powerline-zsh.py -m konsole $?)"
}
precmd()
{
    _update_ps1
}
```

