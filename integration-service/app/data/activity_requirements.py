from typing import Literal, TypedDict


RULE_CATALOG_VERSION = "2026.09-review-v1"


RuleStatus = Literal[
    "review_confirmed",
    "provisional",
    "pending_approval",
]


class ActivityRequirement(TypedDict):
    activity_code: str
    materials_required: bool | None
    rule_status: RuleStatus
    note: str


# Canonical Activity Requirement Matrix.
#
# IMPORTANT:
# - Chỉ rule có căn cứ rõ mới được enforce như ERROR.
# - None = chưa được doanh nghiệp/giảng viên chốt; backend không tự suy đoán.
# - Không chứa min/max quantity vì review yêu cầu không hard-code ngưỡng
#   khi chưa có dữ liệu/rule nghiệp vụ được xác nhận.
ACTIVITY_REQUIREMENTS: dict[str, ActivityRequirement] = {
    "BON_PHAN": {
        "activity_code": "BON_PHAN",
        "materials_required": True,
        "rule_status": "review_confirmed",
        "note": (
            "Review v2 xác định record Bón phân thiếu vật tư "
            "không được coi là valid."
        ),
    },
    "PHUN_THUOC": {
        "activity_code": "PHUN_THUOC",
        "materials_required": None,
        "rule_status": "pending_approval",
        "note": (
            "Review v2 chỉ ra rule hiện đang mâu thuẫn giữa prompt/"
            "confidence/backend; chưa tự chốt rule thay doanh nghiệp."
        ),
    },
    "TUOI_NUOC": {
        "activity_code": "TUOI_NUOC",
        "materials_required": False,
        "rule_status": "provisional",
        "note": (
            "Giữ tương thích flow/test hiện tại: tưới nước có thể "
            "không có materials. Cần nghiệp vụ duyệt trước production."
        ),
    },
    "LAM_CO": {
        "activity_code": "LAM_CO",
        "materials_required": None,
        "rule_status": "pending_approval",
        "note": "Chưa có rule nghiệp vụ được duyệt trong tài liệu review.",
    },
    "THU_HOACH": {
        "activity_code": "THU_HOACH",
        "materials_required": None,
        "rule_status": "pending_approval",
        "note": "Chưa có rule nghiệp vụ được duyệt trong tài liệu review.",
    },
    "CHO_BO_AN": {
        "activity_code": "CHO_BO_AN",
        "materials_required": None,
        "rule_status": "pending_approval",
        "note": "Chưa có rule nghiệp vụ được duyệt trong tài liệu review.",
    },
}


def get_activity_requirement(
    activity_code: str,
) -> ActivityRequirement | None:
    return ACTIVITY_REQUIREMENTS.get(
        str(activity_code or "")
        .strip()
        .upper()
    )
