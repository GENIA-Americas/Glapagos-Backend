import csv
from typing import Dict


def csv_parameters_detect(sample: str) -> Dict:
    sniffer = csv.Sniffer()

    dialect = sniffer.sniff(sample)

    has_header = sniffer.has_header(sample)

    return {
        'delimiter': dialect.delimiter,
        'quotechar': dialect.quotechar,
        'escapechar': dialect.escapechar,
        'doublequote': dialect.doublequote,
        'skipinitialspace': dialect.skipinitialspace,
        'lineterminator': dialect.lineterminator,
        'quoting': dialect.quoting,
        'has_header': has_header
    }
