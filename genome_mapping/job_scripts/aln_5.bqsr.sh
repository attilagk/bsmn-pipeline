#!/bin/bash
#$ -cwd
#$ -pe threaded 36 

if [[ $# -lt 1 ]]; then
    echo "Usage: $(basename $0) [sample name]"
    exit 1
fi

source $(pwd)/run_info

set -eu -o pipefail

SM=$1

printf -- "---\n[$(date)] Start BQSR recal_table.\n"

$JAVA -Xmx58G -jar $GATK \
    -T BaseRecalibrator -nct 36 \
    -R $REF -knownSites $DBSNP -knownSites $MILLS -knownSites $INDEL1KG \
    -I $SM/bam/$SM.realigned.bam \
    -o $SM/recal_data.table

printf -- "---\n[$(date)] Start BQSR recal_table.\n"
printf -- "---\n[$(date)] Start BQSR PrintReads.\n---\n"

$JAVA -Xmx58G -jar $GATK \
    -T PrintReads -nct 36 \
    --emit_original_quals \
    -R $REF -BQSR $SM/recal_data.table \
    -I $SM/bam/$SM.realigned.bam \
    -o $SM/bam/$SM.bam
rm $SM/bam/$SM.realigned.{bam,bai}

printf -- "[$(date)] Finish BQSR PrintReads.\n---\n"
