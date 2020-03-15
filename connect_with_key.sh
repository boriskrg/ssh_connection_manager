#!/usr/bin/bash

echo -ne "\033]30;SSH: $___USER___@$___ALIAS___\007"

ssh -i $___KEY___ $___USER___@$___HOST___

unset ___KEY___
unset ___USER___
unset ___HOST___
unset ___ALIAS___

$SHELL

