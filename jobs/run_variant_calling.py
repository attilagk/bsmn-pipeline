#!/usr/bin/env python3

import argparse
import os
import sys
from collections import defaultdict, deque

cmd_home = os.path.dirname(os.path.realpath(__file__))
pipe_home = os.path.normpath(cmd_home + "/..")
job_home = cmd_home + "/variant_calling"
sys.path.append(pipe_home)

from library.config import run_info, run_info_append, log_dir
from library.login import synapse_login, nda_login
from library.parser import sample_list
from library.job_queue import GridEngineQueue
q = GridEngineQueue()

def main():
    args = parse_args()

    synapse_login()
    nda_login()

    global down_jid_queue
    down_jid_queue = deque([None] * args.con_down_limit)

    samples = sample_list(args.sample_list)
    for (sample, filetype), sdata in samples.items():
        print("- Sample: " + sample)

        f_run_jid = sample + "/run_jid"
        if q.num_run_jid_in_queue(f_run_jid) > 0:
            print("There are submitted jobs for this sample.")
            print("Skip to submit jobs.\n")
            continue
        q.set_run_jid(f_run_jid, new=True)

        f_run_info = sample + "/run_info"
        run_info(f_run_info)
        run_info_append(f_run_info, "\n#RUN_OPTIONS")
        run_info_append(f_run_info, "UPLOAD={}".format(args.upload))
        run_info_append(f_run_info, "RUN_CNVNATOR={}".format(args.run_cnvnator))
        run_info_append(f_run_info, "RUN_MUTECT_SINGLE={}".format(args.run_mutect_single))
        if args.run_gatk_hc:
            ploidy = " ".join(str(i) for i in args.run_gatk_hc)
            run_info_append(f_run_info, "RUN_GATK_HC=True\nPLOIDY=\"{}\"".format(ploidy))
        else:
            run_info_append(f_run_info, "RUN_GATK_HC={}".format(args.run_gatk_hc))

        if filetype == "fastq":
            raise Exception("The input filetype should be bam or cram.")

        global down_jid
        jid_list = []
        for fname, loc in sdata:
            down_jid = down_jid_queue.popleft()
            jid = q.submit(opt(sample, down_jid), 
                    "{job_home}/pre_1.download.sh {sample} {fname} {loc}".format(
                        job_home=job_home, sample=sample, fname=fname, loc=loc))
            jid_list.append(jid)
            down_jid_queue.append(jid)
        jid = ",".join(jid_list)

        if filetype == "bam":
            jid = q.submit(opt(sample, jid),
                "{job_home}/pre_2.bam2cram.sh {sample}".format(
                    job_home=job_home, sample=sample))
            jid = q.submit(opt(sample, jid),
                "{job_home}/pre_2b.unmapped_reads.sh {sample}".format(
                    job_home=job_home, sample=sample))

        jid = q.submit(opt(sample, jid),
            "{job_home}/pre_3.run_variant_calling.sh {sample}".format(
                job_home=job_home, sample=sample))
        q.submit(opt(sample, jid),
            "{job_home}/pre_4.upload_cram.sh {sample}".format(
                job_home=job_home, sample=sample))

        print()

def opt(sample, jid=None):
    opt = "-r y -j y -o {log_dir} -l h_vmem=4G".format(log_dir=log_dir(sample))
    if jid is not None:
        opt = "-hold_jid {jid} {opt}".format(jid=jid, opt=opt)
    return opt

def parse_args():
    parser = argparse.ArgumentParser(description='Variant Calling Pipeline')
    parser.add_argument('--con-down-limit', metavar='int', type=int,
        help='''The maximum allowded number of concurrent downloads
        [ Default: 6 ]''', default=6)
    parser.add_argument('--upload', metavar='syn123', 
        help='''Synapse ID of project or folder where to upload result cram files. 
        If it is not set, the result cram files will be locally saved.
        [ Default: None ]''', default=None)
    parser.add_argument('--run-gatk-hc', metavar='ploidy', type=int, nargs='+', default=False)
    parser.add_argument('--run-mutect-single', action='store_true')
    parser.add_argument('--run-cnvnator', action='store_true')
    parser.add_argument('--sample-list', metavar='sample_list.txt', required=True,
        help='''Sample list file.
        Each line format is "sample_id\\tfile_name\\tlocation".
        Lines staring with "#" will omitted.
        Header line should also start with "#".
        Trailing columns will be ignored.
        "location" is Synapse ID, S3Uri of the NDA or a user, or LocalPath.
        For data download, synapse or aws clients, or symbolic link will be used, respectively.''')
    return parser.parse_args()

if __name__ == "__main__":
    main()
