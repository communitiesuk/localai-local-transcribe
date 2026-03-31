from worker.signal_handler import SignalHandler


def test_signal_handler_initial_state():
    handler = SignalHandler()
    assert handler.signal_received is False

    handler._handle_signal(15, None)  # noqa: SLF001
    assert handler.signal_received is True
