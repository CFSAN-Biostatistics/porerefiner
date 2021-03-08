from functools import wraps
from pathlib import Path
from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import SampleSheet
from porerefiner.models import create_readable_name

from . import SnifferFor, ParserFor

@SnifferFor.csv
@SnifferFor.xls
def ver_100(rows):
    """porerefiner_ver	1.0.0
library_id	
sequencing_kit	
sample_id	accession	barcode_id	organism	extraction_kit	comment user
TEST	TEST	TEST	TEST	TEST	TEST	TEST"""
    note, ver, *_ = rows[0]
    return 'porerefiner_ver' in note and '1.0.0' in ver

@SnifferFor.csv
@SnifferFor.xls
def ver_100_fda(rows):
    """porerefiner_ver	1.0.0-fda
library_id	
sequencing_kit	
sample_id	accession	barcode_id	organism	extraction_kit	comment user
TEST	TEST	TEST	TEST	TEST	TEST	TEST"""
    note, ver, *_ = rows[0]
    return 'porerefiner_ver' in note and '1.0.0-fda' in ver

@SnifferFor.csv
@SnifferFor.xls
def ver_101(rows):
    """porerefiner_ver	1.0.1
library_id	
sequencing_kit	
barcode_kit	
sample_id	accession	barcode_id	organism	extraction_kit	comment user
TEST	TEST	TEST	TEST	TEST	TEST	TEST"""
    note, ver, *_ = rows[0]
    return 'porerefiner_ver' in note and '1.0.1' in ver

@ParserFor.ver_100
@ParserFor.ver_101
@ParserFor.ver_100_fda
def ver_100(rows):
    "Standard Porerefiner samplesheet parser"
    rows = iter(rows)
    ss = SampleSheet()
    ss.date.GetCurrentTime()
    _, ss.porerefiner_ver, *_ = next(rows)
    _, ss.library_id, *_ = next(rows)
    _, ss.sequencing_kit = next(rows)
    key, value, *rest = next(rows)
    if 'barcode_kit' in key: #if it's not the header
        [ss.barcode_kit.append(barcode) for barcode in [value] + rest]
        next(rows) # skip the header
    for sample_id, accession, barcode_id, organism, extraction_kit, comment, user, *_ in rows:
        ss.samples.add(sample_id=sample_id,
                        accession=accession,
                        barcode_id=barcode_id,
                        organism=organism,
                        extraction_kit=extraction_kit,
                        comment=comment,
                        user=user)
    return ss


@SnifferFor.xls
def cip_microbiome(rows):
    """FORM VALIDATION											
Test for duplicate ids: OK											
SAMPLE_ID length: OK											
SAMPLE_IDs are purely alphanumeric: OK											
WELL	SAMPLE_ID	DESCRIPTION	DNA_CONC	SAMPLE_TYPE	REGION	HOST	METADATA1	METADATA2	METADATA3	SUBMITTER_INITIALS	LAB_SAMPLE_ID
A1	TEST	TEST	TEST	TEST	TEST	TEST	TEST				"""
    return "FORM VALIDATION" in rows[0][0]

@ParserFor.cip_microbiome
def cip_microbiome(rows):
    "Special samplesheet parser for the CIP Microbiome project"
    ss = SampleSheet()
    ss.date.GetCurrentTime()
    ss.porerefiner_ver = "CIP100"
    ss.library_id = create_readable_name()
    key0, key1, key2 = rows[4][7:10] # set the names of metadata1 2 and 3
    for well, sample_id, description, dna_conc, sample_type, region, host, val0, val1, val2, user, accession in rows[5:]:
        if sample_id: #ignore rows with blank sample id
            sample = ss.samples.add(sample_id=sample_id,
                                    accession=accession,
                                    comment=description,
                                    user=user)
            if dna_conc:
                sample.trip_tags.add(namespace='CIP',
                                    name='concentration',
                                    value=str(dna_conc))
            if region:
                sample.trip_tags.add(namespace='CIP',
                                    name='region',
                                    value=str(region))
            if host:
                sample.trip_tags.add(namespace='CIP',
                                    name='host',
                                    value=str(host))
            if val0:
                sample.trip_tags.add(namespace='custom',
                                 name=str(key0),
                                 value=str(val0))
            if val1:
                sample.trip_tags.add(namespace='custom',
                                 name=str(key1),
                                 value=str(val1))
            if val2:
                sample.trip_tags.add(namespace='custom',
                                 name=str(key2),
                                 value=str(val2))