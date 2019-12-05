from porerefiner.jobs import RunJob
from dataclasses import dataclass

@dataclass
class GuppyJob(RunJob):

    num_cores: int = 8
    preamble: str = "module load guppy/3.4.1"

    # def __init__(self, num_cores):
    #     self.num_cores = num_cores

    def setup(self, run, datadir, remotedir):
        return f"""{self.preamble};
                    guppy_barcoder -t {self.num_cores}
                    --verbose_logs
                    --compress_fastq
                    -i {remotedir}
                    -s {remotedir}/output
                    --trim_barcodes""", {"NUM_THREADS":self.num_cores} #execution hints

    def collect(self, run, datadir, pid):
        pass
