import signal

from worker.signal_handler import SignalHandler


def test_signal_handler_initial_state():
    handler = SignalHandler()
    assert handler.signal_received is False


def test_signal_handler_sets_flag_after_signal():
    handler = SignalHandler()
    handler._handle_signal(int(signal.SIGTERM), None)  # noqa: SLF001
    assert handler.signal_received is True
