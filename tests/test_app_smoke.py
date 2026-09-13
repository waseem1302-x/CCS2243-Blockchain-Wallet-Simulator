from streamlit.testing.v1 import AppTest


def test_streamlit_app_starts_without_uncaught_exception():
    app = AppTest.from_file("app.py")
    app.run(timeout=15)
    assert not app.exception
