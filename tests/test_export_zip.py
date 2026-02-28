"""
Tests for POST /api/export-zip endpoint.
"""
import zipfile
import io

from fastapi.testclient import TestClient

from web.server import app

client = TestClient(app)


class TestExportZip:
    """Tests for /api/export-zip."""

    def test_basic_zip(self):
        resp = client.post("/api/export-zip", json={
            "files": {
                "dirtyPage.pmd": '{"id": "page1"}',
                "dirtyPod.pod": '{"podId": "pod1"}',
            },
        })
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"

        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        names = sorted(zf.namelist())
        assert names == ["dirtyPage.pmd", "dirtyPod.pod"]
        assert zf.read("dirtyPage.pmd").decode() == '{"id": "page1"}'

    def test_strips_uuid_prefix(self):
        resp = client.post("/api/export-zip", json={
            "files": {
                "abcd1234-5678-90ab-cdef-1234567890ab_dirtyPage.pmd": "content",
            },
        })
        assert resp.status_code == 200
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        assert zf.namelist() == ["dirtyPage.pmd"]

    def test_empty_files_rejected(self):
        resp = client.post("/api/export-zip", json={"files": {}})
        assert resp.status_code == 400
        assert "No files" in resp.json()["detail"]

    def test_missing_files_field(self):
        resp = client.post("/api/export-zip", json={})
        assert resp.status_code == 422

    def test_content_disposition_header(self):
        resp = client.post("/api/export-zip", json={
            "files": {"test.pmd": "{}"},
        })
        assert resp.status_code == 200
        assert "fixed_files.zip" in resp.headers.get("content-disposition", "")

    def test_preserves_file_content_exactly(self):
        content = '{\n  "id": "myPage",\n  "value": "hello\\nworld"\n}'
        resp = client.post("/api/export-zip", json={
            "files": {"test.pmd": content},
        })
        assert resp.status_code == 200
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        assert zf.read("test.pmd").decode() == content
