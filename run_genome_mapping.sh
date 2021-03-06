#!/bin/bash

PIPE_HOME=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
PYTHON3=$PIPE_HOME/$(grep PYTHON3 $PIPE_HOME/config.ini |cut -f2 -d=|sed 's/^ \+//')

cmd=$(basename $0)
$PYTHON3 $PIPE_HOME/jobs/run_genome_mapping.py $@ \
    1> >(sed "s/run_genome_mapping.py/$cmd/" >&1) \
    2> >(sed "s/run_genome_mapping.py/$cmd/" >&2)
