from typing import TypedDict


class MasterDataRecord(TypedDict):
    code: str
    name: str
    aliases: list[str]


ACTIVITIES: list[MasterDataRecord] = [
    {
        "code": "BON_PHAN",
        "name": "Bón phân",
        "aliases": [
            "bón phân",
            "rải phân",
            "cho phân",
            "đánh phân",
            "bỏ phân",
        ],
    },
    {
        "code": "PHUN_THUOC",
        "name": "Phun thuốc",
        "aliases": [
            "phun thuốc",
            "xịt thuốc",
            "xịt sâu",
            "phun sâu",
            "phun thuốc sâu",
        ],
    },
    {
        "code": "TUOI_NUOC",
        "name": "Tưới nước",
        "aliases": [
            "tưới",
            "tưới nước",
            "tưới cây",
            "tưới ruộng",
        ],
    },
    {
        "code": "LAM_CO",
        "name": "Làm cỏ",
        "aliases": [
            "làm cỏ",
            "nhổ cỏ",
            "dọn cỏ",
            "phát cỏ",
        ],
    },
    {
        "code": "THU_HOACH",
        "name": "Thu hoạch",
        "aliases": [
            "thu hoạch",
            "hái",
            "hái trái",
            "hái quả",
            "cắt trái",
        ],
    },
]


UNITS: list[MasterDataRecord] = [
    {
        "code": "KG",
        "name": "Kilôgam",
        "aliases": [
            "kg",
            "ký",
            "kí",
            "ki lô",
            "kilô",
            "kilogram",
            "cân",
        ],
    },
    {
        "code": "G",
        "name": "Gam",
        "aliases": [
            "g",
            "gam",
            "gram",
        ],
    },
    {
        "code": "L",
        "name": "Lít",
        "aliases": [
            "l",
            "lít",
            "lit",
        ],
    },
    {
        "code": "ML",
        "name": "Mililít",
        "aliases": [
            "ml",
            "mi li lít",
            "mililít",
        ],
    },
    {
        "code": "BAG",
        "name": "Bao",
        "aliases": [
            "bao",
            "bịch",
            "túi",
        ],
    },
    {
        "code": "BOTTLE",
        "name": "Chai",
        "aliases": [
            "chai",
            "lọ",
        ],
    },
]


# Các từ không được tự động quy đổi vì ý nghĩa phụ thuộc khu vực.
AMBIGUOUS_TERMS: dict[str, str] = {
    "xi": (
        "Đơn vị 'xị' có thể được hiểu khác nhau theo khu vực; "
        "cần người dùng xác nhận số lượng và đơn vị chuẩn."
    ),
    "cong": (
        "Đơn vị diện tích 'công' có thể khác nhau theo khu vực; "
        "cần người dùng xác nhận."
    ),
    "sao": (
        "Đơn vị diện tích 'sào' có giá trị khác nhau giữa các vùng; "
        "cần người dùng xác nhận."
    ),
}