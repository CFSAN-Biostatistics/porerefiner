#!/bin/bash

set -e

cp porerefiner/porerefiner.service ~/.config/systemd/user/
cp porerefiner/porerefiner.app.service ~/.config/systemd/user/

systemctl --user enable porerefiner.service
systemctl --user enable porerefiner.app.service
