#!/usr/bin/env python
import sys
import os
import json
import subprocess as sp
import keyring


KW_ADD = 'add'
SERVICE_NAME = 'issh'
ALIAS_NAME = 'alias'

# TERMINAL_ARGS = [
#     'gnome-terminal',
#     '-e',
# ]
TERMINAL_ARGS = [
    'konsole',
    '--noclose',
    '-e',
]


def get_opts() -> dict:
    opts = keyring.get_password(SERVICE_NAME, ALIAS_NAME)
    if not opts:
        keyring.set_password(SERVICE_NAME, ALIAS_NAME, '[]')
        return []

    return json.loads(opts)


def get_credentials(alias: str) -> dict:
    info = keyring.get_password(SERVICE_NAME, alias)
    if info:
        return json.loads(info)


def rofi(mesg: str, opts: list = []) -> str:
    if not opts:
        mesg = 'No options'
    options = sp.Popen(['echo', '\n'.join(opts)], stdout=sp.PIPE)
    dmenu = sp.Popen(['rofi', '-dmenu', '-p', mesg], stdin=options.stdout, stdout=sp.PIPE)
    options.stdout.close()
    return dmenu.communicate()[0].decode().strip()


def show_error(mesg: str) -> None:
    mesg = '\n'.join([mesg[c:c+50] for c in range(0, len(mesg), 50)])
    sp.Popen(['yad', '--error', f'--text={mesg}'])


def add_credentials() -> None:
    a, h, u, p, k = check_output_safe([
        'yad',
        '--form',
        '--field=Alias',
        '--field=Host',
        '--field=User',
        '--field=Password::h',
        '--field=Key::fl',
    ])

    opts = get_opts()
    if a in opts:
        show_error('Alias already exist')
        return

    credentials = json.dumps({'u': u, 'h': h, 'p': p, 'k': k})
    keyring.set_password(SERVICE_NAME, a, credentials)

    opts.append(a)
    opts = json.dumps(opts)
    keyring.set_password(SERVICE_NAME, ALIAS_NAME, opts)


def connect(info: dict) -> None:
    connect_script_path = './connect_with_pass.sh'
    os.environ['___HOST___'] = info['h']
    os.environ['___USER___'] = info['u']
    os.environ['___PASS___'] = info.get('p')

    if info.get('k'):
        os.environ['___KEY___'] = info['k']
        connect_script_path = './connect_with_key.sh'

    sp.Popen(
        [*TERMINAL_ARGS, connect_script_path],
        stdout=sp.DEVNULL, stderr=sp.DEVNULL
    )


def edit_credentials(alias: str, info: dict) -> None:
    a, h, u, p, k = check_output_safe([
        'yad',
        '--form',
        f'--field=Alias', f'{alias}',
        f'--field=Host', f'{info["h"]}',
        f'--field=User', f'{info["u"]}',
        f'--field=Password::h', f'{info["p"]}',
        f'--field=Key::fl', f'{info.get("k")}',
    ])

    k = k if os.path.isfile(k) else ''

    if a != alias:
        opts = get_opts()
        if a in opts:
            return show_error('Alias already exist')
        opts.append(a)
        opts.remove(alias)
        opts = json.dumps(opts)
        credentials = json.dumps(info)

        keyring.set_password(SERVICE_NAME, ALIAS_NAME, opts)
        keyring.delete_password(SERVICE_NAME, alias)

    credentials = json.dumps({'u': u, 'h': h, 'p': p, 'k': k})
    keyring.set_password(SERVICE_NAME, a, credentials)


def copy_credentials(alias: str, info: dict) -> None:
    creds = '\n'.join(info.values())
    import pyperclip
    pyperclip.copy(f'{alias}\n{creds}')
    sp.Popen(['notify-send', 'SSHControl', 'Credentials copied to clipboard'], stderr=sp.DEVNULL)


def check_output_safe(params: list) -> str:
    try:
        return sp.check_output(params).decode().strip().split('|')[:-1]
    except:
        return ''


def delete_credentials(alias: str) -> None:
    res = rofi(f'Delete {alias}? ', ['N', 'Y'])

    if res.upper() != 'Y':
        return

    opts = get_opts()
    opts.remove(alias)
    opts = json.dumps(opts)
    keyring.delete_password(SERVICE_NAME, alias)
    keyring.set_password(SERVICE_NAME, ALIAS_NAME, opts)


if __name__ == '__main__':
    try:
        keyring.get_keyring()

        data = get_opts()

        if not (alias := rofi('SSH', data)):
            sys.exit(1)
        if alias.lower() == KW_ADD.lower():
            add_credentials()
            sys.exit(1)
        if not (info := get_credentials(alias)):
            sys.exit(1)

        res = rofi('Action', ['CONNECT', '  COPY', '  EDIT', 'DELETE']).upper()

        if res == 'CONNECT':
            try:
                connect(info)
            except Exception as e:
                show_error(str(e))
        elif res == 'EDIT':
            edit_credentials(alias, info)
        elif res == 'COPY':
            copy_credentials(alias, info)
        elif res == 'DELETE':
            delete_credentials(alias)
    except Exception as e:
        show_error(str(e))
