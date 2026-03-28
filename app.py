import os
import calendar
from datetime import datetime, date, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, abort, session, jsonify, Response
)

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import and_

app = Flask(__name__)
app.config["SECRET_KEY"] = "kaanmotel-2026-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sadakat.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MANAGER_PASSWORD"] = "kaan2026"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

CONTACT_INFO = {
    "address": "Deniz Mahallesi, Değirmenardı Mevkii, Zafer Sokak No:10, Avşa Adası",
    "phone": "+90 553 889 85 44",
    "phone_raw": "905538898544",
    "email": "kaanmotelavsa@gmail.com",
    "whatsapp_link": (
        "https://wa.me/905538898544"
        "?text=Merhaba%20Kaan%20Motel,%20rezervasyon%20hakk%C4%B1nda%20bilgi%20almak%20istiyorum."
    ),
    "instagram": "https://instagram.com/avsakaanmotel",
    "maps_embed": (
        "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3032.958911929898!"
        "2d27.495157275155798!3d40.520399249324505!2m3!1f0!2f0!3f0!"
        "3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x14b419000f224301%3A0x4e6d88d0246a0cb6!"
        "2sKaan%20Motel!5e0!3m2!1str!2str!4v1760429758683!5m2!1str!2str"
    ),
}

REVIEWS = {
    "airbnb": {
        "platform": "Airbnb",
        "score": "4.8 / 5",
        "icon_class": "fab fa-airbnb",
        "items": [
            "Temiz, huzurlu ve ailece rahat edebileceğiniz bir yer. Konum çok iyiydi.",
            "Odalar düzenliydi, ortam sakindi. Avşa’da kafa dinlemek için güzel bir seçim.",
            "Ev sahibi çok ilgiliydi. Giriş süreci çok kolay ilerledi.",
            "Bahçe alanı çok keyifliydi. Sessiz ve samimi bir atmosfer vardı."
        ]
    },
    "google": {
        "platform": "Google",
        "score": "4.7 / 5",
        "icon_class": "fab fa-google",
        "items": [
            "İletişim çok hızlıydı, WhatsApp üzerinden kolayca bilgi alabildik.",
            "Konumu güzel, odalar temiz, işletme ilgili. Tavsiye ederim.",
            "Aile ortamı sevenler için çok uygun. Gürültüden uzak bir yer.",
            "Fiyat performans açısından memnun kaldık. Tekrar gelebiliriz."
        ]
    },
    "tripadvisor": {
        "platform": "Tripadvisor",
        "score": "4.6 / 5",
        "icon_class": "fas fa-suitcase",
        "items": [
            "Sakin, temiz ve samimi bir konaklama deneyimi. Tekrar gelmek isteriz.",
            "Kısa tatil için tercih ettik, gayet memnun kaldık.",
            "Denize yakınlık ve huzurlu atmosfer en sevdiğimiz tarafı oldu.",
            "Odalar düzenliydi, işletme çözüm odaklıydı ve iletişim çok rahattı."
        ]
    }
}

ROOM_DEFINITIONS = {
    "standart": {
        "name": "3 Kişilik Standart Oda",
        "description": "Avşa otelleri arasında temiz, sade ve konforlu bir standart oda seçeneği.",
        "long_description": (
            "3 Kişilik Standart Odamız, Avşa Adası'nda uygun fiyatlı ve huzurlu konaklama "
            "araması yapan misafirler için ideal bir seçenektir. Ferah yapısı, kullanışlı düzeni "
            "ve denize yakın konumuyla rahat bir tatil deneyimi sunar."
        ),
        "default_price": 3000,
        "capacity": 3,
        "folder_names": ["standart"],
    },
    "suit": {
        "name": "Suit Oda",
        "description": "Aileler ve arkadaş grupları için geniş ve rahat suit oda seçeneği.",
        "long_description": (
            "Suit Odamız, Avşa'da nerede kalınır diye araştıran misafirler için "
            "geniş ve konforlu bir konaklama deneyimi sunar."
        ),
        "default_price": 5000,
        "capacity": 5,
        "folder_names": ["suit"],
    },
    "petsuit": {
        "name": "Petsuit Oda",
        "description": "Evcil hayvan dostu, geniş ve rahat konaklama seçeneği.",
        "long_description": (
            "Petsuit Odamız, patili dostlarıyla birlikte Avşa Adası tatili yapmak isteyen "
            "misafirler için hazırlanmıştır."
        ),
        "default_price": 3800,
        "capacity": 4,
        "folder_names": ["pet-dostu", "petsuit"],
    },
}

ROOM_ORDER = ["STD01", "STD02", "STD03", "STD04", "SUI01", "PET01", "STD07", "STD08"]

SOURCE_OPTIONS = [
    "Website",
    "Airbnb",
    "WhatsApp",
    "Instagram",
    "Telefon",
    "Booking",
    "Diğer"
]

MONTH_NAMES_TR = {
    1: "Ocak",
    2: "Şubat",
    3: "Mart",
    4: "Nisan",
    5: "Mayıs",
    6: "Haziran",
    7: "Temmuz",
    8: "Ağustos",
    9: "Eylül",
    10: "Ekim",
    11: "Kasım",
    12: "Aralık"
}


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, default=2)

    reservations = db.relationship("Reservation", backref="room_details", lazy=True)

    def __repr__(self):
        return f"<Room {self.room_number} - {self.room_type}>"


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(120), nullable=False)
    guest_email = db.Column(db.String(120), nullable=False)
    guest_phone = db.Column(db.String(30))
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    adults = db.Column(db.Integer, default=1)
    children = db.Column(db.Integer, default=0)
    total_price = db.Column(db.Float, default=0.0)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=True)
    status = db.Column(db.String(50), default="Yeni Talep")
    source = db.Column(db.String(50), default="Website")

    def __repr__(self):
        return f"<Reservation {self.id} - {self.guest_name}>"


class ManualBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(120), nullable=True)
    source = db.Column(db.String(50), default="Diğer")
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=True)
    is_full_hotel = db.Column(db.Boolean, default=False)
    note = db.Column(db.Text, nullable=True)

    room = db.relationship("Room", backref="manual_blocks")

    def __repr__(self):
        return f"<ManualBlock {self.id}>"


class PriceRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_type = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    nightly_price = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<PriceRule {self.room_type} {self.start_date}-{self.end_date}: {self.nightly_price}>"


def manager_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("manager_logged_in"):
            flash("Bu alana erişmek için yönetim şifresi gerekli.", "warning")
            return redirect(url_for("yonetim_login"))
        return view_func(*args, **kwargs)
    return wrapped_view


def normalize_room_type(room_type_value):
    if not room_type_value:
        return None

    room_type_value = room_type_value.strip().lower()
    aliases = {
        "standart": "standart",
        "suit": "suit",
        "petsuit": "petsuit",
        "pet-dostu": "petsuit",
        "pet_dostu": "petsuit",
    }
    return aliases.get(room_type_value, room_type_value)


def room_sort_key(room_obj):
    if room_obj.room_number in ROOM_ORDER:
        return ROOM_ORDER.index(room_obj.room_number)
    return 999


def get_room_display_name(room):
    room_names = {
        "STD01": "Oda 1",
        "STD02": "Oda 2",
        "STD03": "Oda 3",
        "STD04": "Oda 4",
        "SUI01": "Suit",
        "PET01": "Petsuit",
        "STD07": "Oda 7",
        "STD08": "Oda 8",
    }
    return room_names.get(room.room_number, room.room_number)


def build_seo(title, description):
    return {"title": title, "description": description}


def get_default_price(room_type):
    normalized = normalize_room_type(room_type)
    return float(ROOM_DEFINITIONS.get(normalized, {}).get("default_price", 0))


def get_lowest_price(room_type):
    """
    Oda tipine ait en düşük fiyatı döndürür.
    Fiyat kuralları varsa en düşük rule fiyatı ile varsayılan fiyatı karşılaştırır.
    """
    normalized = normalize_room_type(room_type)
    default_price = get_default_price(normalized)

    min_rule = PriceRule.query.filter(
        PriceRule.room_type == normalized
    ).order_by(PriceRule.nightly_price.asc()).first()

    if min_rule:
        return min(float(min_rule.nightly_price), default_price)

    return default_price


def get_nightly_price(room_type, target_date):
    normalized = normalize_room_type(room_type)
    price_rule = PriceRule.query.filter(
        PriceRule.room_type == normalized,
        PriceRule.start_date <= target_date,
        PriceRule.end_date >= target_date
    ).order_by(PriceRule.id.desc()).first()

    if price_rule:
        return float(price_rule.nightly_price)

    return get_default_price(normalized)


def calculate_total_price(room_type, check_in, check_out):
    total = 0.0
    current = check_in
    while current < check_out:
        total += get_nightly_price(room_type, current)
        current += timedelta(days=1)
    return total


def load_room_data_from_static():
    room_data = []
    base_room_path = os.path.join(app.root_path, "static", "rooms")

    if not os.path.exists(base_room_path):
        return room_data

    for room_type_code, room_meta in ROOM_DEFINITIONS.items():
        found_folder = None

        for folder_name in room_meta["folder_names"]:
            possible_path = os.path.join(base_room_path, folder_name)
            if os.path.isdir(possible_path):
                found_folder = folder_name
                break

        if not found_folder:
            continue

        room_dir = os.path.join(base_room_path, found_folder)
        files = sorted(os.listdir(room_dir))

        gallery_images = []
        main_image_path = None

        for filename in files:
            lower_name = filename.lower()
            if not lower_name.endswith((".png", ".jpg", ".jpeg", ".webp")):
                continue

            file_url = url_for("static", filename=f"rooms/{found_folder}/{filename}")

            if lower_name in ["main.jpg", "main.jpeg", "main.png", "main.webp"]:
                main_image_path = file_url

            gallery_images.append({
                "title": f"{room_meta['name']} Görsel {len(gallery_images) + 1}",
                "path": file_url
            })

        if not main_image_path and gallery_images:
            main_image_path = gallery_images[0]["path"]

        if not main_image_path:
            continue

        room_data.append({
            "id": room_type_code,
            "folder_id": found_folder,
            "name": room_meta["name"],
            "description": room_meta["description"],
            "long_description": room_meta["long_description"],
            "price_per_night": get_lowest_price(room_type_code),
            "capacity": room_meta["capacity"],
            "main_image": main_image_path,
            "gallery_images": gallery_images
        })

    return room_data


def get_gallery_items():
    gallery_list = []
    gallery_folder = os.path.join(app.root_path, "static", "gallery")

    if not os.path.exists(gallery_folder):
        return gallery_list

    for filename in sorted(os.listdir(gallery_folder)):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            gallery_list.append({
                "title": filename.replace("_", " ").rsplit(".", 1)[0].title(),
                "description": "Kaan Motel ve Avşa Adası'ndan kareler",
                "path": url_for("static", filename=f"gallery/{filename}")
            })

    return gallery_list


def load_yat_kulubu_data():
    room_id = "yat_kulubu"
    base_path = os.path.join(app.root_path, "static", "rooms", room_id)

    if not os.path.isdir(base_path):
        return None

    files = sorted(os.listdir(base_path))
    gallery_images = []
    main_image_path = None

    for filename in files:
        lower_name = filename.lower()
        if not lower_name.endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue

        file_url = url_for("static", filename=f"rooms/{room_id}/{filename}")

        if lower_name in ["main.jpg", "main.jpeg", "main.png", "main.webp"]:
            main_image_path = file_url

        gallery_images.append({
            "title": f"Yat Kulübü Görsel {len(gallery_images) + 1}",
            "path": file_url
        })

    if not main_image_path and gallery_images:
        main_image_path = gallery_images[0]["path"]

    if not main_image_path:
        return None

    return {
        "title": "Kaan Motel Yat Kulübü",
        "description": "Avşa Adası'nda deniz keyfini farklı bir deneyime dönüştüren özel alan.",
        "long_text": (
            "Kaan Motel Yat Kulübü, denizle iç içe vakit geçirmek isteyen misafirler için "
            "özel bir deneyim alanı sunar."
        ),
        "image_path": main_image_path,
        "gallery_images": gallery_images
    }


def check_availability(room_type_kod, check_in_date_str, check_out_date_str):
    normalized_room_type = normalize_room_type(room_type_kod)

    try:
        check_in = datetime.strptime(check_in_date_str, "%Y-%m-%d").date()
        check_out = datetime.strptime(check_out_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False, "Lütfen geçerli giriş ve çıkış tarihleri seçin."

    if check_in >= check_out:
        return False, "Çıkış tarihi, giriş tarihinden sonra olmalıdır."

    if check_in < date.today():
        return False, "Geçmiş tarih seçemezsiniz."

    candidate_rooms = Room.query.filter_by(room_type=normalized_room_type).all()
    if not candidate_rooms:
        return False, "Seçtiğiniz oda tipi şu anda sistemde bulunmuyor."

    full_hotel_block = ManualBlock.query.filter(
        ManualBlock.is_full_hotel.is_(True),
        ManualBlock.check_out > check_in,
        ManualBlock.check_in < check_out
    ).first()

    if full_hotel_block:
        return False, "Seçtiğiniz tarihler için tesis genelinde doluluk veya blokaj bulunuyor."

    blocking_statuses = ["Yeni Talep", "Onaylandı", "Telefon Onaylı", "Giriş Yaptı"]

    clashing_reservations = Reservation.query.filter(
        Reservation.room_id.in_([room.id for room in candidate_rooms]),
        and_(
            Reservation.check_out > check_in,
            Reservation.check_in < check_out,
            Reservation.status.in_(blocking_statuses)
        )
    ).all()

    clashing_blocks = ManualBlock.query.filter(
        ManualBlock.is_full_hotel.is_(False),
        ManualBlock.room_id.in_([room.id for room in candidate_rooms]),
        ManualBlock.check_out > check_in,
        ManualBlock.check_in < check_out
    ).all()

    reserved_room_ids = {r.room_id for r in clashing_reservations}
    blocked_room_ids = {b.room_id for b in clashing_blocks}

    available_rooms = [
        room for room in sorted(candidate_rooms, key=room_sort_key)
        if room.id not in reserved_room_ids and room.id not in blocked_room_ids
    ]

    if not available_rooms:
        room_name = ROOM_DEFINITIONS.get(normalized_room_type, {}).get("name", "Seçilen oda")
        return False, f"Üzgünüz, {room_name} için seçtiğiniz tarihlerde uygun oda görünmüyor."

    return True, available_rooms[0]


def build_calendar_matrix(year, month):
    start_date = date(year, month, 1)
    num_days = calendar.monthrange(year, month)[1]
    end_date = date(year, month, num_days)

    rooms = Room.query.order_by(Room.room_number.asc()).all()
    blocking_statuses = ["Yeni Talep", "Onaylandı", "Telefon Onaylı", "Giriş Yaptı"]

    reservations = Reservation.query.filter(
        Reservation.check_out > start_date,
        Reservation.check_in <= end_date,
        Reservation.status.in_(blocking_statuses)
    ).all()

    manual_blocks = ManualBlock.query.filter(
        ManualBlock.check_out > start_date,
        ManualBlock.check_in <= end_date
    ).all()

    days = list(range(1, num_days + 1))
    rows = []

    for room in rooms:
        row = {
            "room_id": room.id,
            "room_number": room.room_number,
            "room_name": get_room_display_name(room),
            "days": []
        }

        for day in days:
            current_day = date(year, month, day)
            status = "bos"
            label = ""

            full_hotel_block = next(
                (b for b in manual_blocks if b.is_full_hotel and b.check_in <= current_day < b.check_out),
                None
            )

            room_block = next(
                (b for b in manual_blocks if not b.is_full_hotel and b.room_id == room.id and b.check_in <= current_day < b.check_out),
                None
            )

            room_reservation = next(
                (r for r in reservations if r.room_id == room.id and r.check_in <= current_day < r.check_out),
                None
            )

            if full_hotel_block:
                status = "blokaj"
                label = f"Tüm otel - {full_hotel_block.source}"
            elif room_block:
                status = "blokaj"
                label = room_block.source
            elif room_reservation:
                status = "rezervasyon"
                label = room_reservation.source

            row["days"].append({
                "day": day,
                "status": status,
                "label": label
            })

        rows.append(row)

    return {
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES_TR.get(month, str(month)),
        "days": days,
        "rows": rows
    }


@app.context_processor
def inject_globals():
    return {
        "contact_info": CONTACT_INFO,
        "current_year": datetime.now().year,
        "manager_logged_in": session.get("manager_logged_in", False)
    }


@app.route('/google7e356096ec55f89d.html')
def google_verification():
    return app.send_static_file('google7e356096ec55f89d.html')

@app.route("/")
def index():
    seo = build_seo(
        "Kaan Motel | Avşa Otelleri Arasında Huzurlu ve Samimi Konaklama",
        "Avşa otelleri, Avşa otel fiyatları ve Avşa'da nerede kalınır soruları için sade, temiz ve konforlu bir seçenek: Kaan Motel."
    )

    featured_gallery = get_gallery_items()[:3]
    preview_prices = {
        room_type: get_lowest_price(room_type)
        for room_type in ROOM_DEFINITIONS.keys()
    }

    return render_template(
        "index.html",
        title=seo["title"],
        description=seo["description"],
        slogan="Avşa Adası'nda huzurlu, samimi ve konforlu konaklama",
        reviews=REVIEWS,
        featured_gallery=featured_gallery,
        today=date.today().isoformat(),
        preview_prices=preview_prices
    )


@app.route("/api/calculate-price", methods=["GET"])
def api_calculate_price():
    room_type = request.args.get("room_type")
    check_in_str = request.args.get("check_in")
    check_out_str = request.args.get("check_out")

    if not room_type:
        return jsonify({"ok": False, "message": "Oda tipi eksik."}), 400

    normalized_room_type = normalize_room_type(room_type)

    if not check_in_str or not check_out_str:
        nightly_price = get_lowest_price(normalized_room_type)
        return jsonify({
            "ok": True,
            "nightly_price": nightly_price,
            "total_price": None,
            "nights": 0
        })

    try:
        check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
        check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"ok": False, "message": "Geçersiz tarih formatı."}), 400

    if check_in >= check_out:
        return jsonify({"ok": False, "message": "Çıkış tarihi girişten sonra olmalı."}), 400

    nightly_price = get_nightly_price(normalized_room_type, check_in)
    total_price = calculate_total_price(normalized_room_type, check_in, check_out)
    nights = (check_out - check_in).days

    return jsonify({
        "ok": True,
        "nightly_price": nightly_price,
        "total_price": total_price,
        "nights": nights
    })


@app.route("/galeri")
def galeri():
    seo = build_seo(
        "Kaan Motel Galeri | Avşa Adası Oda ve Tesis Görselleri",
        "Avşa'da nerede kalınır diye araştırıyorsanız Kaan Motel galerisini inceleyin. Odalarımızı, bahçemizi ve tesisimizi fotoğraflarla görün."
    )

    return render_template(
        "galeri.html",
        title=seo["title"],
        description=seo["description"],
        gallery_items=get_gallery_items()
    )


@app.route("/odalar")
def odalar():
    seo = build_seo(
        "Kaan Motel Odalar | Avşa Otel Fiyatları ve Oda Seçenekleri",
        "Avşa otel fiyatları ve oda seçenekleri için Kaan Motel odalarını inceleyin. Standart, suit ve petsuit konaklama alternatifleri burada."
    )

    return render_template(
        "odalar.html",
        title=seo["title"],
        description=seo["description"],
        rooms=load_room_data_from_static()
    )


@app.route("/odalar/<room_id>")
def oda_detay(room_id):
    oda_verileri = load_room_data_from_static()
    room = next((r for r in oda_verileri if r["id"] == room_id), None)

    if room is None:
        abort(404)

    seo = build_seo(
        f"{room['name']} | Kaan Motel Avşa Adası",
        f"{room['name']} detaylarını inceleyin. {room['description']} Avşa'da konforlu konaklama için Kaan Motel oda seçeneklerini keşfedin."
    )

    return render_template(
        "oda_detay.html",
        title=seo["title"],
        description=seo["description"],
        room=room,
        gallery_items=room["gallery_images"]
    )


@app.route("/konum-iletisim")
def konum_iletisim():
    seo = build_seo(
        "Kaan Motel Konum ve İletişim | Avşa Adası",
        "Kaan Motel telefon, WhatsApp, e-posta ve konum bilgilerine ulaşın. Avşa Adası rezervasyon ve bilgi talepleriniz için bize kolayca ulaşabilirsiniz."
    )

    bilgiler = {
        "adres": CONTACT_INFO["address"],
        "telefon": CONTACT_INFO["phone"],
        "email": CONTACT_INFO["email"],
        "ulasim": "Avşa Adası iskelesine yaklaşık 15 dakikalık yürüyüş mesafesindedir.",
        "harita_iframe": (
            f'<iframe src="{CONTACT_INFO["maps_embed"]}" width="100%" height="420" '
            'style="border:0;" allowfullscreen="" loading="lazy" '
            'referrerpolicy="no-referrer-when-downgrade"></iframe>'
        ),
    }

    return render_template(
        "konum_iletisim.html",
        title=seo["title"],
        description=seo["description"],
        bilgiler=bilgiler
    )


@app.route("/rezervasyon", methods=["GET"])
def rezervasyon_formu():
    seo = build_seo(
        "Rezervasyon | Kaan Motel Avşa Adası",
        "Kaan Motel Avşa Adası rezervasyon formu ile hızlıca talep oluşturun. Avşa otelleri arasında konforlu bir konaklama için bize ulaşın."
    )

    return render_template(
        "rezervasyon_formu.html",
        title=seo["title"],
        description=seo["description"],
        rooms=load_room_data_from_static(),
        datetime=datetime,
        today=date.today().isoformat(),
    )


@app.route("/rezervasyon/yap", methods=["POST"])
def rezervasyon_yap():
    check_in_str = request.form.get("check_in")
    check_out_str = request.form.get("check_out")
    room_type_kod = request.form.get("room_type")
    guest_name = (request.form.get("guest_name") or "").strip()
    guest_email = (request.form.get("guest_email") or "").strip()
    guest_phone = (request.form.get("guest_phone") or "").strip()

    try:
        adults = int(request.form.get("adults", 1))
        children = int(request.form.get("children", 0))
    except ValueError:
        flash("Kişi sayısı geçersiz.", "danger")
        return redirect(url_for("index") + "#rezervasyon")

    if not all([check_in_str, check_out_str, room_type_kod, guest_name, guest_email]):
        flash("Lütfen zorunlu alanları eksiksiz doldurun.", "danger")
        return redirect(url_for("index") + "#rezervasyon")

    try:
        check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Tarih formatı geçersiz.", "danger")
        return redirect(url_for("index") + "#rezervasyon")

    is_available, result = check_availability(room_type_kod, check_in_str, check_out_str)

    if not is_available:
        flash(result, "danger")
        return redirect(url_for("index") + "#rezervasyon")

    available_room = result

    final_reservation_conflict = Reservation.query.filter(
        Reservation.room_id == available_room.id,
        Reservation.check_out > check_in_date,
        Reservation.check_in < check_out_date,
        Reservation.status.in_(["Yeni Talep", "Onaylandı", "Telefon Onaylı", "Giriş Yaptı"])
    ).first()

    if final_reservation_conflict:
        flash("Bu tarihlerde oda müsait değil.", "danger")
        return redirect(url_for("index") + "#rezervasyon")

    final_block_conflict = ManualBlock.query.filter(
        ManualBlock.room_id == available_room.id,
        ManualBlock.check_out > check_in_date,
        ManualBlock.check_in < check_out_date
    ).first()

    if final_block_conflict:
        flash("Bu tarihlerde oda müsait değil.", "danger")
        return redirect(url_for("index") + "#rezervasyon")

    total_price = calculate_total_price(room_type_kod, check_in_date, check_out_date)

    new_reservation = Reservation(
        guest_name=guest_name,
        guest_email=guest_email,
        guest_phone=guest_phone,
        check_in=check_in_date,
        check_out=check_out_date,
        adults=adults,
        children=children,
        room_id=available_room.id,
        status="Yeni Talep",
        source="Website",
        total_price=total_price
    )

    db.session.add(new_reservation)
    db.session.commit()

    flash(f"Rezervasyon talebiniz başarıyla alındı. Toplam fiyat: {total_price:,.0f} ₺", "success")
    return redirect(url_for("index") + "#rezervasyon")


@app.route("/yat-klubu")
def yat_klubu():
    seo = build_seo(
        "Kaan Motel Yat Kulübü | Avşa Adası",
        "Kaan Motel Yat Kulübü ile Avşa Adası'nda deniz keyfini farklı bir deneyime dönüştürün."
    )

    data = load_yat_kulubu_data()
    if data is None:
        flash("Yat Kulübü alanı şu anda hazır değil.", "warning")
        return redirect(url_for("index"))

    return render_template(
        "yat_kulubu_detay.html",
        title=seo["title"],
        description=seo["description"],
        data=data
    )


@app.route("/yonetim-giris", methods=["GET", "POST"])
def yonetim_login():
    seo = build_seo(
        "Yönetim Girişi | Kaan Motel",
        "Kaan Motel rezervasyon, blokaj ve fiyat yönetimi giriş ekranı."
    )

    if request.method == "POST":
        password = request.form.get("password", "")
        if password == app.config["MANAGER_PASSWORD"]:
            session["manager_logged_in"] = True
            flash("Yönetim paneline giriş yapıldı.", "success")
            return redirect(url_for("yonetim"))
        flash("Şifre hatalı.", "danger")

    return render_template(
        "yonetim_login.html",
        title=seo["title"],
        description=seo["description"]
    )


@app.route("/yonetim-cikis")
def yonetim_logout():
    session.pop("manager_logged_in", None)
    flash("Yönetim oturumu kapatıldı.", "info")
    return redirect(url_for("index"))


@app.route("/yonetim")
@manager_required
def yonetim():
    seo = build_seo(
        "Kaan Motel Yönetim Paneli",
        "Rezervasyon, blokaj ve fiyat yönetimi ekranı."
    )

    today_obj = date.today()
    try:
        selected_year = int(request.args.get("year", today_obj.year))
        selected_month = int(request.args.get("month", today_obj.month))
    except ValueError:
        selected_year = today_obj.year
        selected_month = today_obj.month

    if selected_month < 1 or selected_month > 12:
        selected_month = today_obj.month

    reservations = Reservation.query.order_by(Reservation.check_in.asc()).all()
    manual_blocks = ManualBlock.query.order_by(ManualBlock.check_in.asc()).all()
    price_rules = PriceRule.query.order_by(PriceRule.start_date.asc(), PriceRule.room_type.asc()).all()
    rooms = Room.query.order_by(Room.room_number.asc()).all()
    calendar_data = build_calendar_matrix(selected_year, selected_month)

    return render_template(
        "yonetim.html",
        title=seo["title"],
        description=seo["description"],
        reservations=reservations,
        manual_blocks=manual_blocks,
        price_rules=price_rules,
        rooms=rooms,
        source_options=SOURCE_OPTIONS,
        calendar_data=calendar_data,
        selected_year=selected_year,
        selected_month=selected_month,
        get_room_display_name=get_room_display_name,
        room_definitions=ROOM_DEFINITIONS
    )


@app.route("/yonetim/fiyat-ekle", methods=["POST"])
@manager_required
def yonetim_fiyat_ekle():
    room_type = normalize_room_type(request.form.get("room_type"))
    start_date_str = request.form.get("start_date")
    end_date_str = request.form.get("end_date")
    nightly_price_str = request.form.get("nightly_price")
    note = (request.form.get("note") or "").strip()

    if not room_type or not start_date_str or not end_date_str or not nightly_price_str:
        flash("Lütfen fiyat tanımı için tüm zorunlu alanları doldurun.", "danger")
        return redirect(url_for("yonetim"))

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        nightly_price = float(nightly_price_str)
    except ValueError:
        flash("Fiyat veya tarih formatı geçersiz.", "danger")
        return redirect(url_for("yonetim"))

    if end_date < start_date:
        flash("Bitiş tarihi başlangıç tarihinden önce olamaz.", "danger")
        return redirect(url_for("yonetim"))

    new_rule = PriceRule(
        room_type=room_type,
        start_date=start_date,
        end_date=end_date,
        nightly_price=nightly_price,
        note=note or None
    )
    db.session.add(new_rule)
    db.session.commit()

    flash("Fiyat kuralı başarıyla eklendi.", "success")
    return redirect(url_for("yonetim"))


@app.route("/yonetim/fiyat-sil/<int:rule_id>")
@manager_required
def yonetim_fiyat_sil(rule_id):
    rule = PriceRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    flash("Fiyat kuralı silindi.", "warning")
    return redirect(url_for("yonetim"))


@app.route("/yonetim/blok-ekle", methods=["POST"])
@manager_required
def yonetim_blok_ekle():
    guest_name = (request.form.get("guest_name") or "").strip()
    source = request.form.get("source") or "Diğer"
    check_in_str = request.form.get("check_in")
    check_out_str = request.form.get("check_out")
    room_id_raw = request.form.get("room_id")
    note = (request.form.get("note") or "").strip()
    is_full_hotel = request.form.get("is_full_hotel") == "on"

    if not check_in_str or not check_out_str:
        flash("Lütfen giriş ve çıkış tarihlerini girin.", "danger")
        return redirect(url_for("yonetim"))

    try:
        check_in_date = datetime.strptime(check_in_str, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Tarih formatı geçersiz.", "danger")
        return redirect(url_for("yonetim"))

    if check_in_date >= check_out_date:
        flash("Çıkış tarihi, giriş tarihinden sonra olmalıdır.", "danger")
        return redirect(url_for("yonetim"))

    room_id = None
    if not is_full_hotel:
        if not room_id_raw:
            flash("Tüm oteli kapatmıyorsanız oda seçmelisiniz.", "danger")
            return redirect(url_for("yonetim"))
        try:
            room_id = int(room_id_raw)
        except ValueError:
            flash("Geçersiz oda seçimi.", "danger")
            return redirect(url_for("yonetim"))

    if is_full_hotel:
        existing_full_hotel_block = ManualBlock.query.filter(
            ManualBlock.is_full_hotel.is_(True),
            ManualBlock.check_out > check_in_date,
            ManualBlock.check_in < check_out_date
        ).first()

        if existing_full_hotel_block:
            flash("Bu tarihlerde zaten tüm otel için bir blokaj bulunuyor.", "danger")
            return redirect(url_for("yonetim"))
    else:
        existing_reservation = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.check_out > check_in_date,
            Reservation.check_in < check_out_date,
            Reservation.status.in_(["Yeni Talep", "Onaylandı", "Telefon Onaylı", "Giriş Yaptı"])
        ).first()

        if existing_reservation:
            flash("Bu tarihlerde oda müsait değil.", "danger")
            return redirect(url_for("yonetim"))

        existing_block = ManualBlock.query.filter(
            ManualBlock.room_id == room_id,
            ManualBlock.check_out > check_in_date,
            ManualBlock.check_in < check_out_date
        ).first()

        if existing_block:
            flash("Bu tarihlerde oda müsait değil.", "danger")
            return redirect(url_for("yonetim"))

    new_block = ManualBlock(
        guest_name=guest_name or None,
        source=source,
        check_in=check_in_date,
        check_out=check_out_date,
        room_id=room_id,
        is_full_hotel=is_full_hotel,
        note=note or None
    )

    db.session.add(new_block)
    db.session.commit()

    flash("Blokaj / dış rezervasyon başarıyla eklendi.", "success")
    return redirect(url_for("yonetim"))


@app.route("/yonetim/blok-sil/<int:block_id>")
@manager_required
def yonetim_blok_sil(block_id):
    block = ManualBlock.query.get_or_404(block_id)
    db.session.delete(block)
    db.session.commit()
    flash("Blokaj kaydı silindi.", "warning")
    return redirect(url_for("yonetim"))


@app.route("/yonetim/rezervasyon-durum/<int:reservation_id>", methods=["POST"])
@manager_required
def yonetim_rezervasyon_durum(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    new_status = request.form.get("status", "").strip()

    allowed_statuses = [
        "Yeni Talep",
        "Onaylandı",
        "Telefon Onaylı",
        "Giriş Yaptı",
        "Tamamlandı",
        "İptal"
    ]

    if new_status not in allowed_statuses:
        flash("Geçersiz rezervasyon durumu.", "danger")
        return redirect(url_for("yonetim"))

    reservation.status = new_status
    db.session.commit()

    flash("Rezervasyon durumu güncellendi.", "success")
    return redirect(url_for("yonetim"))


@app.route("/robots.txt")
def robots_txt():
    robots_path = os.path.join(app.root_path, "static", "robots.txt")
    if os.path.exists(robots_path):
        with open(robots_path, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="text/plain")
    return Response("User-agent: *\nAllow: /\n", mimetype="text/plain")


@app.route("/sitemap.xml", methods=["GET"])
def sitemap():
    pages = []

    static_routes = [
        ("index", {}),
        ("galeri", {}),
        ("odalar", {}),
        ("konum_iletisim", {}),
        ("rezervasyon_formu", {}),
        ("yat_klubu", {}),
        ("kvkk", {}),
    ]

    today = date.today().isoformat()

    for route_name, params in static_routes:
        try:
            pages.append({
                "loc": url_for(route_name, _external=True, **params),
                "lastmod": today,
                "changefreq": "weekly",
                "priority": "0.8"
            })
        except Exception:
            pass

    try:
        oda_verileri = load_room_data_from_static()
        for room in oda_verileri:
            pages.append({
                "loc": url_for("oda_detay", room_id=room["id"], _external=True),
                "lastmod": today,
                "changefreq": "weekly",
                "priority": "0.7"
            })
    except Exception:
        pass

    xml = render_template("sitemap.xml", pages=pages)
    return Response(xml, mimetype="application/xml")

@app.route("/kvkk")
def kvkk():
    seo = build_seo(
        "KVKK | Kaan Motel",
        "Kaan Motel kişisel verilerin korunması ve aydınlatma metni bilgileri."
    )
    return render_template("kvkk.html", title=seo["title"], description=seo["description"])


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "404.html",
        title="Sayfa Bulunamadı | Kaan Motel",
        description="Aradığınız sayfa bulunamadı."
    ), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if Room.query.count() == 0:
            initial_rooms = [
                Room(room_number="STD01", room_type="standart", capacity=3),
                Room(room_number="STD02", room_type="standart", capacity=3),
                Room(room_number="STD03", room_type="standart", capacity=3),
                Room(room_number="STD04", room_type="standart", capacity=3),
                Room(room_number="SUI01", room_type="suit", capacity=5),
                Room(room_number="PET01", room_type="petsuit", capacity=4),
                Room(room_number="STD07", room_type="standart", capacity=3),
                Room(room_number="STD08", room_type="standart", capacity=3),
            ]
            db.session.add_all(initial_rooms)
            db.session.commit()
            print(f"✅ Başlangıç odaları oluşturuldu: {Room.query.count()} oda")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)