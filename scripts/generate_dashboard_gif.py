"""
Generate an animated GIF preview of the Walmart Fraud Detection dashboard.
Run: python scripts/generate_dashboard_gif.py
Output: docs/assets/dashboard-preview.gif
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1280, 720
HEADER_H = 56
SIDEBAR_W = 230
BG = (255, 255, 255)
HEADER_BG = (0, 32, 96)          # Walmart dark blue
HEADER_FG = (255, 255, 255)
SIDEBAR_BG = (248, 249, 250)
SIDEBAR_ACTIVE_BG = (220, 228, 245)
BLUE = (0, 64, 153)
LIGHT_BLUE = (30, 100, 200)
RED = (220, 50, 50)
GREEN = (34, 139, 34)
ORANGE = (220, 120, 0)
GOLD = (200, 160, 0)
BORDER = (220, 225, 235)
TEXT_DARK = (30, 30, 50)
TEXT_MUTED = (120, 130, 150)
CARD_BG = (252, 253, 255)

try:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f_sm  = ImageFont.truetype(font_path, 13)
    f_md  = ImageFont.truetype(font_path, 16)
    f_lg  = ImageFont.truetype(font_bold_path, 20)
    f_xl  = ImageFont.truetype(font_bold_path, 28)
    f_xxl = ImageFont.truetype(font_bold_path, 38)
    f_nav = ImageFont.truetype(font_path, 15)
    f_nav_b = ImageFont.truetype(font_bold_path, 15)
    f_kpi = ImageFont.truetype(font_bold_path, 34)
    f_kpi_lbl = ImageFont.truetype(font_path, 11)
    f_badge = ImageFont.truetype(font_bold_path, 11)
    f_tiny = ImageFont.truetype(font_path, 11)
except Exception:
    f_sm = f_md = f_lg = f_xl = f_xxl = f_nav = f_nav_b = f_kpi = f_kpi_lbl = f_badge = f_tiny = ImageFont.load_default()

NAV_ITEMS = ["Home", "Overview", "Monitor", "Drivers", "Customers",
             "Geographic", "Product Analysis", "Patterns", "Methodology", "Model Performance"]


def rounded_rect(draw, xy, radius=8, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


def draw_base(active_page, subtitle=""):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, W, HEADER_H], fill=HEADER_BG)
    draw.text((24, 15), "Walmart Fraud Control", font=f_lg, fill=HEADER_FG)
    draw.text((W - 160, 18), "Share   Deploy", font=f_md, fill=(200, 210, 230))

    # Sidebar
    draw.rectangle([0, HEADER_H, SIDEBAR_W, H], fill=SIDEBAR_BG)
    draw.line([SIDEBAR_W, HEADER_H, SIDEBAR_W, H], fill=BORDER, width=1)

    y = HEADER_H + 12
    for item in NAV_ITEMS:
        is_active = item == active_page
        if is_active:
            draw.rectangle([4, y - 2, SIDEBAR_W - 4, y + 26], fill=SIDEBAR_ACTIVE_BG)
        color = TEXT_DARK if is_active else TEXT_MUTED
        font = f_nav_b if is_active else f_nav
        draw.text((18, y + 3), item, font=font, fill=color)
        y += 34

    # Sidebar footer
    draw.line([10, H - 90, SIDEBAR_W - 10, H - 90], fill=BORDER, width=1)
    draw.text((12, H - 82), "Last Updated: 2026-05-12 20:24", font=f_tiny, fill=TEXT_MUTED)
    draw.text((12, H - 64), "Owner: Fraud Ops Team", font=f_tiny, fill=TEXT_MUTED)
    draw.text((12, H - 46), "Walmart Inc. © 2024", font=f_tiny, fill=TEXT_MUTED)

    return img, draw


def kpi_card(draw, x, y, w, h, label, value, sub, val_color=TEXT_DARK, sub_color=TEXT_MUTED, border_color=BORDER):
    rounded_rect(draw, [x, y, x + w, y + h], radius=8, fill=CARD_BG, outline=border_color, width=2)
    draw.text((x + 14, y + 12), label, font=f_kpi_lbl, fill=TEXT_MUTED)
    draw.text((x + 14, y + 30), value, font=f_kpi, fill=val_color)
    if sub:
        sub_bg = (240, 250, 240) if "↓" in sub else (255, 240, 240) if "+" in sub else (235, 240, 255)
        sub_c = GREEN if "↓" in sub else RED if "+" in sub else LIGHT_BLUE
        tw = draw.textlength(sub, font=f_badge)
        rounded_rect(draw, [x + 12, y + h - 30, x + 18 + int(tw), y + h - 12], radius=10, fill=sub_bg)
        draw.text((x + 15, y + h - 29), sub, font=f_badge, fill=sub_c)


# ── Frame 1: Home ──────────────────────────────────────────────────────────────
def frame_home():
    img, draw = draw_base("Home")
    cx = SIDEBAR_W + (W - SIDEBAR_W) // 2
    draw.text((cx - 180, 90), "Walmart Fraud Control", font=f_xxl, fill=BLUE)
    draw.text((cx - 135, 138), "Fraud Detection & Analytics Dashboard", font=f_md, fill=TEXT_MUTED)

    draw.text((SIDEBAR_W + 40, 195),
              "This dashboard provides comprehensive fraud analysis for Walmart", font=f_md, fill=TEXT_DARK)
    draw.text((SIDEBAR_W + 40, 218), "e-commerce deliveries in Central Florida.", font=f_md, fill=TEXT_DARK)

    draw.text((SIDEBAR_W + 40, 265), "Available Pages", font=f_xl, fill=BLUE)
    draw.text((SIDEBAR_W + 40, 298), "Navigate through the sidebar to access different analysis modules:", font=f_md, fill=TEXT_MUTED)

    pages = [
        ("1. Overview", "Executive summary and KPIs"),
        ("2. Monitor", "Real-time operational dashboard"),
        ("3. Drivers", "Driver risk analysis"),
        ("4. Customers", "Customer behavior patterns"),
        ("5. Geographic", "Regional hotspot analysis"),
        ("6. Product Analysis", "Product-level fraud patterns"),
        ("7. Methodology", "Model documentation"),
        ("8. Patterns", "Statistical fraud patterns"),
        ("9. Model Performance", "ML model monitoring"),
    ]
    y = 330
    for title, desc in pages:
        draw.text((SIDEBAR_W + 60, y), f"• {title}", font=f_nav_b, fill=TEXT_DARK)
        draw.text((SIDEBAR_W + 185, y), f"- {desc}", font=f_nav, fill=TEXT_MUTED)
        y += 24
    return img


# ── Frame 2: Overview ──────────────────────────────────────────────────────────
def frame_overview():
    img, draw = draw_base("Overview")
    cx = SIDEBAR_W + 20

    draw.text((cx, 75), "Overview", font=f_md, fill=TEXT_MUTED)
    draw.text((cx, 98), "Network Health Monitor", font=f_xxl, fill=BLUE)

    alert_x = W - 180
    rounded_rect(draw, [alert_x, 96, alert_x + 148, 120], radius=10, fill=(255, 245, 200))
    draw.text((alert_x + 14, 101), "High Alert Level", font=f_badge, fill=GOLD)

    draw.text((cx, 145), "Analysis of delivery anomalies in Central Florida Region.", font=f_md, fill=TEXT_MUTED)
    draw.text((cx, 168), "Data Period: 2023-01-01 to 2023-12-31", font=f_sm, fill=TEXT_MUTED)

    draw.text((cx, 200), "Executive Performance Indicators", font=f_lg, fill=BLUE)

    card_w = (W - SIDEBAR_W - 80) // 4
    kpis = [
        ("ORDERS ANALYZED (YTD)", "10,000", "2023-01-01 to 2023-12-31", BLUE),
        ("MISSING ITEM RATE", "1.63%", "↓ 0.32% MoM", GREEN),
        ("PROJECTED ANNUAL LOSS", "$298,260", "$74,565 recoverable at 25%", RED),
        ("CRITICAL ALERTS", "152", "+72 High priority", RED),
    ]
    for i, (lbl, val, sub, col) in enumerate(kpis):
        x = SIDEBAR_W + 20 + i * (card_w + 16)
        kpi_card(draw, x, 228, card_w, 100, lbl, val, sub, val_color=col)

    draw.text((cx, 355), "Risk Intelligence Summary", font=f_lg, fill=BLUE)
    draw.line([cx, 378, W - 20, 378], fill=BORDER, width=1)

    risk_cards = [
        ("DRIVER RISK PROFILE", "150", "Critical Risk Drivers  +275 High | 0 Medium", RED, (255, 248, 240)),
        ("CUSTOMER RISK PROFILE", "2", "Critical Risk Customers  +15 High | 194 Medium", ORANGE, (255, 252, 235)),
        ("FLAGGED ORDERS", "15.0%", "1,502 orders with missing items  Out of 10,000 total", TEXT_DARK, (242, 245, 255)),
    ]
    rc_w = (W - SIDEBAR_W - 60) // 3
    for i, (lbl, val, sub, vcol, bg) in enumerate(risk_cards):
        x = SIDEBAR_W + 20 + i * (rc_w + 10)
        rounded_rect(draw, [x, 390, x + rc_w, 490], radius=8, fill=bg, outline=BORDER, width=2)
        draw.text((x + 14, 404), lbl, font=f_kpi_lbl, fill=TEXT_MUTED)
        draw.text((x + 14, 422), val, font=f_kpi, fill=vcol)
        draw.text((x + 14, 465), sub, font=f_tiny, fill=TEXT_MUTED)

    return img


# ── Frame 3: Geographic ────────────────────────────────────────────────────────
def frame_geographic():
    img, draw = draw_base("Geographic")
    cx = SIDEBAR_W + 20

    draw.text((cx, 75), "Central Florida Bubble Map", font=f_xl, fill=TEXT_DARK)
    draw.text((cx, 110), "Bubble size = order volume, hover includes risk and loss context.", font=f_sm, fill=TEXT_MUTED)

    # Map area
    map_x, map_y, map_w, map_h = cx, 135, 510, 340
    rounded_rect(draw, [map_x, map_y, map_x + map_w, map_y + map_h], radius=6, fill=(242, 244, 248), outline=BORDER)
    draw.text((map_x + map_w // 2 - 80, map_y + map_h // 2 - 10), "Central Florida Region", font=f_md, fill=TEXT_MUTED)

    cities = [
        ("Altamonte Springs", (270, 230), (255, 180, 50), 24),
        ("Apopka",            (260, 200), (100, 170, 240), 32),
        ("Clermont",          (195, 270), (34, 150, 80), 42),
        ("Orlando",           (295, 270), (210, 60, 120), 38),
        ("Winter Park",       (310, 250), (220, 200, 50), 26),
        ("Sanford",           (345, 195), (210, 100, 30), 40),
        ("Kissimmee",         (295, 340), (20, 100, 180), 50),
    ]
    for name, (bx, by), color, r in cities:
        draw.ellipse([map_x + bx - r, map_y + by - r, map_x + bx + r, map_y + by + r],
                     fill=(*color, 180), outline=(*color, 255))

    # Legend
    legend_x = map_x
    draw.text((legend_x, map_y + map_h + 8), "●", font=f_sm, fill=(255, 180, 50))
    draw.text((legend_x + 20, map_y + map_h + 8), "Altamonte Springs", font=f_tiny, fill=TEXT_DARK)
    draw.text((legend_x + 150, map_y + map_h + 8), "●", font=f_sm, fill=(100, 170, 240))
    draw.text((legend_x + 170, map_y + map_h + 8), "Apopka", font=f_tiny, fill=TEXT_DARK)
    draw.text((legend_x + 240, map_y + map_h + 8), "●", font=f_sm, fill=(34, 150, 80))
    draw.text((legend_x + 260, map_y + map_h + 8), "Clermont", font=f_tiny, fill=TEXT_DARK)
    draw.text((legend_x + 340, map_y + map_h + 8), "●", font=f_sm, fill=(210, 60, 120))
    draw.text((legend_x + 360, map_y + map_h + 8), "Orlando", font=f_tiny, fill=TEXT_DARK)

    # Bar chart
    chart_x = map_x + map_w + 30
    chart_w = W - chart_x - 20
    draw.text((chart_x, 75), "Missing Rate Ranking", font=f_xl, fill=TEXT_DARK)
    draw.text((chart_x, 110), "Regions ordered by missing rate with average baseline.", font=f_sm, fill=TEXT_MUTED)

    bars = [
        ("Kissimmee",       1.90, (20, 100, 180)),
        ("Sanford",         1.82, (210, 100, 30)),
        ("Winter Park",     1.72, (220, 200, 50)),
        ("Orlando",         1.66, (210, 60, 120)),
        ("Clermont",        1.60, (34, 150, 80)),
        ("Apopka",          1.56, (100, 170, 240)),
        ("Altamonte Springs", 1.46, (255, 180, 50)),
    ]
    by_start = 138
    bh = 30
    max_val = 2.2
    for i, (city, val, color) in enumerate(bars):
        y = by_start + i * (bh + 8)
        bar_len = int((val / max_val) * (chart_w - 80))
        draw.text((chart_x, y + 7), city, font=f_tiny, fill=TEXT_DARK)
        bx = chart_x + 130
        draw.rectangle([bx, y + 4, bx + bar_len, y + bh - 4], fill=color)
        draw.text((bx + bar_len + 5, y + 7), f"{val:.2f}%", font=f_tiny, fill=TEXT_DARK)

    # Average line
    avg_x = chart_x + 130 + int((1.64 / max_val) * (chart_w - 80))
    draw.line([avg_x, by_start - 5, avg_x, by_start + 7 * (bh + 8)], fill=(180, 130, 50), width=2)
    draw.text((avg_x + 4, by_start - 16), "Average 1.64%", font=f_tiny, fill=(180, 130, 50))

    return img


# ── Frame 4: Product Analysis ──────────────────────────────────────────────────
def frame_products():
    img, draw = draw_base("Product Analysis")
    cx = SIDEBAR_W + 20

    half_w = (W - SIDEBAR_W - 60) // 2
    right_x = cx + half_w + 20

    # Treemap title
    draw.text((cx, 75), "Treemap: Category > Price Band > SKU", font=f_xl, fill=TEXT_DARK)
    draw.text((cx, 106), "Node size = estimated loss; node color = composite risk score.", font=f_sm, fill=TEXT_MUTED)

    # Treemap placeholder
    tm_y = 128
    tm_h = 260
    rounded_rect(draw, [cx, tm_y, cx + half_w, tm_y + tm_h], radius=4, fill=(50, 20, 10), outline=BORDER)
    draw.text((cx + 8, tm_y + 8), "Electronics", font=f_sm, fill=(220, 180, 100))

    blocks = [
        ("Bose QC Earbuds",    cx+8,       tm_y+30, cx+150,    tm_y+110, (160,30,10)),
        ("Sony PS5",           cx+8,       tm_y+115, cx+150,   tm_y+210, (180,40,10)),
        ("Google Chromecast",  cx+155,     tm_y+30,  cx+half_w-5, tm_y+90, (200,60,20)),
        ("Nintendo Switch",    cx+155,     tm_y+95,  cx+260,   tm_y+155, (170,50,10)),
        ("GoPro Hero 9",       cx+8,       tm_y+215, cx+110,   tm_y+tm_h-5, (140,25,10)),
        ("Nest Thermostat",    cx+115,     tm_y+215, cx+230,   tm_y+tm_h-5, (150,35,10)),
    ]
    for lbl, x0, y0, x1, y1, color in blocks:
        draw.rectangle([x0, y0, x1, y1], fill=color, outline=(30,10,5))
        if x1 - x0 > 60 and y1 - y0 > 20:
            draw.text((x0 + 4, y0 + 4), lbl[:20], font=f_tiny, fill=(240, 230, 200))

    # Time series title
    draw.text((right_x, 75), "Time Series: Loss by Category (Last 6 Months)", font=f_lg, fill=TEXT_DARK)
    draw.text((right_x, 106), "Dotted line marks historical baseline monthly loss.", font=f_sm, fill=TEXT_MUTED)

    ts_y, ts_h = 128, 240
    rounded_rect(draw, [right_x, ts_y, right_x + half_w, ts_y + ts_h], radius=4, fill=CARD_BG, outline=BORDER)

    months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    electronics = [9800, 12400, 9200, 10600, 9400, 9600]
    supermarket = [1100, 1000, 900, 1100, 1000, 1050]

    def map_y_val(val, mn=500, mx=13500, area_h=180, area_y=ts_y+30):
        return area_y + area_h - int((val - mn) / (mx - mn) * area_h)

    pts_e = [(right_x + 40 + i * (half_w - 60) // 5, map_y_val(v)) for i, v in enumerate(electronics)]
    pts_s = [(right_x + 40 + i * (half_w - 60) // 5, map_y_val(v)) for i, v in enumerate(supermarket)]

    baseline_y = map_y_val(10500)
    for x in range(right_x + 35, right_x + half_w - 10, 8):
        draw.line([x, baseline_y, x + 4, baseline_y], fill=GOLD, width=1)

    for i in range(len(pts_e) - 1):
        draw.line([pts_e[i], pts_e[i+1]], fill=LIGHT_BLUE, width=2)
        draw.line([pts_s[i], pts_s[i+1]], fill=(150, 80, 180), width=2)

    for pt in pts_e:
        draw.ellipse([pt[0]-3, pt[1]-3, pt[0]+3, pt[1]+3], fill=LIGHT_BLUE)
    for pt in pts_s:
        draw.ellipse([pt[0]-3, pt[1]-3, pt[0]+3, pt[1]+3], fill=(150, 80, 180))

    for i, (m, pt) in enumerate(zip(months, pts_e)):
        draw.text((pt[0]-10, ts_y + ts_h - 22), m, font=f_tiny, fill=TEXT_MUTED)

    # Legend
    draw.rectangle([right_x + 10, ts_y + ts_h - 14, right_x + 26, ts_y + ts_h - 6], fill=LIGHT_BLUE)
    draw.text((right_x + 30, ts_y + ts_h - 15), "Electronics", font=f_tiny, fill=TEXT_DARK)
    draw.rectangle([right_x + 110, ts_y + ts_h - 14, right_x + 126, ts_y + ts_h - 6], fill=(150, 80, 180))
    draw.text((right_x + 130, ts_y + ts_h - 15), "Supermarket", font=f_tiny, fill=TEXT_DARK)

    return img


# ── Frame 5: Model Performance ────────────────────────────────────────────────
def frame_model():
    img, draw = draw_base("Model Performance")
    cx = SIDEBAR_W + 20

    draw.text((cx, 75), "Model Performance & MLOps", font=f_xxl, fill=BLUE)
    draw.text((cx, 122), "Monitoring Isolation Forest efficacy, data drift, and algorithmic stability.", font=f_md, fill=TEXT_MUTED)

    draw.line([cx, 155, W - 20, 155], fill=BORDER, width=1)
    draw.text((cx, 168), "1. Strategy & Architecture", font=f_xl, fill=BLUE)

    half_w = (W - SIDEBAR_W - 60) // 2

    draw.text((cx, 205), "Algorithm:", font=f_md, fill=TEXT_DARK)
    rounded_rect(draw, [cx + 95, 203, cx + 310, 226], radius=4, fill=(235, 245, 255))
    draw.text((cx + 102, 206), "Isolation Forest (Unsupervised)", font=f_sm, fill=LIGHT_BLUE)

    draw.text((cx, 238), "Why Isolation Forest?", font=f_nav_b, fill=TEXT_DARK)
    points = [
        "Label Deficiency: We lack historically confirmed fraud labels.",
        "Anomaly Focus: Fraud mimics rare outliers (high volume, unusual hours).",
        "Scalability: Efficient for high-volume order streams.",
    ]
    for i, pt in enumerate(points):
        draw.text((cx + 10, 262 + i * 26), f"• {pt}", font=f_sm, fill=TEXT_DARK)

    # Anomaly rate card
    card_x = SIDEBAR_W + half_w + 20
    rounded_rect(draw, [card_x, 195, card_x + 220, 340], radius=8, fill=CARD_BG, outline=(100, 150, 220), width=2)
    draw.text((card_x + 14, 210), "CURRENT ANOMALY RATE", font=f_kpi_lbl, fill=TEXT_MUTED)
    draw.text((card_x + 14, 238), "14.90%", font=f_kpi, fill=TEXT_DARK)
    rounded_rect(draw, [card_x + 12, 292, card_x + 122, 316], radius=10, fill=(255, 235, 235))
    draw.text((card_x + 16, 296), "-1.6% vs Ref", font=f_badge, fill=RED)

    draw.line([cx, 355, W - 20, 355], fill=BORDER, width=1)
    draw.text((cx, 368), "2. MLOps Monitoring", font=f_xl, fill=BLUE)

    # Tab row
    tab_y = 402
    draw.text((cx, tab_y), "Data Drift (KS Test)", font=f_nav_b, fill=LIGHT_BLUE)
    draw.line([cx, tab_y + 20, cx + 160, tab_y + 20], fill=LIGHT_BLUE, width=2)
    draw.text((cx + 175, tab_y), "Feature Importance", font=f_nav, fill=TEXT_MUTED)

    draw.text((cx, 440), "Reference vs Current Period Drift", font=f_lg, fill=BLUE)

    # Table
    table_y = 470
    cols = [("feature", 180), ("ks_stat", 80), ("p_value", 90), ("Status", 80), ("curr_mean", 100)]
    tx = cx
    draw.rectangle([tx, table_y, tx + 560, table_y + 25], fill=(242, 245, 255))
    for col, cw in cols:
        draw.text((tx + 6, table_y + 5), col, font=f_kpi_lbl, fill=TEXT_MUTED)
        tx += cw

    rows = [
        ("order_amount", "0.016000", "0.544187", "Stable",  "284.119"),
        ("items_missing", "0.002400", "1.000000", "Stable",  "0.1646"),
        ("delivery_hour",  "0.018000", "0.472000", "Stable",  "13.42"),
    ]
    for ri, row in enumerate(rows):
        ry = table_y + 28 + ri * 28
        tx = cx
        bg_row = (252, 253, 255) if ri % 2 == 0 else (247, 249, 255)
        draw.rectangle([cx, ry, cx + 560, ry + 26], fill=bg_row)
        for j, (val, (col, cw)) in enumerate(zip(row, cols)):
            color = GREEN if val == "Stable" else RED if val == "Drift" else TEXT_DARK
            draw.text((tx + 6, ry + 6), val, font=f_tiny, fill=color)
            tx += cw

    return img


def make_gif(frames, path, duration=2500):
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        optimize=False,
        duration=duration,
        loop=0,
    )
    print(f"Saved: {path} ({os.path.getsize(path) // 1024} KB)")


if __name__ == "__main__":
    os.makedirs("docs/assets", exist_ok=True)

    frames = [
        frame_home(),
        frame_overview(),
        frame_geographic(),
        frame_products(),
        frame_model(),
    ]

    make_gif(frames, "docs/assets/dashboard-preview.gif")
    print("Done. GIF saved to docs/assets/dashboard-preview.gif")
