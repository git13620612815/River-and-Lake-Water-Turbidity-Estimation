import io
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

import numpy as np

from ml.estimator import estimate
from ml.preprocess import preprocess_for_infer
from ml.visual import predict_visual

TEMP_MEDIA = tempfile.mkdtemp(prefix="water-media-")


def png_file(name="water.png", size=(64, 40)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (20, 120, 180)).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class WaterApiTests(TestCase):
    def setUp(self):
        Path(TEMP_MEDIA).mkdir(parents=True, exist_ok=True)
        call_command("init_rbac")
        self.client = APIClient()

    def login(self, code="mock:dev-user"):
        response = self.client.post("/api/auth/wechat/", {"code": code}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["data"]["access"])
        return response.data["data"]

    def login_admin(self):
        response = self.client.post(
            "/api/admin/auth/login/",
            {"username": "admin", "password": "admin123456"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["data"]["access"])
        return response.data["data"]

    def test_estimate_matches_document_example(self):
        result = estimate({"clear": 0.08, "slight": 0.71, "moderate": 0.18, "severe": 0.03})
        self.assertEqual(result["label"], "slight")
        self.assertEqual(result["ntu"], 56.2)
        self.assertEqual(result["ntu_min"], 10)
        self.assertEqual(result["ntu_max"], 50)
        self.assertIn("邻近", result["note"])

    def test_visual_model_orders_water_colors(self):
        samples = {
            "clear": (30, 110, 190),
            "slight": (176, 184, 186),
            "moderate": (176, 140, 60),
            "severe": (96, 64, 32),
        }
        labels = []
        for name, color in samples.items():
            path = Path(TEMP_MEDIA) / f"{name}.png"
            image = np.zeros((80, 80, 3), dtype=np.uint8)
            image[:, :] = color
            Image.fromarray(image, "RGB").save(path)
            labels.append(predict_visual(str(path))["label"])
        self.assertEqual(labels, ["clear", "slight", "moderate", "severe"])

    def test_preprocess_output_shape(self):
        path = Path(TEMP_MEDIA) / "sample.png"
        Image.new("RGB", (300, 120), (8, 90, 140)).save(path)
        tensor = preprocess_for_infer(str(path))
        self.assertEqual(tuple(tensor.shape), (3, 224, 224))

    def test_health_and_repeat_login(self):
        health = APIClient().get("/api/health/")
        self.assertEqual(health.data["data"]["status"], "ok")
        first = APIClient().post("/api/auth/wechat/", {"code": "mock:dev-user"}, format="json")
        second = APIClient().post("/api/auth/wechat/", {"code": "mock:dev-user"}, format="json")
        self.assertEqual(first.data["data"]["user"]["id"], second.data["data"]["user"]["id"])
        bad = APIClient().post("/api/auth/wechat/", {"code": "abc"}, format="json")
        self.assertEqual(bad.status_code, 400)

    def test_disabled_user_cannot_login(self):
        self.login("mock:dev-user")
        self.login_admin()
        listed = self.client.get("/api/admin/users/", {"nickname": "微信用户"})
        user_id = listed.data["data"]["results"][0]["id"]
        changed = self.client.patch(f"/api/admin/users/{user_id}/", {"is_active": False}, format="json")
        self.assertEqual(changed.status_code, 200)
        denied = APIClient().post("/api/auth/wechat/", {"code": "mock:dev-user"}, format="json")
        self.assertEqual(denied.status_code, 403)

    def test_user_cannot_manage_and_admin_can(self):
        self.login("mock:dev-user")
        denied = self.client.get("/api/admin/users/")
        self.assertEqual(denied.status_code, 403)
        self.login_admin()
        allowed = self.client.get("/api/admin/users/")
        self.assertEqual(allowed.status_code, 200)
        self.assertGreaterEqual(allowed.data["data"]["count"], 1)

    def test_remove_detect_permission_and_keep_builtin_role(self):
        self.login_admin()
        roles = self.client.get("/api/admin/roles/").data["data"]
        user_role = next(item for item in roles if item["code"] == "user")
        admin_role = next(item for item in roles if item["code"] == "admin")
        kept = [item["id"] for item in user_role["permissions"] if item["code"] != "detect.create"]
        updated = self.client.patch(
            f"/api/admin/roles/{user_role['id']}/",
            {"name": "普通用户", "permission_ids": kept},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        removed = self.client.delete(f"/api/admin/roles/{admin_role['id']}/")
        self.assertEqual(removed.status_code, 400)
        self.login("mock:someone")
        blocked = self.client.post("/api/detections/batches/", {"total": 1}, format="json")
        self.assertEqual(blocked.status_code, 403)

    def test_profile_validation(self):
        self.login()
        phone = self.client.patch("/api/users/me/", {"phone": "123"}, format="json")
        nickname = self.client.patch("/api/users/me/", {"nickname": "  "}, format="json")
        self.assertEqual(phone.status_code, 400)
        self.assertEqual(nickname.status_code, 400)
        saved = self.client.patch("/api/users/me/", {"nickname": "河湖采样", "phone": "13800138000"}, format="json")
        self.assertEqual(saved.data["data"]["nickname"], "河湖采样")

    @override_settings(MODEL_WEIGHTS=str(Path(TEMP_MEDIA) / "missing.pt"))
    def test_single_image_without_weights_and_corrupt_file(self):
        self.login()
        created = self.client.post("/api/detections/batches/", {"total": 1}, format="json").data["data"]
        uploaded = self.client.post(
            f"/api/detections/batches/{created['id']}/images/",
            {"file": png_file()},
            format="multipart",
        )
        self.assertEqual(uploaded.data["data"]["status"], "pending")
        started = self.client.post(f"/api/detections/batches/{created['id']}/start/", format="json")
        record = started.data["data"]["records"][0]
        self.assertEqual(record["status"], "success")
        self.assertEqual(record["label"], "clear")
        self.assertIn("图像特征模型", record["note"])

        created = self.client.post("/api/detections/batches/", {"total": 1}, format="json").data["data"]
        bad = SimpleUploadedFile("bad.jpg", b"not-an-image", content_type="image/jpeg")
        failed = self.client.post(
            f"/api/detections/batches/{created['id']}/images/",
            {"file": bad},
            format="multipart",
        )
        self.assertEqual(failed.data["data"]["status"], "failed")
        self.assertEqual(failed.data["data"]["error_message"], "解码失败")
        started = self.client.post(f"/api/detections/batches/{created['id']}/start/", format="json")
        self.assertEqual(started.data["data"]["status"], "finished")

    def test_start_rejected_when_upload_incomplete(self):
        self.login()
        created = self.client.post("/api/detections/batches/", {"total": 2}, format="json").data["data"]
        self.client.post(
            f"/api/detections/batches/{created['id']}/images/",
            {"file": png_file()},
            format="multipart",
        )
        started = self.client.post(f"/api/detections/batches/{created['id']}/start/", format="json")
        self.assertEqual(started.status_code, 400)

    def test_records_are_private(self):
        self.login("mock:alice")
        created = self.client.post("/api/detections/batches/", {"total": 1}, format="json").data["data"]
        bad = SimpleUploadedFile("bad.jpg", b"not-an-image", content_type="image/jpeg")
        record = self.client.post(
            f"/api/detections/batches/{created['id']}/images/",
            {"file": bad},
            format="multipart",
        ).data["data"]
        self.login("mock:bob")
        listed = self.client.get("/api/detections/records/")
        self.assertEqual(listed.data["data"]["count"], 0)
        hidden = self.client.get(f"/api/detections/records/{record['id']}/")
        self.assertEqual(hidden.status_code, 404)

    def test_dataset_stats_and_user_cannot_upload(self):
        self.login("mock:dev-user")
        denied = self.client.post(
            "/api/admin/datasets/",
            {"label": "clear", "file": png_file()},
            format="multipart",
        )
        self.assertEqual(denied.status_code, 403)
        self.login_admin()
        created = self.client.post(
            "/api/admin/datasets/",
            {"label": "clear", "note": "晴天水面", "file": png_file("lake.png")},
            format="multipart",
        )
        self.assertEqual(created.status_code, 200)
        stats = self.client.get("/api/admin/datasets/stats/").data["data"]
        self.assertEqual(stats["clear"], 1)
        self.assertEqual(stats["slight"], 0)

    def test_register_then_login_with_password(self):
        created = APIClient().post(
            "/api/auth/register/",
            {"username": "river01", "password": "pass1234", "nickname": "采样员"},
            format="json",
        )
        self.assertEqual(created.status_code, 200, created.content)
        self.assertEqual(created.data["data"]["user"]["nickname"], "采样员")
        self.assertEqual(created.data["data"]["user"]["role"]["code"], "user")
        duplicate = APIClient().post(
            "/api/auth/register/",
            {"username": "river01", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        wrong = APIClient().post(
            "/api/auth/login/",
            {"username": "river01", "password": "bad-pass"},
            format="json",
        )
        self.assertEqual(wrong.status_code, 400)
        logged = APIClient().post(
            "/api/auth/login/",
            {"username": "river01", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(logged.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + logged.data["data"]["access"])
        denied = self.client.get("/api/admin/users/")
        self.assertEqual(denied.status_code, 403)

    def test_mock_login_cannot_enter_admin(self):
        data = self.login("mock:dev-admin")
        self.assertNotIn("user.manage", data["user"]["permissions"])
        denied = self.client.get("/api/admin/dashboard/")
        self.assertEqual(denied.status_code, 403)
        wrong = APIClient().post(
            "/api/admin/auth/login/",
            {"username": "admin", "password": "wrong-pass"},
            format="json",
        )
        self.assertEqual(wrong.status_code, 400)

    def test_admin_views_all_records_but_cannot_delete_others(self):
        entered = self.login("mock:alice")
        created = self.client.post("/api/detections/batches/", {"total": 1}, format="json").data["data"]
        bad = SimpleUploadedFile("bad.jpg", b"not-an-image", content_type="image/jpeg")
        record = self.client.post(
            f"/api/detections/batches/{created['id']}/images/",
            {"file": bad},
            format="multipart",
        ).data["data"]
        self.login_admin()
        listed = self.client.get("/api/detections/records/", {"user_id": entered["user"]["id"]})
        self.assertEqual(listed.data["data"]["count"], 1)
        removed = self.client.delete(f"/api/detections/records/{record['id']}/")
        self.assertEqual(removed.status_code, 403)

    def test_dashboard_shape(self):
        self.login_admin()
        data = self.client.get("/api/admin/dashboard/").data["data"]
        self.assertIn("user_count", data)
        self.assertEqual(len(data["daily_counts"]), 7)
        self.assertIn("clear", data["level_counts"])
        self.assertIn("model_ready", data)
