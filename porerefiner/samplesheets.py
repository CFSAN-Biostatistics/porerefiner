from porerefiner.protocols.porerefiner.rpc.porerefiner_pb2 import SampleSheet

import csv
from io import TextIOWrapper

# We should do sample sheet parsing on the client side

def load_from_csv(file, delimiter=b',') -> SampleSheet:
    ss = SampleSheet()
    _, ss.porerefiner_ver, *_ = file.readline().strip().split(delimiter)
    ss.date.GetCurrentTime()
    if ss.porerefiner_ver == '1.0.0':
        _, ss.library_id, *_ = file.readline().strip().split(delimiter)
        _, ss.sequencing_kit, *_ = file.readline().strip().split(delimiter)
        delimiter = delimiter.decode()
        [ss.samples.add(**row) for row in csv.DictReader(TextIOWrapper(file), delimiter=delimiter, dialect='excel')] #this should handle commas in fields
    elif ss.porerefiner_ver == '1.0.0-fda':
        _, ss.library_id, *_ = file.readline().strip().split(delimiter)
        _, ss.sequencing_kit, *_ = file.readline().strip().split(delimiter)
        delimiter = delimiter.decode()
        file.readline() #ditch the header
        for sample_id, accession, barcode_id, organism, extraction_kit, comment, user, *_ in csv.reader(TextIOWrapper(file), delimiter=delimiter, dialect='excel'):
            ss.samples.add(sample_id=sample_id,
                           accession=accession,
                           barcode_id=barcode_id,
                           organism=organism,
                           extraction_kit=extraction_kit,
                           comment=comment,
                           user=user)
    elif ss.porerefiner_ver == '1.0.1':
        _, ss.library_id, *_ = file.readline().strip().split(delimiter)
        _, ss.sequencing_kit, *_ = file.readline().strip().split(delimiter)
        # _, ss.barcode_kit, *_ = file.readline().split(delimiter) #TODO
        # barcode kit takes multiple values
        _, *barcodes = file.readline().strip().split(delimiter)
        [ss.barcode_kit.append(barcode) for barcode in barcodes if barcode]
        delimiter = delimiter.decode()
        file.readline() # ditch the header
        for sample_id, accession, barcode_id, organism, extraction_kit, comment, user, *_ in csv.reader(TextIOWrapper(file), delimiter=delimiter, dialect='excel'):
            ss.samples.add(sample_id=sample_id,
                           accession=accession,
                           barcode_id=barcode_id,
                           organism=organism,
                           extraction_kit=extraction_kit,
                           comment=comment,
                           user=user)
    else:
        raise ValueError(f"Sample sheet of version {ss.porerefiner_ver} not supported.")
    return ss

def load_from_excel(file) -> SampleSheet:
    import openpyxl
    ss = SampleSheet()
    book = openpyxl.load_workbook(file)
    rows = (tuple(c.value for c in row) for row in book.worksheets[0].iter_rows())
    _, ss.porerefiner_ver, *_ = next(rows)
    if ss.porerefiner_ver == '1.0.0' or ss.porerefiner_ver == '1.0.0-fda':
        ss.date.GetCurrentTime()
        _, ss.library_id, *_ = next(rows)
        _, ss.sequencing_kit, *_ = next(rows)
        next(rows) # ditch the header
        for sample_id, accession, barcode_id, organism, extraction_kit, comment, user, *_ in rows:
            ss.samples.add(sample_id=sample_id,
                           accession=accession,
                           barcode_id=str(barcode_id),
                           organism=organism,
                           extraction_kit=extraction_kit,
                           comment=comment,
                           user=user)
    elif ss.porerefiner_ver == '1.0.1':
        ss.date.GetCurrentTime()
        _, ss.library_id, *_ = next(rows)
        _, ss.sequencing_kit, *_ = next(rows)
        _, ss.barcode_kit, *_ = next(rows)
        next(rows) # ditch the header
        for sample_id, accession, barcode_id, organism, extraction_kit, comment, user, *_ in rows:
            ss.samples.add(sample_id=sample_id,
                           accession=accession,
                           barcode_id=str(barcode_id),
                           organism=organism,
                           extraction_kit=extraction_kit,
                           comment=comment,
                           user=user)

    else:
        raise ValueError(f"Sample sheet of version {ss.porerefiner_ver} not supported.")

    return ss