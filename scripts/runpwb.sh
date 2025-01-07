#!/bin/bash
id
cat user-config.tmpl > user-config.py
ls -lah user-config.py
python3 $@ #> $TOOL_DATA_DIR/logs/notifier_$(date + "%F %T").log