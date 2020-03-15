#!/usr/bin/bash

echo -ne "\033]30;SSH: $___USER___@$___ALIAS___\007"

sshpass -p $___PASS___ ssh $___USER___@$___HOST___

unset ___PASS___
unset ___USER___
unset ___HOST___
unset ___ALIAS___

$SHELL

