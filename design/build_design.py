from html import escape
from pathlib import Path
import json
import zipfile


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "说车三岁-界面设计"
OUT.mkdir(exist_ok=True)

COLORS = {
    "ink": "#202235",
    "body": "#55596F",
    "muted": "#8A8DA1",
    "faint": "#B2B4C4",
    "purple": "#6554E8",
    "purple_dark": "#5142CE",
    "lavender": "#F0EDFF",
    "line": "#EAEAF2",
    "page": "#F7F7FB",
    "field": "#F7F7FC",
    "white": "#FFFFFF",
}
FONT = "'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif"


def attrs(**values):
    return " ".join(
        f'{name.replace("_", "-")}="{escape(str(value), quote=True)}"'
        for name, value in values.items()
        if value is not None
    )


def rect(x, y, width, height, fill, radius=0, stroke=None, **values):
    return f'<rect {attrs(x=x, y=y, width=width, height=height, rx=radius, fill=fill, stroke=stroke, **values)}/>'


def circle(x, y, radius, fill, **values):
    return f'<circle {attrs(cx=x, cy=y, r=radius, fill=fill, **values)}/>'


def path(data, stroke=None, fill="none", **values):
    return f'<path {attrs(d=data, stroke=stroke, fill=fill, **values)}/>'


def line(x1, y1, x2, y2, stroke, width=1, **values):
    return f'<line {attrs(x1=x1, y1=y1, x2=x2, y2=y2, stroke=stroke, stroke_width=width, **values)}/>'


def text(x, y, value, size=14, color=None, weight=400, anchor="start", **values):
    return f'<text {attrs(x=x, y=y, fill=color or COLORS["ink"], font_family=FONT, font_size=size, font_weight=weight, text_anchor=anchor, **values)}>{escape(value)}</text>'


def group(identifier, content, name=None, **values):
    return f'<g {attrs(id=identifier, data_name=name, **values)}>{"".join(content) if isinstance(content, list) else content}</g>'


def icon(name, x, y, size=20, color=None, stroke_width=1.7):
    color = color or COLORS["purple"]
    shapes = {
        "plus": '<path d="M12 5v14M5 12h14"/>',
        "chevron": '<path d="m9 5 7 7-7 7"/>',
        "back": '<path d="m15 5-7 7 7 7"/>',
        "arrow": '<path d="M4 12h15m-6-6 6 6-6 6"/>',
        "camera": '<path d="M4 6h4l2-3h4l2 3h4a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Z"/><circle cx="12" cy="13" r="4"/><path d="M18 9h1"/>',
        "gallery": '<rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 6-6 4 4 3-3 5 5"/>',
        "grid": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
        "person": '<circle cx="12" cy="7.5" r="4"/><path d="M4 21v-3a8 8 0 0 1 16 0v3"/>',
        "sparkles": '<path d="m12 3 2.3 6.7L21 12l-6.7 2.3L12 21l-2.3-6.7L3 12l6.7-2.3Z"/><path d="M20 2v4m-2-2h4"/>',
        "check": '<path d="m5 12 4 4L19 6"/>',
        "mic": '<rect x="8" y="2" width="8" height="13" rx="4"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3m-4 0h8"/>',
        "note": '<path d="M6 3h9l4 4v14H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm8 0v5h5M8 12h7m-7 4h5"/>',
        "video": '<rect x="2" y="5" width="14" height="14" rx="4"/><path d="m16 10 6-4v12l-6-4"/>',
        "phone": '<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 18h4"/>',
        "landscape": '<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M18 10v4"/>',
        "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.2"/>',
        "folder": '<path d="M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    }
    return f'<g {attrs(transform=f"translate({x} {y}) scale({size / 24})", fill="none", stroke=color, stroke_width=stroke_width, stroke_linecap="round", stroke_linejoin="round")}>{shapes[name]}</g>'


def car_icon(kind, x, y, width=54, color=None):
    color = color or "#AAA5C3"
    fill = "#EEECF6"
    pieces = []
    if kind == "front45":
        pieces = [
            path("M7 26 15 19 28 15 44 16 57 23 60 32 55 38 9 36 5 32Z", color, fill),
            path("m17 20 7-10 17 1 10 10M26 12l-1 8m-8 0 26 2 8-1M6 27l23 4 28-4m-28 4v6", color),
            path("m10 25 9 2m23-1 10-2m-36 8 7 1m13 0 12-2", color),
            circle(14, 36, 4, "#FFFFFF", stroke=color),
            circle(50, 36, 4, "#FFFFFF", stroke=color),
        ]
    elif kind in ("front", "rear"):
        pieces = [
            path("m14 22 5-11h26l5 11 5 5v12H9V27Z", color, fill),
            path("m18 21 3-7h22l3 7Zm-7 5H7m43 0h7M15 38v4m34-4v4", color),
            path("M15 29h9m16 0h9M25 34h14" if kind == "front" else "M14 28h36M25 34h14", color),
        ]
    elif kind in ("side", "side_right"):
        pieces = [
            path("m5 29 6-6 9-3 8-10h16l9 13 7 5v10H5Z", color, fill),
            path("m23 21 7-8h11l6 9Zm12-8v9m0 2v10m6-8h4M8 29h8m38 1h5", color),
            circle(18, 37, 5, "#FFFFFF", stroke=color),
            circle(49, 37, 5, "#FFFFFF", stroke=color),
        ]
    elif kind == "interior":
        pieces = [
            path("M6 36V17l7-7h38l7 7v19M8 20h48M31 22v15", color, fill),
            circle(19, 28, 8, "#F9F8FD", stroke=color),
            path("M11 28h16m-8 0v8M37 24h14v9H37Z", color),
            path("M34 40h19M14 13h36", color),
        ]
    elif kind == "seats":
        pieces = [
            rect(12, 7, 13, 10, fill, 4, color),
            rect(38, 7, 13, 10, fill, 4, color),
            path("M11 20h15l3 19H8Zm26 0h15l3 19H34ZM9 31h18m8 0h18M8 42h21m5 0h21", color, fill),
        ]
    elif kind == "rear_seats":
        pieces = [
            rect(9, 8, 12, 9, fill, 3, color),
            rect(27, 8, 10, 9, fill, 3, color),
            rect(43, 8, 12, 9, fill, 3, color),
            path("M8 20h48l3 17H5Zm-3 17v6h54v-6M23 20v17m18-17v17", color, fill),
        ]
    else:
        pieces = [
            circle(30, 25, 17, fill, stroke=color),
            circle(30, 25, 6, "#FFFFFF", stroke=color),
            path("m30 8 0 11m0 12v11M13 25h11m12 0h11M18 13l8 8m8 8 8 8m0-24-8 8m-8 8-8 8", color),
            path("m52 6 1.8 5.2L59 13l-5.2 1.8L52 20l-1.8-5.2L45 13l5.2-1.8Z", color, "#FFFFFF"),
        ]
    return f'<g {attrs(transform=f"translate({x} {y}) scale({width / 64})", stroke_width=1.6, stroke_linecap="round", stroke_linejoin="round")}>{"".join(pieces)}</g>'


def pill(x, y, width, label, fill=None, color=None, size=10, height=22):
    return rect(x, y, width, height, fill or COLORS["lavender"], height / 2) + text(x + width / 2, y + height / 2 + size * 0.36, label, size, color or COLORS["purple"], 500, "middle")


def button(identifier, x, y, width, height, label, primary=False, leading=None, trailing=None):
    color = COLORS["white"] if primary else COLORS["purple"]
    content = [rect(x, y, width, height, COLORS["purple"] if primary else COLORS["white"], 14, None if primary else "#DDD8F8")]
    text_x = x + width / 2
    if leading:
        content.append(icon(leading, x + 16, y + (height - 19) / 2, 19, color))
        text_x += 10
    if trailing:
        content.append(icon(trailing, x + width - 34, y + (height - 18) / 2, 18, color))
        text_x -= 11
    content.append(text(text_x, y + height / 2 + 5, label, 14, color, 600, "middle"))
    return group(identifier, content, label, data_role="button")


def status_bar():
    return group("System_StatusBar", [
        text(27, 27, "9:41", 14, COLORS["ink"], 600),
        rect(294, 20, 3, 5, COLORS["ink"], 1),
        rect(299, 17, 3, 8, COLORS["ink"], 1),
        rect(304, 14, 3, 11, COLORS["ink"], 1),
        rect(309, 11, 3, 14, COLORS["ink"], 1),
        path("M321 16a10 10 0 0 1 14 0m-11 3a6 6 0 0 1 8 0m-5 3a2 2 0 0 1 2 0", COLORS["ink"], stroke_width=1.8, stroke_linecap="round"),
        rect(343, 13, 23, 12, "none", 3, COLORS["ink"], stroke_width=1.1),
        rect(345.5, 15.5, 18, 7, COLORS["ink"], 1.3),
        rect(367.5, 16.5, 2, 5, COLORS["ink"], 1),
    ], "系统状态栏")


def capsule():
    return group("System_WeChatCapsule", [
        rect(282, 48, 88, 31, "#FFFFFF", 16, "#E6E5ED"),
        circle(298, 63.5, 1.8, COLORS["ink"]),
        circle(306, 63.5, 2.2, COLORS["ink"]),
        circle(314, 63.5, 1.8, COLORS["ink"]),
        line(327, 55, 327, 72, "#E6E5ED"),
        circle(348, 63.5, 7, "none", stroke=COLORS["ink"], stroke_width=1.6),
        circle(348, 63.5, 2.7, COLORS["ink"]),
    ], "微信胶囊")


def navbar(title=None):
    content = []
    if title:
        content.extend([
            group("Button_Back", icon("back", 19, 53, 22, COLORS["ink"]), "返回", data_role="button"),
            text(51, 70, title, 17, weight=600),
        ])
    else:
        content.extend([
            group("Brand_Logo", [
                rect(20, 50, 28, 28, COLORS["purple"], 9),
                path("M27 60h14v9H31l-4 3Z", "#FFFFFF", stroke_width=1.5, stroke_linejoin="round"),
                path("m29.5 64 2-2h5l2 2m-9 2h9", "#FFFFFF", stroke_width=1.2, stroke_linecap="round"),
            ], "说车三岁标识"),
            text(57, 70, "说车三岁", 18, weight=600),
        ])
    content.append(capsule())
    return group("NavigationBar", content, "顶部导航")


def footer(left, right, hint="信息先保存，视频稍后生成"):
    return group("BottomActionBar", [
        rect(0, 742, 390, 102, "#FFFFFF"),
        line(0, 742, 390, 742, COLORS["line"]),
        left,
        right,
        text(195, 823, hint, 10, COLORS["muted"], anchor="middle"),
        rect(129, 836, 132, 4, COLORS["ink"], 2),
    ], "底部操作区")


def card(identifier, y, height, contents, name):
    return group(identifier, [rect(20, y + 2, 350, height, "#EEEEF6", 20), rect(20, y, 350, height, "#FFFFFF", 20)] + contents, name)


def section_title(number, title, y, right=None):
    content = [
        rect(36, y - 15, 23, 23, COLORS["lavender"], 8),
        text(47.5, y + 1, number, 10.5, COLORS["purple"], 600, "middle"),
        text(68, y + 2, title, 15, weight=600),
    ]
    if right:
        content.append(text(353, y + 1, right, 10.5, COLORS["muted"], anchor="end"))
    return group(f"Heading_Section{number}", content, title)


PHOTO_SLOTS = [
    ("01", "左前 45°", "front45", "Front45"),
    ("02", "正前方", "front", "Front"),
    ("03", "右后 45°", "rear", "Rear45"),
    ("04", "左侧车身", "side", "LeftSide"),
    ("05", "右侧车身", "side_right", "RightSide"),
    ("06", "中控内饰", "interior", "Dashboard"),
    ("07", "前排座椅", "seats", "FrontSeats"),
    ("08", "后排空间", "rear_seats", "RearSeats"),
    ("09", "亮点细节", "detail", "Details"),
]


def photo_slot(index, label, kind, suffix, x, y, compact=False):
    width, height = (100, 68) if compact else (110, 118)
    is_first = index == "01"
    color = COLORS["purple"] if is_first else "#A29CB9"
    content = [
        rect(x, y, width, height, "#F3F0FF" if is_first else "#FAFAFD", 12 if compact else 16, "#D9D1FC" if is_first else "#EAE8F2"),
    ]
    if compact:
        content.extend([
            car_icon(kind, x + 27, y + 10, 45, color),
            icon("plus", x + 82, y + 7, 11, color, 1.8),
            text(x + 50, y + 58, label, 10.5, COLORS["purple"] if is_first else COLORS["body"], 500, "middle"),
        ])
    else:
        content.extend([
            text(x + 11, y + 20, index, 10, color, 500),
            icon("plus", x + 86, y + 9, 15, color, 1.7),
            car_icon(kind, x + 21, y + 33, 68, color),
            line(x + 12, y + 87, x + 98, y + 87, "#E8E3F6" if is_first else COLORS["line"]),
            text(x + 55, y + 106, label, 11.5, COLORS["purple"] if is_first else COLORS["body"], 500, "middle"),
        ])
    return group(f"Button_UploadVehicle_{index}_{suffix}", content, f"上传车辆照片 {index} {label}", data_role="button", data_slot=index)


def svg_document(identifier, title, description, contents):
    return '\n'.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" {attrs(width=390, height=844, viewBox="0 0 390 844", fill="none", id=identifier, role="img", aria_label=title)}>',
        f'<title>{escape(title)}</title>',
        f'<desc>{escape(description)}</desc>',
        '<defs><linearGradient id="HeaderTint" x1="0" y1="0" x2="390" y2="185" gradientUnits="userSpaceOnUse"><stop stop-color="#EEEBFF"/><stop offset="0.6" stop-color="#F6F5FC"/><stop offset="1" stop-color="#F7F7FB"/></linearGradient></defs>',
        group("Background", [rect(0, 0, 390, 844, COLORS["page"]), rect(0, 0, 390, 185, "url(#HeaderTint)")], "页面背景"),
        *contents,
        '</svg>',
    ])


def home_screen():
    sales = card("Section_01_SalesProfile", 153, 137, [
        section_title("01", "销售形象", 181, "必填 · 用于视频出镜"),
        group("Button_UploadSalesPhoto", [
            rect(36, 197, 76, 76, "#F3F0FE", 15, "#DFD8FA", stroke_dasharray="4 3"),
            circle(74, 221, 11, "#C8BEED"),
            path("M50 258c0-16 9-24 24-24s24 8 24 24Z", fill="#D7CFF0"),
            circle(99, 260, 12, COLORS["purple"], stroke="#FFFFFF", stroke_width=3),
            icon("plus", 91.5, 252.5, 15, "#FFFFFF", 1.9),
            text(128, 214, "添加一张正面半身照", 13, weight=500),
            text(128, 234, "光线清晰，让客户记住你", 11, COLORS["muted"]),
            rect(128, 246, 100, 29, COLORS["lavender"], 9),
            icon("gallery", 139, 253, 14, COLORS["purple"]),
            text(185, 265, "选择照片", 11.5, COLORS["purple"], 600, "middle"),
        ], "上传销售照片", data_role="button"),
    ], "01 销售形象")

    photos = [section_title("02", "车辆照片", 320)]
    photos.extend([
        text(136, 322, "0 / 9", 11, COLORS["muted"]),
        group("Button_OpenPhotoManager", [text(340, 322, "批量上传", 11, COLORS["purple"], 500, "end"), icon("chevron", 341, 311, 14, COLORS["purple"])], "打开照片管理", data_role="button"),
        text(36, 346, "外观、内饰、细节，按格上传更省心", 11, COLORS["muted"]),
    ])
    for position, slot in enumerate(PHOTO_SLOTS):
        photos.append(photo_slot(*slot, 36 + (position % 3) * 109, 358 + (position // 3) * 76, compact=True))
    photos.append(text(36, 593, "首张建议放左前 45°，作为视频封面参考", 10, COLORS["muted"]))
    photo_card = card("Section_02_VehiclePhotos", 302, 302, photos, "02 车辆照片九宫格")

    points = card("Section_03_SellingPoints", 616, 111, [
        section_title("03", "车辆卖点", 644),
        group("Button_OpenVehicleDetails", [text(340, 646, "完善信息", 11, COLORS["purple"], 500, "end"), icon("chevron", 341, 635, 14, COLORS["purple"])], "打开车辆信息与卖点", data_role="button"),
        group("Field_SellingPointsPreview", [
            rect(36, 660, 318, 51, COLORS["field"], 11),
            text(48, 681, "例如：空间宽敞、配置丰富、保养齐全…", 11, COLORS["muted"]),
            text(342, 701, "0 / 300", 9, COLORS["faint"], anchor="end"),
        ], "卖点快捷输入框"),
    ], "03 车辆卖点")

    return svg_document("Screen_01_VehicleEntry", "说车三岁 · 新建车辆档案", "390×844。销售照片、车辆九宫格、卖点快捷输入与底部保存操作同屏展示。所有文字为原生 text，控件以命名 g 分组。", [
        status_bar(), navbar(),
        group("PageHeading", [
            text(20, 117, "新建车辆档案", 24, weight=600, letter_spacing=-0.6),
            pill(307, 97, 63, "素材录入", size=10),
            text(20, 138, "照片和卖点填好，为视频准备素材", 12, COLORS["body"]),
        ], "页面标题"),
        sales, photo_card, points,
        footer(
            button("Button_SaveDraft", 20, 757, 102, 48, "存草稿"),
            button("Button_SaveAndContinue", 132, 757, 238, 48, "保存并继续", True, trailing="arrow"),
        ),
    ])


def photo_screen():
    grid = []
    for position, slot in enumerate(PHOTO_SLOTS):
        grid.append(photo_slot(*slot, 20 + (position % 3) * 120, 238 + (position // 3) * 130))
    return svg_document("Screen_02_VehiclePhotos", "说车三岁 · 车辆照片", "390×844。九宫格角度引导、相册批量上传、拍照上传与完成返回。9 个照片槽位均为独立命名分组。", [
        status_bar(), navbar("车辆照片"),
        group("PageHeading", [
            text(20, 117, "9 个角度，讲清一辆车", 23, weight=600, letter_spacing=-0.6),
            text(20, 141, "先拍外观，再补内饰和细节", 12, COLORS["body"]),
        ], "页面标题"),
        group("Section_PhotoProgress", [
            rect(20, 159, 350, 60, "#ECE8FF", 16),
            rect(34, 173, 32, 32, "#FFFFFF", 10),
            icon("gallery", 41, 180, 18),
            text(77, 183, "已上传 0 张照片", 13, weight=600),
            text(77, 203, "建议上传 9 张，单张也可替换", 10.5, COLORS["body"]),
            group("Button_BatchUploadVehicles", [
                rect(276, 177, 79, 27, COLORS["purple"], 9),
                text(315.5, 195, "批量选图", 11, "#FFFFFF", 600, "middle"),
            ], "从相册批量上传车辆照片", data_role="button"),
        ], "照片上传进度"),
        group("PhotoGrid_3x3", grid, "车辆照片九宫格"),
        group("Section_PhotoGuidance", [
            rect(20, 638, 350, 88, "#FFFFFF", 18, COLORS["line"]),
            icon("info", 35, 653, 17, COLORS["purple"]),
            text(60, 667, "外观 5 张 · 内饰 3 张 · 细节 1 张", 12, weight=500),
            text(36, 690, "横向拍摄，尽量让整车完整入镜。", 11, COLORS["body"]),
            text(36, 710, "首张图片将作为视频封面参考。", 11, COLORS["muted"]),
        ], "照片上传指引"),
        footer(
            button("Button_CaptureVehiclePhoto", 20, 757, 102, 48, "拍照", leading="camera"),
            button("Button_ConfirmPhotos", 132, 757, 238, 48, "完成，返回录入", True, trailing="check"),
            "支持相册多选 · 点按任意格子上传或替换",
        ),
    ])


def input_field(identifier, x, y, width, label, placeholder):
    return group(identifier, [
        text(x, y, label, 10.5, COLORS["body"], 500),
        rect(x, y + 10, width, 37, COLORS["field"], 10, "#EEEEF5"),
        text(x + 12, y + 34, placeholder, 12, COLORS["muted"]),
    ], label)


def option(identifier, x, y, width, label, selected=False, leading=None):
    contents = [
        rect(x, y, width, 28, COLORS["lavender"] if selected else "#F7F7FB", 9, "#DAD1FF" if selected else "#EEEEF5"),
    ]
    color = COLORS["purple"] if selected else COLORS["body"]
    if leading:
        contents.append(icon(leading, x + 9, y + 7, 14, color, 1.6))
    contents.append(text(x + width / 2 + (8 if leading else 0), y + 18.5, label, 10.5, color, 500 if selected else 400, "middle"))
    return group(identifier, contents, label, data_role="option", data_selected=str(selected).lower())


def details_screen():
    basics = card("Section_VehicleBasics", 159, 188, [
        icon("note", 36, 175, 19),
        text(64, 191, "车辆信息", 15, weight=600),
        text(353, 190, "车型必填，其他选填", 10, COLORS["muted"], anchor="end"),
        input_field("Field_VehicleModel", 36, 215, 318, "车型名称 *", "填写品牌、车系和年款"),
        input_field("Field_AskingPrice", 36, 282, 153, "售价（万元）", "例如 12.8"),
        input_field("Field_Mileage", 201, 282, 153, "里程（万公里）", "例如 3.2"),
    ], "车辆基础信息")

    points = card("Section_SellingPoints", 359, 187, [
        icon("sparkles", 36, 375, 19),
        text(64, 391, "这辆车，有哪些亮点？", 15, weight=600),
        text(353, 390, "0 / 300", 10, COLORS["muted"], anchor="end"),
        group("Field_SellingPoints", [
            rect(36, 405, 318, 76, COLORS["field"], 12, "#EEEEF5"),
            text(48, 428, "写下车况、配置和推荐理由…", 12, COLORS["muted"]),
            text(48, 451, "例如：全景天窗，后排空间宽敞，", 11, "#A2A4B5"),
            text(48, 469, "保养记录齐全，适合日常家用。", 11, "#A2A4B5"),
        ], "车辆卖点多行输入框"),
        option("Button_AddPoint_Space", 36, 493, 98, "+ 空间宽敞"),
        option("Button_AddPoint_Service", 145, 493, 99, "+ 保养齐全"),
        option("Button_AddPoint_Features", 255, 493, 99, "+ 配置丰富"),
        text(36, 536, "点选标签即可补充，也可以直接修改", 10, COLORS["muted"]),
    ], "车辆卖点与快捷标签")

    preferences = card("Section_VideoPreferences", 558, 169, [
        icon("video", 36, 574, 19),
        text(64, 590, "视频偏好", 15, weight=600),
        text(353, 589, "可稍后调整", 10, COLORS["muted"], anchor="end"),
        group("Field_VideoRatio", [
            text(36, 620, "画面比例", 11.5, COLORS["body"]),
            option("Option_Ratio_Portrait", 123, 602, 110, "竖屏 9:16", True, "phone"),
            option("Option_Ratio_Landscape", 243, 602, 111, "横屏 16:9", False, "landscape"),
        ], "视频画面比例"),
        group("Field_VideoDuration", [
            text(36, 659, "视频时长", 11.5, COLORS["body"]),
            option("Option_Duration_30s", 123, 641, 110, "30 秒", True),
            option("Option_Duration_60s", 243, 641, 111, "60 秒"),
        ], "视频时长"),
        group("Field_VideoTone", [
            text(36, 698, "介绍风格", 11.5, COLORS["body"]),
            option("Option_Tone_Professional", 123, 680, 110, "专业讲解", True),
            option("Option_Tone_Relaxed", 243, 680, 111, "轻松种草"),
        ], "视频介绍风格"),
    ], "后续视频生成偏好")

    return svg_document("Screen_03_DetailsAndVideo", "说车三岁 · 卖点与视频偏好", "390×844。车辆基础信息、卖点输入、快捷标签、视频比例、时长和风格。原生 text、path、rect 和命名 g 可供后续设计调整。", [
        status_bar(), navbar("车辆信息"),
        group("PageHeading", [
            text(20, 117, "让每一句介绍，都有依据", 23, weight=600, letter_spacing=-0.6),
            text(20, 141, "补充真实信息，用于生成视频脚本", 12, COLORS["body"]),
        ], "页面标题"),
        basics, points, preferences,
        footer(
            button("Button_SaveDetailsDraft", 20, 757, 102, 48, "存草稿"),
            button("Button_SaveAndPrepareVideo", 132, 757, 238, 48, "保存，准备生成视频", True, trailing="arrow"),
            "当前只保存素材，不会立即开始生成视频",
        ),
    ])


SCREENS = [
    ("01-车辆录入首页.svg", "车辆录入首页", home_screen()),
    ("02-车辆照片九宫格.svg", "车辆照片九宫格", photo_screen()),
    ("03-卖点与视频偏好.svg", "卖点与视频偏好", details_screen()),
]

for filename, title, content in SCREENS:
    (OUT / filename).write_text(content, encoding="utf-8")

preview_cards = "\n".join(
    f'<section class="screen"><div class="screen-label"><span>0{position + 1}</span><h2>{title}</h2><a href="{filename}" download>下载 SVG ↗</a></div><div class="device"><img src="{filename}" alt="{title}" width="390" height="844"></div></section>'
    for position, (filename, title, content) in enumerate(SCREENS)
)
html = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>说车三岁 · 车辆录入界面</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#efedf5;color:#202235;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1360px;margin:0 auto;padding:54px 42px 40px}.eyebrow{font-size:11px;font-weight:650;letter-spacing:2.6px;color:#776c99}header{display:flex;justify-content:space-between;align-items:end;margin:13px 0 35px}h1{margin:0 0 10px;font-size:36px;font-weight:650;letter-spacing:-1px}header p{margin:0;font-size:14px;color:#777489}.meta{display:flex;gap:9px;margin-bottom:4px}.meta span{padding:9px 13px;border:1px solid #d9d4e8;border-radius:30px;color:#777086;font-size:11px}.screens{display:grid;grid-template-columns:repeat(3,390px);justify-content:space-between;gap:28px}.screen-label{display:flex;align-items:center;gap:9px;margin:0 0 15px}.screen-label>span{font-size:11px;font-weight:600;color:#857b9b}h2{font-size:14px;font-weight:550;margin:0;flex:1}a{font-size:10px;color:#6e5adb;text-decoration:none}.device{border-radius:26px;overflow:hidden;box-shadow:0 12px 40px #2c194914,0 0 0 1px #ffffffb3;background:white;width:390px;height:844px}.device img{display:block;width:390px;height:844px}.foot{display:flex;justify-content:space-between;margin-top:28px;font-size:11px;color:#8f889f}.route{letter-spacing:.2px}@media(max-width:1280px){.screens{justify-content:center;grid-template-columns:390px}main{padding:28px 20px}header{display:block}.meta{margin-top:18px}.foot{gap:20px;line-height:1.8}}@media(max-width:430px){.screens{display:block}.screen{margin-bottom:30px}.device{width:100%;height:auto}.device img{width:100%;height:auto}.screen-label{max-width:390px}h1{font-size:30px}.foot{display:block}}
</style></head><body><main><div class="eyebrow">SHUOCHE SANSUI / MINI PROGRAM</div><header><div><h1>说车三岁<span style="font-weight:400;color:#958ba8"> / </span>车辆录入</h1><p>先收集完整素材，再把好车介绍清楚。</p></div><div class="meta"><span>390 × 844</span><span>3 个独立页面</span><span>可编辑 SVG</span></div></header><div class="screens">''' + preview_cards + '''</div><div class="foot"><span class="route">销售形象 → 车辆九宫格 → 卖点与视频偏好</span><span>照片为上传占位 · 文字与按钮均为独立分组</span></div></main></body></html>'''
(OUT / "设计预览.html").write_text(html, encoding="utf-8")

readme = '''# 说车三岁 · 车辆录入界面

## 交付内容

- `01-车辆录入首页.svg`：一屏包含销售照片、车辆照片九宫格、卖点快捷输入和保存入口。
- `02-车辆照片九宫格.svg`：展开照片管理，包含九种拍摄角度、批量选图、拍照和完成返回。
- `03-卖点与视频偏好.svg`：车型、售价、里程、卖点、视频比例、时长与介绍风格。
- `说车三岁-首页效果图.png`：首页 3 倍清晰度预览，与首页 SVG 一致。
- `说车三岁-三页总览.png`：三个页面的单页设计总览。
- `设计预览.html`：本地三页预览与独立 SVG 下载入口。
- `说车三岁-三个独立SVG.zip`：仅打包三个 SVG，不含依赖。

## 导入与编辑

三个 SVG 均声明 `width="390" height="844" viewBox="0 0 390 844"`，独立、无外链依赖。
文字保留为原生 `<text>`，没有转曲或栅格化；图标为原生路径，模块、输入框、按钮使用命名 `<g>`。
没有 `<foreignObject>`、嵌入位图、外部字体、滤镜、脚本或 `<use>` 复用。
中文字体优先为 PingFang SC，备选 Hiragino Sans GB、Microsoft YaHei 和 sans-serif。
将 SVG 拖入 Figma 后，可通过分组逐层选择元素；字体缺失时替换为本机可用的中文字体。
画板中的人像和车辆线稿都是上传占位，不代表已经上传了真实照片。

## 主要按钮图层名

| 文件 | 图层 id | 用途 |
| --- | --- | --- |
| 01 | Button_UploadSalesPhoto | 选择销售照片 |
| 01 | Button_OpenPhotoManager | 展开九宫格照片管理 |
| 01 | Button_OpenVehicleDetails | 完善车型、卖点和视频偏好 |
| 01 | Button_SaveDraft | 保存当前草稿 |
| 01 | Button_SaveAndContinue | 保存并进入完整信息确认 |
| 02 | Button_BatchUploadVehicles | 从相册批量选图 |
| 02 | Button_CaptureVehiclePhoto | 拍照上传 |
| 02 | Button_ConfirmPhotos | 完成照片选择，返回录入 |
| 03 | Button_SaveDetailsDraft | 保存信息草稿 |
| 03 | Button_SaveAndPrepareVideo | 保存档案，进入视频生成准备 |

每个车辆照片格子独立命名为 `Button_UploadVehicle_01_Front45` 至 `Button_UploadVehicle_09_Details`。
卖点快捷标签使用 `Button_AddPoint_*`，视频选项使用 `Option_Ratio_*`、`Option_Duration_*` 和 `Option_Tone_*`。

## 页面关系与状态

首页是统一录入入口，不是三个连续向导步骤；第 02、03 页是对应区域的详情编辑页。
首页「批量上传」打开照片管理；「完善信息」及「保存并继续」进入完整信息页。
照片页「完成，返回录入」回到首页；信息页保存后进入后续视频生成准备。
这次交付是静态界面设计，不包含上传、保存、识别、拖拽排序或实际视频生成程序。
初始状态照片计数为 0；占位文本是示例，不作为真实车辆信息。主按钮展示品牌标准样式。
建议实现时允许保存不完整草稿，在继续时校验销售照片、车型名称和至少一张车辆照片；九张照片为推荐，不是强制。
卖点标签仅提供快捷输入，应由录入人确认车辆实际情况。

## 视觉参数

- 主色 `#6554E8`，主文字 `#202235`，页面背景 `#F7F7FB`。
- 横向安全边距 20px；卡片圆角 20px；主按钮高 48px。
- 底部操作区从 y=742 开始，预留系统手势区域。
- 首页核心录入区无需滚动即可完整查看。

## 源文件

可在上级目录运行 `python3 build_design.py` 重新生成 SVG 与本地预览。
效果图由这些 SVG 渲染产生，避免另画一张与可编辑稿不一致的示意图。
'''
(OUT / "设计说明.md").write_text(readme, encoding="utf-8")

with zipfile.ZipFile(OUT / "说车三岁-三个独立SVG.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    for filename, title, content in SCREENS:
        archive.write(OUT / filename, arcname=filename)

print(json.dumps({"directory": str(OUT), "svgs": [name for name, _, _ in SCREENS]}, ensure_ascii=False, indent=2))
