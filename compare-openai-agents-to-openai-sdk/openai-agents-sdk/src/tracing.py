# src/tracing.py
from agents.tracing.processors import BackendSpanExporter, BatchTraceProcessor

from agents import set_trace_processors


def setup_tracing() -> None:
    set_trace_processors([BatchTraceProcessor(BackendSpanExporter())])
