"Tests for sample sheet parsing and attachment."

from pathlib import Path

from pytest import mark, raises

from tests import db  # noqa: F401  (fixture)

from porerefiner import models
from porerefiner.samplesheets import load_from_csv


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_parse_sample_sheet_with_samples():
    with open(REPO_ROOT / "SampleSheetSample.csv") as f:
        ss = load_from_csv(f)
    assert len(ss.samples) == 3
    assert ss.samples[0].sample_id == "CFSAN000123"
    # comma-in-quoted-field must survive
    assert ss.samples[0].comment == "a comment, with a comma in it"


def test_parse_empty_sample_sheet():
    with open(REPO_ROOT / "SampleSheet.csv") as f:
        ss = load_from_csv(f)
    assert len(ss.samples) == 0


def test_parse_unknown_format_raises():
    import io
    with raises(ValueError):
        load_from_csv(io.StringIO("not,a,known,header\nfoo,bar,baz,qux\n"))


def test_new_sheet_from_message_uses_correct_kit_field(db):
    "Regression: barcoding_kit was mistakenly filled from sequencing_kit."
    with open(REPO_ROOT / "SampleSheetSample.csv") as f:
        msg = load_from_csv(f)
    run = models.Run.create(name="TEST", path="/dev/null")
    ss = models.SampleSheet.new_sheet_from_message(msg, run)
    assert ss.sequencing_kit == msg.sequencing_kit
    assert len(ss.samples) == 3


@mark.asyncio
async def test_attach_samplesheet_to_run(db):
    "Regression: attach_samplesheet_to_run called nonexistent SampleSheet.from_csv."
    from porerefiner import fsevents
    run = models.Run.create(name="TEST", path="/dev/null", status="RUNNING")
    ss = await fsevents.attach_samplesheet_to_run(
        str(REPO_ROOT / "SampleSheetSample.csv"), run_id=run.id
    )
    run = models.Run.get_by_id(run.id)
    assert run.sample_sheet == ss
    assert len(ss.samples) == 3


def test_barcode_kit_barcodes_known_kit(db):
    ss = models.SampleSheet.create(barcoding_kit="EXP-NBD104")
    table = ss.barcode_kit_barcodes
    assert table["NB01"] == "AAGAAAGTTGTCGGTGTCTTTGTG"
    assert len(table) == 12


def test_barcode_kit_barcodes_unknown_kit(db):
    ss = models.SampleSheet.create(barcoding_kit="NOT-A-REAL-KIT")
    assert ss.barcode_kit_barcodes == {}


def test_make_run_msg_with_samples(db):
    "Regression: make_run_msg referenced nonexistent sample.pk."
    from porerefiner import rpc
    with open(REPO_ROOT / "SampleSheetSample.csv") as f:
        msg = load_from_csv(f)
    run = models.Run.create(name="TEST", path="/dev/null")
    models.SampleSheet.new_sheet_from_message(msg, run)
    run = models.Run.get_by_id(run.id)
    out = rpc.make_run_msg(run)
    assert len(out.samples) == 3
    assert out.samples[0].id


def test_sample_barcode_seq_resolves(db):
    ss = models.SampleSheet.create(barcoding_kit="EXP-NBD104")
    sample = models.Sample.create(samplesheet=ss, sample_id="s1", barcode_id="NB01")
    assert sample.barcode_seq == "AAGAAAGTTGTCGGTGTCTTTGTG"
    unknown = models.Sample.create(samplesheet=ss, sample_id="s2", barcode_id="ZZ99")
    assert unknown.barcode_seq == ""
