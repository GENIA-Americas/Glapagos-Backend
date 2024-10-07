class DatasetException(Exception):
    ...


class BigQueryException(DatasetException):
    ...


class BigQueryExecutionFailed(BigQueryException):
    ...