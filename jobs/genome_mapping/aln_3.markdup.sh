#!/bin/bash
#$ -cwd
#$ -pe threaded 12

trap "exit 100" ERR

if [[ $# -lt 1 ]]; then
    echo "Usage: $(basename $0) [sample name]"
    false
fi

SM=$1

source $(pwd)/$SM/run_info

set -o nounset
set -o pipefail

DONE=$SM/run_status/aln_3.markdup.done

printf -- "---\n[$(date)] Start markdup.\n"

if [[ -f $DONE ]]; then
    echo "Skip this step."

else
    $JAVA -Xmx30G -Djava.io.tmpdir=tmp -jar $PICARD MarkDuplicates \
        I=$SM/alignment/$SM.merged.bam \
        O=$SM/alignment/$SM.markduped.bam \
        METRICS_FILE=$SM/alignment/markduplicates_metrics.txt \
        OPTICAL_DUPLICATE_PIXEL_DISTANCE=2500 \
        CREATE_INDEX=true \
        TMP_DIR=tmp

    rm $SM/alignment/$SM.merged.bam{,.bai}
    touch $DONE
fi

printf -- "[$(date)] Finish markdup.\n---\n"
