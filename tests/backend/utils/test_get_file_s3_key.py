from backend.utils.get_file_s3_key import get_file_s3_key  

def test_get_file_s3_key_multimedia():
    result = get_file_s3_key("test@example.com", "file.mp3")
    assert result == "app_data/user-uploads/test@example.com/file.mp3"


def test_get_file_s3_key_document():
    result = get_file_s3_key("test@example.com", "file.pdf", file_type="document")
    assert result == "app_data/document-uploads/test@example.com/file.pdf"