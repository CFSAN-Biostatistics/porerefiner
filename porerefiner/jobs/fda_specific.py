from dataclasses import dataclass, field
from porerefiner.jobs import FileJob, RunJob
from typing import List

import json
import os
import subprocess

"""
{
  "porerefiner_ver": "1.0.0",
  "library_id": "TEST_TEST",
  "dna kit": "TEST_DNAKIT",
  "sequencing_kit": "SQK-RBK004",
  "flowcell": "FAK80437",
  "sequencer": "Revolution",
  "relative_location": "FAK80437/FAK80437/20190911_1923_GA10000_FAK80437_bceaf277"
  "run_month": "11",
  "run_year": "2019",
   "notifications": {
    "genome_closure_status": [ "Fred.Garvin@fda.hhs.gov", "Veet.Voojagig@fda.hhs.gov" ],
    "import_ready": [ "Gag.Halfrunt@fda.hhs.gov" ]
    },
  "samples": [
      {
          "sample_id": "TEST01",
          "accession": "ACC_TEST_01",
          "barcode_id": "09",
          "organism": "Pseudomonas aeruginosa",
	  "extraction_kit": "TEST_KIT_KIT",
          "comment": " 44",
          "user": "justin.payne@fda.hhs.gov"
      },
"""


@dataclass
class FdaRunJob(RunJob):
    "Boutique class to handle our own in-house nanopore integration."

    command: str
    closure_status_recipients: List[str] = field(default_factory=list)
    import_ready_recipients: List[str] = field(default_factory=list)


    def setup(self, run, datadir, remotedir):
        samplesh = dict(porerefiner_ver="1.0.0",
                        library_id=run.samplesheet.library_id,
                        dna_kit=None,
                        sequencing_kit=run.samplesheet.sequencing_kit,
                        flowcell=run.flowcell.consumable_id,
                        sequencer=os.environ['HOSTNAME'],
                        relative_location=run.path,
                        run_month=run.started.month,
                        run_year=run.started.year,
                        run_day=run.started.day,
                        notifications=dict(genome_closure_status=self.closure_status_recpients,
                                           import_ready=self.import_ready_recipients),
                        samples=[dict(sample_id=sample.sample_id,
                                      accession=sample.accession,
                                      barcode_id=sample.barcode_id,
                                      organism=sample.organism,
                                      extraction_kit=sample.extraction_kit,
                                      comment=sample.comment,
                                      user=sample.user) for sample in run.samples])
        with open(datadir / "samplesheet.json", 'w') as ss_json:
            json.dump(samplesh, ss_json)
        return command.format(**locals), {}

    def collect(self, run, path, pid):
        pass
