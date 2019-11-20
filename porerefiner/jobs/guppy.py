from porerefiner.jobs import RunJob


class GuppyJob(RunJob):

    def __init__(self, num_cores):
        self.num_cores = num_cores

    def setup(self, run, datadir, remotedir):
        return f"""guppy_barcoder -t {self.num_cores}
                    --verbose_logs
                    --compress_fastq
                    -i {remotedir}
                    -s {remotedir}/output
                    --trim_barcodes""", {"NUM_THREADS":self.num_cores}

    def collect(self, run, datadir, pid):
        pass
