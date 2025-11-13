import os
from flask import abort
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import cast, Integer
from datetime import datetime
from flask_login import login_required, current_user
from markupsafe import Markup  # flask.Markup yerine

# Flask-Login ve diğer bağımlılıklar
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_
import calendar
import markdown
from sqlalchemy import UniqueConstraint

ROOM_DISPLAY_NAMES = {
    'STD01': 'Oda 1',
    'STD02': 'Oda 2',
    'STD03': 'Oda 3',
    'STD04': 'Oda 4',
    'SUI01': 'Suit',
    'PET01': 'Oda 7',
    'STD07': 'Oda 8',
    'LSU01': 'Üst Kat',
}

# --- UYGULAMA AYARLARI ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'maidekaan91'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sadakat.db'

# --- BLOG KLASÖRÜ ---
BLOG_DIR = os.path.join(app.root_path, 'blog_posts')
if not os.path.exists(BLOG_DIR):
    os.makedirs(BLOG_DIR)

# --- VERİTABANI ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- BLOG MODELİ ---
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Lütfen bu sayfaya erişmek için giriş yapınız."
login_manager.login_message_category = "warning"

# --- GENEL SABİT VERİLER ---

MOTEL_SLOGAN = "Kaan Motel: Avşa Adası'nda Huzurlu Kaçış Noktanız."
KVKK_TEXT = """
Kişisel Verilerin Korunması Kanunu (KVKK) gereğince, sitemizi kullanarak veya kayıt olarak bize sağladığınız kişisel verileriniz... (dsfdsbbcvcv)
"""

NAV_LINKS = [
    ('odalar', 'Odalar'),
    ('galeri', 'Galeri'),
    ('konum_iletisim', 'Konum & İletişim'),
    ('ada_rehberi', 'Ada Rehberi'),
    ('rezervasyon_formu', 'Rezervasyon Yap'), 
    ('profil', 'Profilim'),
    ('register', 'Kayıt Ol'),
]

# Odalar Sayfası Verileri
ODALAR = [
    {'kod': 'largesuit', 'ad': '3 Kişilik Standart Oda', 'vurgu': 'Otelimizin En Lüks ve Manzaralı Süiti', 'ozellikler': ['Özel Teras', 'Ekstra Büyük Oda', 'Tam Donanımlı Mutfak', 'Klima'], 'fiyat': 'Mevsime Göre Değişir', 'gorsel': 'suit_buyuk.jpg'},
    {'kod': 'suit', 'ad': '5 Kişilik Suit Oda', 'vurgu': 'Romantik Kaçışlar İçin İdeal', 'ozellikler': ['Geniş Yaşam Alanı', 'Deniz Manzaralı Balkon', 'Mini Mutfak', 'Klima'], 'fiyat': 'Mevsime Göre Değişir', 'gorsel': 'suit_deluxe.jpg'},
    {'kod': 'petsuit', 'ad': 'Pet Dostu Aile Odası', 'vurgu': 'Patili Dostunuzla Birlikte Huzurlu Tatil', 'ozellikler': ['4 Yatak', 'Geniş Oda', 'Özel Giriş', 'Mama/Su Kabı Seti', 'Klima'], 'fiyat': 'Mevsime Göre Değişir', 'gorsel': 'pet_dostu.jpg'}
   ]

# Oda kodlarını formu doldurmak için hazırlıyoruz
ODA_TIPLERI_DICT = {oda['kod']: oda['ad'] for oda in ODALAR}

# KULLANICI İSTEĞİNE ÖZEL TAKVİM GÖRÜNÜM İSİMLENDİRMESİ (KESİN LİSTE)
CUSTOM_CALENDAR_NAMES = [
    "Oda 1",
    "Oda 2",
    "Oda 3",
    "Oda 4",
    "Suit", 
    "Oda 7",
    "Oda 8",
    "Üst Kat"
]
# TOPLAM 8 ODA VARSA BU LİSTEDE 8 İSİM OLMALIDIR.

# --- VERİTABANI MODELLERİ (Tablo Tanımları) ---

# Kullanıcı/Sadakat Modeli 
# --- TEMİZLENMİŞ VE BİRLEŞTİRİLMİŞ MODELLER ---

# --- VERİTABANI MODELLERİ (Tablo Tanımları) ---

# --- MODEL SIRALAMASI DÜZELTİLDİ: İlişki Kurulan Sınıflar, User Sınıfından ÖNCE TANIMLANDI ---

# GÖREV TANIM MODELİ
# GÖREV TANIM MODELİ
class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    points_reward = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False, default='REZERVASYON')
    is_repeatable = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Mission {self.title}>'


# GÖREV TAMAMLAMA MODELİ (UserTask'ın yeni adı UserMission)
class UserMission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey('mission.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_validated = db.Column(db.Boolean, default=False)
    proof_data = db.Column(db.String(500), nullable=True)

    __tablename__ = 'user_mission_completion'

    # Backref çakışmasını önlemek için sadece relationship kullanıldı. 'user' referansı User modelinde ayarlanacak.
    user = db.relationship('User', backref='mission_links') 
    mission = db.relationship('Mission', backref=db.backref('completions', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'mission_id', name='_user_mission_uc'),
    )

    def __repr__(self):
        return f'<UserMission User:{self.user_id} Mission:{self.mission_id}>'

# ÖDÜL TALEP MODELİ (ClaimedReward yerine Redemption kullanıldı)
class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey('reward.id'), nullable=False)
    redemption_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Beklemede')
    points_used = db.Column(db.Integer, nullable=False) 
    
    # Backref çakışmasını önlemek için sadece relationship kullanıldı.
    user = db.relationship('User', backref='rewards_redeemed')
    reward = db.relationship('Reward', backref=db.backref('redemptions', lazy=True))
    
    def __repr__(self):
        return f'<Redemption User:{self.user_id} Reward:{self.reward_id}>'


# KULLANICI/SADAKAT MODELİ (İlişki Modellerinden SONRA TANIMLANDI)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # --- İSİM/SOYİSİM ALANLARI (DÜZELTİLDİ) ---
    first_name = db.Column(db.String(64)) 
    last_name = db.Column(db.String(64))
    # -------------------------------------------
    
    total_points = db.Column(db.Integer, default=0, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    kvkk_consent = db.Column(db.Boolean, default=False, nullable=False)
    
    # İlişkiler: backref parametresi çakışmayı önlemek için KALDIRILDI
    tasks = db.relationship('UserMission', lazy='dynamic') 
    rewards_claimed = db.relationship('Redemption', lazy='dynamic')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        if self.first_name and self.last_name:
            return f'<User {self.username} ({self.first_name} {self.last_name})>'
        return f'<User {self.username}>'

def load_room_data_from_static():
    """/static/rooms/ altındaki klasörleri okuyarak oda verilerini otomatik oluşturur."""
    room_data = []
    base_room_path = os.path.join(app.root_path, 'static', 'rooms')

    if not os.path.exists(base_room_path):
        return []

    # Klasörleri (odaların ID'lerini) oku
    for room_id in os.listdir(base_room_path):
        room_dir = os.path.join(base_room_path, room_id)

        if os.path.isdir(room_dir):
            # Oda bilgilerini tanımla
            if room_id == 'standart':
                room_name = '3 Kişilik Standart Oda'
                room_desc = 'Konforlu, ferah ve kullanışlı standart odamız.'
                room_long_desc = 'Uygun fiyatlı konaklama arayanlar için idealdir.'
                price = 1500
                capacity = 3
            elif room_id == 'suit':
                room_name = '5 Kişilik Suit Oda'
                room_desc = 'Geniş aileler için tasarlanmış lüks suit.'
                room_long_desc = 'İki ayrı bölümlü geniş yaşam alanı sunar.'
                price = 2800
                capacity = 5
            elif room_id == 'pet-dostu':
                room_name = 'Pet Dostu Oda'
                room_desc = 'Patili dostuyla tatil yapmak isteyen misafirlerimiz için özel oda.'
                room_long_desc = (
                    "Kaan Motel olarak, evcil hayvanlarıyla tatil yapmak isteyen misafirlerimiz için "
                    "özel olarak hazırladığımız Pet Dostu Oda seçeneğimizde konforlu bir konaklama deneyimi sunuyoruz. "
                    "Odamız 4 kişiliktir ve evcil dostlarınız için özel mama kabı, yatak ve güvenli alan bulunmaktadır."
                )
                price = 1500
                capacity = 4
            else:
                continue  # Tanımlı olmayan klasörleri atla

            # Klasördeki dosyaları oku
            files = os.listdir(room_dir)
            files.sort()  # Dosyaları alfabetik sırala

            gallery_images = []
            main_image_path = None

            for filename in files:
                if filename.lower() in ['main.jpg', 'main.png']:
                    main_image_path = url_for('static', filename=f'rooms/{room_id}/{filename}')
                elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    gallery_images.append({
                        'title': f"{room_name} Görsel {len(gallery_images) + 1}",
                        'path': url_for('static', filename=f'rooms/{room_id}/{filename}')
                    })





            # ODA VERİSİNİ OLUŞTUR
            if main_image_path: # Ana görsel varsa odayı listeye ekle
                room_data.append({
                    'id': room_id,
                    'name': room_name,
                    'description': room_desc,
                    'long_description': room_long_desc,
                    'price_per_night': price,
                    'capacity': capacity,
                    'main_image': main_image_path,
                    'gallery_images': gallery_images
                })
                
    return room_data
# ÖDÜL TANIM MODELİ
class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    points_cost = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Reward {self.title}>'

# KAMPANYA MODELİ
class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Campaign {self.title}>"

# ODA MODELİ
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, default=2)
    reservations = db.relationship('Reservation', backref='room_details', lazy=True)

    def __repr__(self):
        return f'<Room {self.room_number} - {self.room_type}>'

# REZERVASYON MODELİ
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_email = db.Column(db.String(120), nullable=False)
    guest_phone = db.Column(db.String(20))
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    adults = db.Column(db.Integer, default=1)
    children = db.Column(db.Integer, default=0)
    total_price = db.Column(db.Float, default=0.0)
    
    # DÜZELTİLDİ: nullable=True yapılarak Yat Kulübü (NULL) kayıtlarına izin verildi.
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True) 
    
    status = db.Column(db.String(20), default='Online Onay Bekliyor')
    loyalty_points_awarded = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Reservation {self.id} | Oda: {self.room_id}>'

# --- MODELLER SONU ---
# --- YENİ OTOMATİK GALERİ YÜKLEME FONKSİYONU ---
def get_gallery_items():
    """Static/gallery klasöründeki tüm resimleri otomatik olarak yükler."""
    gallery_list = []
    
    # Flask'ın statik klasörünün gerçek yolunu bulur
    static_folder_path = os.path.join(app.root_path, 'static', 'gallery') 
    
    if not os.path.exists(static_folder_path):
        return []

    # Klasördeki dosyaları listeler
    for filename in os.listdir(static_folder_path):
        # Sadece resim dosyalarını dahil eder
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            gallery_list.append({
                # Dosya adından başlık oluşturur
                'title': filename.replace('_', ' ').title().rsplit('.', 1)[0], 
                'description': f'Avşa Adası hatırası: {filename}.',
                # Flask'ın URL oluşturma yolu
                'path': url_for('static', filename=f'gallery/{filename}')
            })
            
    gallery_list.sort(key=lambda x: x['title'])
    
    return gallery_list
# app.py'de get_gallery_items fonksiyonunun hemen altına ekleyin

def get_oda_verileri():
    """Odaların verilerini url_for kullanarak dinamik olarak döndürür."""
    # BURADAKİ KOD BLOKLARI ARTIK BİR FONKSİYON İÇİNDE OLDUĞU İÇİN 
    # UYGULAMA BAĞLAMI HATASI VERMEYECEKTİR.
    return [
        {
            'id': 'standart', 
            'name': '3 Kişilik Standart Oda',
            'description': 'Konforlu ve ferah bir standart oda.',
            'long_description': '3 Kişilik Standart Odalarımız...',
            'price_per_night': 1500,
            'capacity': 3,
            # url_for kullanımı ARTIK FONKSİYON İÇİNDE GÜVENLİDİR
            'main_image': url_for('static', filename='gallery/goruntu_standart_1.jpg'), 
            'gallery_images': [ 
                {'title': 'Oda İçi Görünüm', 'path': url_for('static', filename='gallery/goruntu_standart_1.jpg')},
                {'title': 'Banyo', 'path': url_for('static', filename='gallery/goruntu_standart_2.jpg')},
                {'title': 'Balkon Manzarası', 'path': url_for('static', filename='gallery/goruntu_standart_3.jpg')}
            ]
        },
        {
            'id': 'suit',
            'name': '5 Kişilik Suit Oda',
            'description': 'Geniş aileler için iki ayrı bölümlü lüks suit.',
            'long_description': '5 Kişilik Suit Odalarımız...',
            'price_per_night': 2800,
            'capacity': 5,
            'main_image': url_for('static', filename='gallery/goruntu_suit_1.jpg'), 
            'gallery_images': [
                {'title': 'Oturma Alanı', 'path': url_for('static', filename='gallery/goruntu_suit_1.jpg')},
                {'title': 'Ebeveyn Odası', 'path': url_for('static', filename='gallery/goruntu_suit_2.jpg')},
                {'title': 'Geniş Balkon', 'path': url_for('static', filename='gallery/goruntu_suit_3.jpg')}
            ]
        }
    ]

# ... get_gallery_items fonksiyonu devam ediyor

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- REZERVASYON MANTIK FONKSİYONU ---

def check_availability(room_type_kod, check_in_date_str, check_out_date_str):
    """
    Belirtilen tarihlerde ve oda tipinde müsait oda olup olmadığını kontrol eder ve müsait odayı döndürür.
    """
    # 1. Tarih Formatlarını Ayarlama
    try:
        check_in = datetime.strptime(check_in_date_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date_str, '%Y-%m-%d').date()
    except ValueError:
        return False, "Hata: Tarih formatı yanlış."

    if check_in >= check_out:
        return False, "Hata: Çıkış tarihi, giriş tarihinden sonra olmalıdır."
    if check_in < date.today():
        return False, "Hata: Geçmiş bir tarih seçilemez."
    
    # 2. İstenen Oda Tipindeki Tüm Odaları Bul
    all_rooms_of_type = Room.query.filter_by(room_type=room_type_kod).all()
    if not all_rooms_of_type:
        return False, "Hata: İstenen oda tipi bulunamadı."
        
    # 3. Rezervasyon çakışması olan odaları bulma (Yalnızca onaylı/dolu rezervasyonları kontrol et)
    clashing_reservations = Reservation.query.filter(
        Reservation.room_id.in_([r.id for r in all_rooms_of_type]),
        and_(
            Reservation.check_out > check_in, 
            Reservation.check_in < check_out, 
            or_(
                Reservation.status == 'Onaylandı',
                Reservation.status == 'Telefon Onaylı',
                Reservation.status == 'Giriş Yaptı'
            )
        )
    ).all()
    
    # 4. Müsait Oda ID'sini bulma
    booked_rooms_ids = {r.room_id for r in clashing_reservations}
    available_room = None
    
    for room in all_rooms_of_type:
        if room.id not in booked_rooms_ids:
            available_room = room
            break
            
    if available_room:
        return True, available_room
    else:
        return False, f"Üzgünüz, {ODA_TIPLERI_DICT.get(room_type_kod, room_type_kod)} tipinde bu tarihlerde oda kalmadı."


# --- ZİYARETÇİ ROTALARI (URL Tanımları) ---

# app.py dosyanızdaki ZİYARETÇİ ROTALARI bloğuna ekleyin

def get_oda_verileri():
    """Odaların verilerini url_for kullanarak dinamik olarak döndürür."""
    return [
        {
            'id': 'standart',
            'name': '3 Kişilik Standart Oda',
            'description': 'Konforlu, ferah ve kullanışlı standart odamız. Uygun fiyatlı konaklama arayanlar için idealdir.',
            'long_description': 'Standart odamız, sade tasarımı ve konforlu donanımıyla misafirlerimize huzurlu bir konaklama deneyimi sunar. Balkonlu ve ferah bir yapıya sahiptir.',
            'price_per_night': 1500,
            'capacity': 3,
            'main_image': url_for('static', filename='gallery/goruntu_standart_1.jpg'),
            'gallery_images': [
                {'title': 'Oda İçi Görünüm', 'path': url_for('static', filename='gallery/goruntu_standart_1.jpg')},
                {'title': 'Banyo', 'path': url_for('static', filename='gallery/goruntu_standart_2.jpg')},
                {'title': 'Balkon Manzarası', 'path': url_for('static', filename='gallery/goruntu_standart_3.jpg')}
            ]
        },
        {
            'id': 'suit',
            'name': '5 Kişilik Suit Oda',
            'description': 'Geniş aileler ve kalabalık gruplar için tasarlanmış, iki ayrı bölümlü lüks suitimiz.',
            'long_description': 'Suit odamız, geniş oturma alanı, ayrı yatak odası ve ferah balkonuyla kalabalık aileler için mükemmel bir seçenektir.',
            'price_per_night': 2800,
            'capacity': 5,
            'main_image': url_for('static', filename='gallery/goruntu_suit_1.jpg'),
            'gallery_images': [
                {'title': 'Oturma Alanı', 'path': url_for('static', filename='gallery/goruntu_suit_1.jpg')},
                {'title': 'Ebeveyn Odası', 'path': url_for('static', filename='gallery/goruntu_suit_2.jpg')},
                {'title': 'Geniş Balkon', 'path': url_for('static', filename='gallery/goruntu_suit_3.jpg')}
            ]
        },
        {
            'id': 'pet-dostu',
            'name': 'Pet Dostu Oda',
            'description': 'Patili dostuyla tatil yapmak isteyen misafirlerimiz için özel olarak tasarlandı.',
            'long_description': """Kaan Motel olarak, evcil hayvanlarıyla tatil yapmak isteyen misafirlerimiz için özel olarak hazırladığımız Pet Dostu Oda seçeneğimizde konforlu bir konaklama deneyimi sunuyoruz. 
Odamız, 4 kişilik kapasitesiyle hem aileler hem de dostlarıyla birlikte seyahat eden misafirlerimiz için idealdir. 
Evcil dostlarınız için özel mama kabı, yatak ve güvenli alan bulunmaktadır.""",
            'price_per_night': 1500,
            'capacity': 4,
            'main_image': url_for('static', filename='gallery/pet_dostu_1.jpg'),
            'gallery_images': [
                {'title': 'Pet Dostu Oda', 'path': url_for('static', filename='gallery/pet_dostu_1.jpg')},
                {'title': 'Oda Detayı', 'path': url_for('static', filename='gallery/pet_dostu_2.jpg')},
                {'title': 'Evcil Dost Alanı', 'path': url_for('static', filename='gallery/pet_dostu_3.jpg')}
            ]
        }
    ]

 



       
    
# --- ADA REHBERİ VERİLERİ (app.py içine ekleyin) ---
ADA_REHBERI_YERI = [
    {
        'id': 'altinkum',
        'ad': 'Altınkum Plajı',
        'aciklama': 'Masmavi denizi, yumuşacık altın rengi kumları ve gün batımında içten içe parlayan sahiliyle Altınkum… Avşa’nın en huzurlu ve keyifli duraklarından biri. Burada deniz sığ ve tertemiz; upuzun sahilde yürüyüp, şezlonga uzanıp, güneşi iliklerine kadar hissedebilirsin. İster sakin bir gün, ister müzik eşliğinde eğlence… Altınkum’da her ruh haline uygun bir köşe mutlaka var. Giden bilir: Bir kez gelince tekrar gelmek istersin.',
        'gorsel_path': 'ada_rehberi/altinkum.jpg', # static/ada_rehberi/altinkum.jpg
    },
    {
        'id': 'manastir',
        'ad': 'Tarihi Manastır Kalıntıları',
        'aciklama': 'Sessizliğin, denizin ve tarihin birbirine karıştığı huzurlu bir köşe: Manastır Koyu. Adını yüzyıllar önce burada bulunan eski bir manastırdan alıyor. Bugün geriye taş duvar izleri ve çokça sakinlik kalmış… Denizi tertemiz, kıyısı daha doğal ve kalabalıktan uzak. Dalga sesi eşliğinde günü yavaşlatmak isteyenlere birebir. Yanına kitap, güneş kremi ve huzur taşı; burada zaman biraz daha ağır akar.',
        'gorsel_path': 'ada_rehberi/manastir.jpg', # static/ada_rehberi/manastir.jpg
    },
    {
        'id': 'Mavikoy',
        'ad': 'Mavikoy Akvaryum Koyu',
        'aciklama': 'Adı gibi MASMAVİ… Doğanın kendi filtresiyle boyadığı, berraklığıyla içini ferahlatan bir koy burası. Kayalıkların arasında saklanan bu koy, sakinlik arayanlara gizli bir kaçış gibi. Deniz o kadar temiz ki, suyun içindeki her ayrıntıyı görebiliyorsun. Geldiğinde sadece denize değil, kendine de dalıyorsun aslında.',
        'gorsel_path': 'ada_rehberi/buyukliman.jpg', # static/ada_rehberi/buyukliman.jpg
    },
{
        'id': 'sarap', # Sadece tanımlayıcı, küçük ve İngilizce benzeri bir isim verin.
        'ad': 'Şarap Fabrikası ve Üzüm Bağları', # Sayfada görünecek Türkçe isim.
        'aciklama': 'Adanın kalbi sadece denizde değil; güneşte olgunlaşan üzüm kokusunda saklı. Yamaçlarda sıralanan bağların arasında gezerken, rüzgar yaprakların arasından usulca konuşur sanki. Avşa’nın şarap kültürü de buradan doğuyor; her üzüm tanesi güneşten bir parça, adadan bir hatıra taşıyor. Huzur isteyenlere “gel biraz soluklan” diyen, yavaş yavaş yaşayan bir dünya. Avşa’nın ruhu sadece sahillerde değil; mahzenlerde saklı. Yılların biriktirdiği şarap kültürü, adanın güneşini ve rüzgarını kendi dilince anlatıyor burada. Tadım masalarında her kadeh bir hikaye… Üzümler bağdan gelir, ama şarap kupaya zarafet olarak dökülür. Rahat, sakin ve seçkin bir atmosfer. Damakta hafif bir meyve ve yaz hatırası…',
        # Adım A'da yüklediğiniz ve isimlendirdiğiniz görselin yolunu buraya yazın.
        'gorsel_path': 'ada_rehberi/sarap.jpg', 
    },
{
        'id': 'disco', # Sadece tanımlayıcı, küçük ve İngilizce benzeri bir isim verin.
        'ad': 'Gece Kulüpleri', # Sayfada görünecek Türkçe isim.
        'aciklama': ' Ada geceleri burada başka parlar. Şık atmosfer, kaliteli müzik ve yaz akşamının hafif rüzgarı… Avşa’nın seçkin beach & club mekanlarında gece, güneş battıktan sonra asıl ritmini bulur. Loş ışıklar, denizin üstünde yansıyan city-chic bir enerji ve uzun sohbetlerin eşlik ettiği zarif bir gece akışı… Sessiz değil; ama gereksiz kalabalık da değil. Tam kararında. Tam senin gibi.',
        # Adım A'da yüklediğiniz ve isimlendirdiğiniz görselin yolunu buraya yazın.
        'gorsel_path': 'ada_rehberi/disco.jpg', 
    },
]
# ----------------------------------------------------
@app.route('/blog')
def blog_list():
    posts = []
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith('.md'):
            slug = filename[:-3]  # .md uzantısını kaldır
            filepath = os.path.join(BLOG_DIR, filename)
            created_at = datetime.fromtimestamp(os.path.getmtime(filepath))  # dosyanın oluşturulma/değişme zamanı
            with open(filepath, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
            posts.append({
                'title': first_line.replace('#', '').strip(),
                'slug': slug,
                'created_at': created_at
            })
    # Tarihe göre sıralama (en yeni önce)
    posts.sort(key=lambda x: x['created_at'], reverse=True)
    return render_template('blog_list.html', posts=posts)



@app.route('/blog/<slug>')
def blog_post(slug):
    filepath = os.path.join(BLOG_DIR, slug + '.md')
    if not os.path.exists(filepath):
        abort(404)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    title = lines[0].replace('#', '').strip() if lines else 'Başlıksız'
    content = ''.join(lines[1:]).strip() if len(lines) > 1 else ''
    created_at = datetime.fromtimestamp(os.path.getmtime(filepath))  # Burayı ekledik

    post = {
        'title': title,
        'content': content,
        'slug': slug,
        'created_at': created_at  # Burayı mutlaka gönder
    }
    
    return render_template('blog_post.html', post=post)



@app.route('/admin/delete_mission/<int:mission_id>', methods=['GET'])
@login_required
def delete_mission(mission_id):
    if not current_user.is_admin:
        flash("Bu işlem için yetkiniz yok.", "danger")
        return redirect(url_for('admin_dashboard'))
    
    mission = Mission.query.get_or_404(mission_id)
    
    # Kullanıcı görev kayıtlarını da sil
    UserMission.query.filter_by(mission_id=mission_id).delete()
    
    db.session.delete(mission)
    db.session.commit()
    
    flash(f"'{mission.title}' görevi başarıyla silindi.", "success")
    return redirect(url_for('admin_dashboard') + '#missions-management')

@app.route('/admin/blog', methods=['GET', 'POST'])
@login_required
def admin_blog():
    if not current_user.is_admin:
        flash("Bu sayfaya erişim yetkiniz yok!", "danger")
        return redirect(url_for('index'))

    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin_blog.html', posts=posts)
@app.route('/admin/blog/new', methods=['GET', 'POST'])
@login_required
def new_blog_post():
    if not current_user.is_admin:
        flash("Bu sayfaya erişim yetkiniz yok!", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        slug = title.lower().replace(" ", "-")  # basit slug
        post = BlogPost(title=title, content=content, slug=slug, author_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash("Yeni blog yazısı eklendi!", "success")
        return redirect(url_for('admin_blog'))

    return render_template('new_blog_post.html')

@app.route('/blog')
def blog_index():
    posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).all()
    return render_template('blog_index.html', posts=posts)

@app.route('/blog/<slug>')
def blog_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('blog_detail.html', post=post)


@app.route("/etkinlik1")
def etkinlik1():
    return render_template("etkinlik1.html")

@app.route("/etkinlik2")
def etkinlik2():
    return render_template("etkinlik2.html")

@app.route('/kvkk')
def kvkk_metni():
    # 'kvkk.html' dosyasını render eder
    return render_template('kvkk.html')
@app.route('/yat-klubu')
def yat_klubu():
    """Kaan Motel Yat Kulübü detay sayfasını yükler."""
    
    # Otomatik görsel yükleme fonksiyonunu çağırıyoruz
    yat_klubu_data = load_yat_kulubu_data() 
    
    if yat_klubu_data is None:
        # Eğer load_yat_kulubu_data None döndürdüyse (klasör/görsel bulunamadıysa)
        # Not: hata.html dosyanızın mevcut olduğundan emin olun, yoksa başka bir hata alırsınız.
        return render_template('hata.html', message="Yat Kulübü bilgileri yüklenemedi. Lütfen klasör yapısını ve görsellerin adını (main.jpg/png) kontrol ediniz.")
    
    # Veri başarıyla yüklendiyse, şablonu çağır
    return render_template('yat_kulubu_detay.html', data=yat_klubu_data)
def load_yat_kulubu_data():
    """/static/rooms/yat_kulubu/ klasörünü okuyarak Yat Kulübü verilerini oluşturur."""
    
    room_id = 'yat_kulubu'
    # app nesnesine ve root_path'e erişim sağlanıyor
    base_room_path = os.path.join(app.root_path, 'static', 'rooms', room_id)
    
    if not os.path.isdir(base_room_path):
        print(f"HATA: Yat Kulübü klasörü bulunamadı: {base_room_path}") # Hata ayıklama için
        return None 

    files = os.listdir(base_room_path)
    files.sort() 
    
    gallery_images = []
    main_image_path = None
    
    for filename in files:
        # Uzantı kontrolünü daha genel hale getiriyoruz
        ext = filename.lower().rsplit('.', 1)[-1]
        if ext in ('png', 'jpg', 'jpeg'):
            
            full_file_path = os.path.join(base_room_path, filename)

            if filename.lower() == 'main.jpg' or filename.lower() == 'main.png':
                # Ana görseli belirle
                main_image_path = url_for('static', filename=f'rooms/{room_id}/{filename}')
            
            # Galeri görsellerini ekle (main.jpg/png galeride de yer alabilir, bu sorun değil)
            gallery_images.append({
                'title': f"Yat Kulübü Görsel {len(gallery_images) + 1}",
                'path': url_for('static', filename=f'rooms/{room_id}/{filename}')
            })

    # Eğer ana görsel bulunamazsa (main.jpg yoksa) galerideki ilk görseli ana görsel yapalım
    if not main_image_path and gallery_images:
        main_image_path = gallery_images[0]['path']
        
    if not main_image_path:
        print(f"HATA: Yat Kulübü klasöründe okunabilir resim dosyası bulunamadı: {base_room_path}") # Hata ayıklama için
        return None # Hiç görsel yoksa

    # YAT KULÜBÜ SABİT METİNLERİ BURADA TANIMLANIR
    yat_data = {
        'title': 'Kaan Motel Yat Kulübü',
        'description': 'Motelimizin misafirlerine özel olarak sunduğu ayrıcalıklı denizcilik deneyimi.',
        'long_text': 'Yat Kulübümüz, misafirlerimize sadece konaklama değil, aynı zamanda unutulmaz deniz maceraları sunmak amacıyla kurulmuştur. Tekne turları, dalış aktiviteleri, yelken dersleri ve özel yat kiralama hizmetlerimiz mevcuttur. Denizle iç içe bir tatil arayanlar için idealdir. Güvenli ve deneyimli kaptanlarımız eşliğinde bölgenin en güzel koylarını keşfedin.',
        'image_path': main_image_path,
        'gallery_images': gallery_images 
    }
    
    return yat_data
# Yeni sayfa görüntülenecek
@app.route('/rezervasyon/yat-kulubu')
def yat_kulubu_form():
    # datetime, title değişkenlerini render_template'e geçirmeyi unutmayın
    return render_template('yacht_club_reservation.html', title="Yat Kulübü Rezervasyon", datetime=datetime)

# Yeni form gönderimini işleyecek
@app.route('/rezervasyon/yat-kulubu/submit', methods=['POST'])
def yacht_club_submit():
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')
    guest_name = request.form.get('guest_name')
    guest_email = request.form.get('guest_email')
    guest_phone = request.form.get('guest_phone')
    
    try:
        check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Hata: Tarih formatı geçersiz.', 'danger')
        return redirect(url_for('yat_kulubu_form'))

    # --- YAT KULÜBÜ KAYIT İŞLEMİ ---
    try:
        # room_id=None olacak. Zorunlu alanlar için varsayılan değerler verilmeli (Aşama 1'e göre)
        new_reservation = Reservation(
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            check_in=check_in_date,
            check_out=check_out_date,
            adults=0, # Yat Kulübü formunda kişi sayısı almadık, varsayılan 0 veya 1 yapın
            children=0,
            room_id=None, # Kesinlikle NULL olmalı
            total_price=0.0, # Modelden gelen zorunlu alan
            loyalty_points_awarded=0, # Modelden gelen zorunlu alan
            status='Yat Kulübü Talebi (Admin Bekliyor)' # Farklı bir başlangıç durumu
        )
        
        db.session.add(new_reservation)
        db.session.commit()

        flash('Yat Kulübü rezervasyon talebiniz başarıyla alındı. Yönetici onayı bekleniyor.', 'success')
        return redirect(url_for('yat_kulubu_form')) # Kendi sayfasına geri dön

    except Exception:
        # Bu hata, modelde eksik bir alan varsa tekrar çıkar (Aşama 1'i atladıysanız)
        flash('Rezervasyon kaydedilirken veritabanı hatası oluştu. Lütfen site yöneticisiyle iletişime geçin.', 'danger')
        return redirect(url_for('yat_kulubu_form'))

@app.route('/forgot-username', methods=['GET', 'POST'])
def forgot_username():
    return render_template('forgot_username.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # Burada formu gösterebilir veya şifre sıfırlama işlemlerini yapabilirsin
    return render_template('forgot_password.html')

@app.route('/ada-rehberi')
def ada_rehberi():
    
    # 1. URL'leri içeren listeyi oluştur
    rehber_listesi = []
    for yer in ADA_REHBERI_YERI:
        # Flask'ın url_for fonksiyonu ile görselin statik URL'sini oluştur
        gorsel_url = url_for('static', filename=yer['gorsel_path']) 
        
        # Yeni bir dictionary oluşturup listeye ekle
        rehber_listesi.append({
            'id': yer['id'],
            'ad': yer['ad'],
            'aciklama': yer['aciklama'],
            'gorsel_url': gorsel_url # HTML şablonunda kullanılacak URL
        })
    
    return render_template(
        'ada_rehberi.html',
        title="Avşa Adası Rehberi",
        nav_links=NAV_LINKS,
        rehber_listesi=rehber_listesi # Yeni veri listesini şablona gönderiyoruz
    )
@app.route('/galeri')
def galeri():
    
    # 🚨 Yeni sistem: Listeyi fonksiyon otomatik oluşturuyor.
    gallery_items = get_gallery_items() 
    
    return render_template(
        'galeri.html', 
        gallery_items=gallery_items,
        current_user=current_user
    )
@app.route('/')
def index():
    return render_template('index.html', slogan=MOTEL_SLOGAN, nav_links=NAV_LINKS)

# app.py içinde /odalar rotasının üstüne veya uygun bir yere ekleyin


@app.route('/odalar')
def odalar():
    # Yeni fonksiyonu kullanarak veriyi al
    oda_listesi = load_room_data_from_static() 
    return render_template('odalar.html', rooms=oda_listesi)

@app.route('/odalar/<room_id>')
def oda_detay(room_id):
    # Yeni fonksiyonu kullanarak veriyi al
    oda_verileri = load_room_data_from_static()
    
    # Oda verilerini bul
    room = next((r for r in oda_verileri if r['id'] == room_id), None)
    
    if room is None:
        abort(404)
        
    return render_template('oda_detay.html', room=room, gallery_items=room['gallery_images'])
@app.route('/konum-iletisim')
def konum_iletisim():
    ILETISIM_BILGILERI = {
        'adres': 'Deniz Mahallesi, Değirmenardı Mevkii, Zafer Sokak no:6 Avşa',
        'telefon': '+90 5538898544',
        'email': 'avsakaanmotel@gmail.com',
        'ulasim': 'Avşa Adası İskelesine 15 dakikalık yürüyüş mesafesinde.',
        'harita_iframe': '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3032.958911929898!2d27.495157275155798!3d40.520399249324505!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x14b419000f224301%3A0x4e6d88d0246a0cb6!2sKaan%20Motel!5e0!3m2!1str!2str!4v1760429758683!5m2!1str!2str" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>'
    }
    return render_template('konum_iletisim.html', title="Konum ve İletişim", nav_links=NAV_LINKS, bilgiler=ILETISIM_BILGILERI)


@app.route('/rezervasyon', methods=['GET'])
def rezervasyon_formu():
    oda_listesi = load_room_data_from_static() # Yeni fonksiyon (veya odaların geldiği fonksiyon) çağrılmalı
    
    return render_template('rezervasyon_formu.html', 
                           title="Online Rezervasyon", 
                           nav_links=NAV_LINKS, 
                           rooms=oda_listesi, # <-- BURADA rooms olarak gönderilmeli
                           datetime=datetime)


# --- ODA BAZLI TAKVİM API ROTASI (ÇALIŞAN VERSİYON) ---
@app.route('/api/takvim-doluluk-oda/<int:year>/<int:month>')
def takvim_doluluk_oda_api(year, month):
    """
    Belirtilen yıl ve ay için her bir Room (oda) bazında günlük doluluk takvimini döndürür.
    """
    try:
        from datetime import date, timedelta
        import calendar
        from sqlalchemy import or_, cast
        from sqlalchemy.types import Integer
        
        start_date = date(year, month, 1)
    except ValueError:
        return jsonify({"error": "Geçersiz yıl veya ay."}), 400

    # Ayın son gününü bulma
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    num_days = calendar.monthrange(year, month)[1]

    # Tüm odaları doğru şekilde numerik sıralayalım
    tum_odalar = Room.query.order_by(cast(Room.room_number, Integer)).all()

    # Çakışan rezervasyonları tek sorguda al
    clashing_reservations = Reservation.query.filter(
        Reservation.room_id.in_([r.id for r in tum_odalar]),
        Reservation.check_out > start_date,
        Reservation.check_in <= end_date,
        or_(
            Reservation.status == 'Onaylandı',
            Reservation.status == 'Telefon Onaylı',
            Reservation.status == 'Giriş Yaptı'
        )
    ).all()

    result = []

    for index, oda in enumerate(tum_odalar):
        # CUSTOM_CALENDAR_NAMES varsa ona göre isim ver, yoksa ROOM_DISPLAY_NAMES
        if index < len(CUSTOM_CALENDAR_NAMES):
            gorunur_oda_adi = CUSTOM_CALENDAR_NAMES[index]
        else:
            gorunur_oda_adi = ROOM_DISPLAY_NAMES.get(oda.room_number, oda.room_number)

        gunler = []
        current_date = start_date
        for day in range(1, num_days + 1):
            dolu = False
            rez_id = None
            for res in clashing_reservations:
                if res.room_id == oda.id and res.check_in <= current_date < res.check_out:
                    dolu = True
                    rez_id = res.id
                    break
            gunler.append({
                'gun': current_date.day,
                'durum': 'dolu' if dolu else 'bos',
                'rez_id': rez_id
            })
            current_date += timedelta(days=1)

        result.append({
            'oda_id': oda.id,
            'oda': gorunur_oda_adi,
            'gunler': gunler
        })

    return jsonify(result)



@app.route('/rezervasyon/yap', methods=['POST'])
def rezervasyon_yap():
    # ... (Rezervasyon yapma mantığı) ...
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')
    room_type_kod = request.form.get('room_type')
    guest_name = request.form.get('guest_name')
    guest_email = request.form.get('guest_email')
    guest_phone = request.form.get('guest_phone')
    adults = int(request.form.get('adults'))
    children = int(request.form.get('children'))

    is_available, result = check_availability(room_type_kod, check_in_str, check_out_str)

    if is_available:
        available_room = result
        
        check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()

        new_reservation = Reservation(
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            check_in=check_in_date,
            check_out=check_out_date,
            adults=adults,
            children=children,
            room_id=available_room.id,
            status='Online Onay Bekliyor'
        )

        db.session.add(new_reservation)
        db.session.commit()

        flash(f'Rezervasyon talebiniz alınmıştır. Onay için ödeme bekleniyor.', 'success')
        
        return redirect(url_for('rezervasyon_formu'))
    else:
        flash(result, 'danger')
        return redirect(url_for('rezervasyon_formu'))

# --- MÜŞTERİ HESAP YÖNETİM ROTALARI ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('profil'))

    if request.method == 'POST':
        # --- HATA ÇÖZÜMÜ: 'form' yerine 'request.form' kullanıldı ---
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        kvkk_consent_value = request.form.get('kvkk_consent')  
        # --- Yeni Alanlar Eklendi ---
        first_name_form = request.form.get('first_name')
        last_name_form = request.form.get('last_name')
        # -----------------------------

        if not (username and email and password and password_confirm):
            flash("Lütfen tüm alanları doldurun.", 'danger')
            return render_template('register.html', title="Kayıt Ol", nav_links=NAV_LINKS)

        if password != password_confirm:
            flash("Şifreler eşleşmiyor.", 'danger')
            return render_template('register.html', title="Kayıt Ol", nav_links=NAV_LINKS)

        if User.query.filter_by(username=username).first():
            flash("Bu kullanıcı adı zaten kullanılıyor.", 'danger')
            return render_template('register.html', title="Kayıt Ol", nav_links=NAV_LINKS)
        if User.query.filter_by(email=email).first():
            flash("Bu e-posta adresi zaten kayıtlı.", 'danger')
            return render_template('register.html', title="Kayıt Ol", nav_links=NAV_LINKS)

        if kvkk_consent_value != 'on':
             flash("Kayıt olabilmek için KVKK metnini onaylamanız gerekmektedir.", 'danger')
             return render_template('register.html', title="Kayıt Ol", nav_links=NAV_LINKS)
            
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
            total_points=0,
            is_admin=False,
            kvkk_consent=True,
            # Yeni alanları atama
            first_name=first_name_form, 
            last_name=last_name_form
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Kayıt başarılı! Lütfen giriş yapınız.", 'success')
        return redirect(url_for('login'))

    # GET İsteği için
    return render_template('register.html', title="Kayıt Ol", nav_links=NAV_LINKS)

# --- 4. YENİ ROTA: Ödül Talebini Onayla ---
@app.route('/admin/approve_redemption/<int:redemption_id>', methods=['GET'])
@login_required
def approve_redemption(redemption_id):
    if not current_user.is_admin:
        flash("Yetkisiz erişim.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    redemption = Redemption.query.get_or_404(redemption_id)
    
    if redemption.status != 'Beklemede':
        flash("Bu talep zaten işlenmiş.", "warning")
        return redirect(url_for('admin_dashboard') + '#redemptions-approval')

    redemption.status = 'Onaylandı'
    db.session.commit()
    
    # NOT: Puan Düşme İşlemi Redundant Olmalı. 
    # Profilde puan zaten düşüldüğü için burada puan EKLEME/DÜŞME yapmıyoruz. 
    # Sadece statüyü güncelliyoruz.
    
    flash(f"Ödül Talebi #{redemption.id} ({redemption.reward.title}) onaylandı.", "success")
    return redirect(url_for('admin_dashboard') + '#redemptions-approval')


# --- 5. YENİ ROTA: Ödül Talebini Reddet ---
@app.route('/admin/reject_redemption/<int:redemption_id>', methods=['GET'])
@login_required
def reject_redemption(redemption_id):
    if not current_user.is_admin:
        flash("Yetkisiz erişim.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    redemption = Redemption.query.get_or_404(redemption_id)
    
    if redemption.status != 'Beklemede':
        flash("Bu talep zaten işlenmiş.", "warning")
        return redirect(url_for('admin_dashboard') + '#redemptions-approval')

    # Talep reddedildiğinde puanı KULLANICININ HESABINA GERİ İADE EDİN
    redemption.status = 'Reddedildi'
    redemption.user.total_points += redemption.points_used 
    db.session.commit()
    
    flash(f"Ödül Talebi #{redemption.id} reddedildi ve {redemption.points_used} puan iade edildi.", "warning")
    return redirect(url_for('admin_dashboard') + '#redemptions-approval')
@app.route('/admin/add-mission', methods=['GET', 'POST'])
@login_required
def add_mission():
    if not current_user.is_admin:
        flash("Bu sayfaya erişim yetkiniz yok.", "danger")
        return redirect(url_for('profil'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        points_reward = int(request.form.get('points_reward'))
        # Formdan gelen veriyi alırken 'mission_type' kullanmak sorun değil
        mission_type = request.form.get('mission_type')
        is_repeatable = request.form.get('is_repeatable') == 'on'
        is_active = request.form.get('is_active') == 'on'

        new_mission = Mission(
            title=title,
            description=description,
            points_reward=points_reward,
            # 🚨 KRİTİK DÜZELTME BURADA!
            # Modeldeki sütun adı 'type' olduğu için burayı 'type' olarak değiştirdik.
            type=mission_type, 
            # Hatalı olan: mission_type=mission_type,
            
            is_repeatable=is_repeatable,
            is_active=is_active
        )
        db.session.add(new_mission)
        db.session.commit()
        flash(f'Yeni görev "{title}" başarıyla eklendi.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_mission.html', nav_links=NAV_LINKS, title="Yeni Görev Ekle")
@app.route('/profil/complete_mission/<int:mission_id>', methods=['GET'])
@login_required
def complete_mission(mission_id):
    mission = Mission.query.get_or_404(mission_id)
    
    if not mission.is_active:
        flash("Bu görev şu anda aktif değil.", "danger")
        return redirect(url_for('profil'))

    # Kullanıcının bu görevi zaten tamamlayıp tamamlamadığını kontrol et
    # UserMission modelini kullanıyoruz.
    existing_task = UserMission.query.filter_by(user_id=current_user.id, mission_id=mission_id).first()
    
    if existing_task and not mission.is_repeatable:
        flash("Bu görevi daha önce tamamladınız.", "warning")
        return redirect(url_for('profil'))
        
    # --- KRİTİK DÜZELTME BAŞLANGIÇ ---
    
    # HATA 2 DÜZELTİLDİ: total_points kullanıldı.
    current_user.total_points += mission.points_reward 
    
    if not existing_task:
        # UserMission modelini kullanıyoruz.
        new_task_record = UserMission(
            user_id=current_user.id,
            mission_id=mission_id,
            # HATA 3 DÜZELTİLDİ: is_validated=True kullanıldı.
            is_validated=True 
            # NOT: is_validated alanını kullanarak görevin tamamlandığını işaretliyoruz.
        )
        db.session.add(new_task_record)
    
    # Eğer görev tekrar edilebilir ise, her seferinde yeni kayıt oluşturulabilir, 
    # ancak sizin modelinizde UniqueConstraint olduğu için (eğer tekrar edilebilir ise)
    # buradaki mantığı basitleştirip sadece puan eklemeyi ve mevcut değilse kayıt 
    # oluşturmayı tercih ettik.
    
    # --- KRİTİK DÜZELTME BİTİŞİ ---

    db.session.commit()
    
    flash(f"Tebrikler! '{mission.title}' görevini tamamladınız ve +{mission.points_reward} puan kazandınız.", "success")
    return redirect(url_for('profil'))

@app.route('/profil')
@login_required
def profil():
    
    user_tasks_data = []
    
    # Model adı artık UserMission (Sizin modelinizin adı)
    active_missions = Mission.query.filter_by(is_active=True).all()
    
    for mission in active_missions:
        # UserMission modelini kullanıyoruz
        # Bu görev, bu kullanıcı tarafından herhangi bir kayıtla tamamlanmış mı?
        is_completed = UserMission.query.filter_by(
            user_id=current_user.id, 
            mission_id=mission.id
            # NOT: Bu modelde sadece kayıt olması tamamlandığı anlamına gelir. 
            # completed=True filtresini çıkardık.
        ).first()
        
        user_tasks_data.append({
            'name': mission.title,
            'description': mission.description,
            # is_completed kayıt varsa True döner.
            'completed': bool(is_completed), 
            'mission_id': mission.id,              
            'points_reward': mission.points_reward   
        })
    
    rewards = Reward.query.all()  

    return render_template(
        'profil.html', 
        current_user=current_user, 
        tasks=user_tasks_data,  
        rewards=rewards
    )
                           
                        
                          
                           
                         

                            

@app.route('/admin/add-campaign', methods=['GET', 'POST'])
@login_required
def add_campaign():
    if not current_user.is_admin:
        flash("Bu sayfaya erişim yetkiniz yok.", "danger")
        return redirect(url_for('profil'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        is_active = request.form.get('is_active') == 'on'

        new_campaign = Campaign(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active
        )
        db.session.add(new_campaign)
        db.session.commit()
        flash(f'Yeni kampanya "{title}" başarıyla eklendi.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_campaign.html', nav_links=NAV_LINKS, title="Yeni Kampanya Ekle")



@app.route('/reward/redeem/<int:reward_id>', methods=['POST'])
@login_required
def redeem_reward(reward_id):
    reward = Reward.query.get_or_404(reward_id)
    
    if current_user.total_points < reward.points_cost:
        flash("Yeterli puanınız yok. Biraz daha görev tamamlamalısınız!", 'danger')
        return redirect(url_for('profil'))
        
    current_user.total_points -= reward.points_cost
    
    new_redemption = Redemption(
        user_id=current_user.id,
        reward_id=reward_id,
        status='REQUESTED'
    )
    
    db.session.add(new_redemption)
    db.session.commit()
    
    flash(f'Tebrikler! "{reward.title}" ödülünü başarıyla talep ettiniz. Kalan Puanınız: {current_user.total_points}', 'success')
    return redirect(url_for('profil'))
# --- SADAKAT ROTALARI SONU ---

# --- YÖNETİCİ GİRİŞ VE PANEL ROTALARI ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('profil'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Hoş geldiniz, {user.username}!', 'success')
            
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('profil'))

        else:
            flash('Kullanıcı adı veya şifre hatalı.', 'danger')

    return render_template('login.html', title="Yönetici Girişi", nav_links=NAV_LINKS)

@app.route('/logout')
@login_required 
def logout():
    logout_user()
    flash("Başarıyla çıkış yaptınız.", 'success') 
    return redirect(url_for('index'))


# app.py dosyasında, mevcut admin_dashboard fonksiyonunuzu bununla değiştirin
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_ # Eğer bu import yoksa ekleyin

@app.route('/admin-dashboard')  # TİRE'LI TANIM
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Bu işlem için yetkiniz yok.", "danger")
        return redirect(url_for('index'))

    # Rezervasyonları çek
    reservations = Reservation.query.filter(
        or_(
            Reservation.status == 'Online Onay Bekliyor',
            Reservation.status == 'Telefon Onaylı',
            Reservation.status == 'Onaylandı',
            Reservation.status == 'Giriş Yaptı',
            Reservation.status == 'Yat Kulübü Talebi (Admin Bekliyor)',
        )
    ).order_by(Reservation.check_in.asc()).all()
    
    # Odaları room_number'a göre sıralıyoruz
    rooms = Room.query.order_by(cast(Room.room_number, Integer)).all()
    
    users_list = User.query.filter(User.is_admin == False).all()
    all_missions = Mission.query.order_by(Mission.is_active.desc(), Mission.id.asc()).all()
    
    # Ödül Taleplerini Çek
    pending_redemptions = Redemption.query.filter_by(status='Beklemede').order_by(Redemption.redemption_date.asc()).all()

    # Şablona gönderim
    return render_template(
        'admin_dashboard.html', 
        current_user=current_user,
        reservations=reservations,
        rooms=rooms,  # sorted_rooms yerine rooms olarak gönderdik
        users_list=users_list,
        missions=all_missions,
        pending_redemptions=pending_redemptions
    )

    
    
# --- 2. YENİ ROTA: Görev Aktivasyon/Deaktivasyon ---
@app.route('/admin/toggle_mission/<int:mission_id>', methods=['GET'])
@login_required
def toggle_mission(mission_id):
    if not current_user.is_admin:
        flash("Bu işlem için yetkiniz yok.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    mission = Mission.query.get_or_404(mission_id)
    mission.is_active = not mission.is_active
    
    status_msg = "yayında" if mission.is_active else "yayından kaldırıldı"
    db.session.commit()
    
    flash(f"'{mission.title}' görevi artık {status_msg}.", "info")
    return redirect(url_for('admin_dashboard') + '#missions-management')


# --- 3. YENİ ROTA: Görev Tamamlama Onayı (Manual Onay Gerektiren Görevler İçin) ---
@app.route('/admin/approve_mission/<int:user_id>/<int:mission_id>', methods=['GET'])
@login_required
def approve_mission_manual(user_id, mission_id):
    if not current_user.is_admin:
        flash("Bu işlem için yetkiniz yok.", "danger")
        return redirect(url_for('admin_dashboard'))
        
    user = User.query.get_or_404(user_id)
    mission = Mission.query.get_or_404(mission_id)
    
    # Kontrol: Görev zaten tamamlanmış mı? (Repeatable olmayan görevler için)
    already_completed = UserMission.query.filter_by(user_id=user_id, mission_id=mission_id).first()
    
    if already_completed and not mission.is_repeatable:
        flash(f"{user.username} kullanıcısı bu görevi zaten tamamlamış.", "warning")
        return redirect(url_for('admin_dashboard') + '#missions-management')
        
    # Puanı ekle ve kaydı oluştur
    user.total_points += mission.points_reward
    user_mission = UserMission(user_id=user_id, mission_id=mission_id)
    db.session.add(user_mission)
    db.session.commit()
    
    flash(f"✅ {user.username} kullanıcısının '{mission.title}' görevi onaylandı ve {mission.points_reward} puan eklendi.", "success")
    return redirect(url_for('admin_dashboard') + '#missions-management')
    
                           

    # Oda seçim listesini özel isimlerle hazırlama
    formatted_rooms = []
    sorted_rooms = Room.query.order_by(Room.room_number).all()
    for index, room in enumerate(sorted_rooms):
        room_name = room.room_number 
        if index < len(CUSTOM_CALENDAR_NAMES):
            room_name = CUSTOM_CALENDAR_NAMES[index]
        room.display_name = room_name 
        formatted_rooms.append(room)

    return render_template('admin_dashboard.html', 
                           title="Yönetici Paneli", 
                           nav_links=NAV_LINKS, 
                           reservations=reservations_list, 
                           oda_tipleri=ODA_TIPLERI_DICT,
                           rooms=formatted_rooms,
                           users_list=users_list,
                           campaigns=campaigns)


@app.route('/admin/add-reservation', methods=['GET', 'POST'])
@login_required
def add_reservation():
    # YÖNETİCİ KONTROLÜ
    if not current_user.is_admin:
        flash("Bu sayfaya erişim yetkiniz bulunmamaktadır.", 'danger')
        return redirect(url_for('profil')) 
    
    if request.method == 'POST':
        room_id = int(request.form.get('room_id'))
        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')
        guest_name = request.form.get('guest_name')
        guest_email = request.form.get('guest_email')
        guest_phone = request.form.get('guest_phone')
        adults = int(request.form.get('adults'))
        children = int(request.form.get('children'))

        check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        # Çakışma kontrolü
        clashing_reservations = Reservation.query.filter(
            Reservation.room_id == room_id,
            and_(
                Reservation.check_out > check_in_date,
                Reservation.check_in < check_out_date,
                or_(
                    Reservation.status == 'Onaylandı',
                    Reservation.status == 'Telefon Onaylı',
                    Reservation.status == 'Giriş Yaptı'
                )
            )
        ).all()
        
        if clashing_reservations:
            room = Room.query.get(room_id)
            flash(f"Hata: {room.room_number} numaralı oda bu tarihlerde zaten dolu!", 'danger')
            return redirect(url_for('add_reservation'))

        new_reservation = Reservation(
            guest_name=guest_name,
            guest_email=guest_email,
            guest_phone=guest_phone,
            check_in=check_in_date,
            check_out=check_out_date,
            adults=adults,
            children=children,
            room_id=room_id,
            status='Telefon Onaylı' 
        )

        db.session.add(new_reservation)
        db.session.commit()

        flash(f'{guest_name} için Manuel Rezervasyon başarıyla eklendi ve Onaylandı.', 'success')
        return redirect(url_for('admin_dashboard'))

    # GET isteği (formu göstermek için)
    formatted_rooms = []
    # Oda numarasına göre doğru sıralama
    sorted_rooms = Room.query.order_by(cast(Room.room_number, Integer)).all()
    
    for index, room in enumerate(sorted_rooms):
        # Kullanıcıya gösterilecek isim
        room_name = CUSTOM_CALENDAR_NAMES[index] if index < len(CUSTOM_CALENDAR_NAMES) else str(room.room_number)
        room.display_name = f"{room_name} ({room.room_number})"
        formatted_rooms.append(room)
    
    return render_template('add_reservation.html', 
                            title="Manuel Rezervasyon Ekle", 
                            nav_links=NAV_LINKS, 
                            rooms=formatted_rooms, 
                            oda_tipleri=ODA_TIPLERI_DICT,
                            datetime=datetime)



@app.route('/admin/update-status/<int:reservation_id>/<string:new_status>')
@login_required
def update_reservation_status(reservation_id, new_status):
    # YÖNETİCİ KONTROLÜ
    if not current_user.is_admin:
        flash("Bu işleme erişim yetkiniz bulunmamaktadır.", 'danger')
        return redirect(url_for('profil')) 
    
    reservation = Reservation.query.get_or_404(reservation_id)

    allowed_statuses = ['Online Onay Bekliyor', 'Telefon Onaylı', 'Onaylandı', 'Giriş Yaptı', 'Çıkış Yaptı', 'İptal']
    if new_status not in allowed_statuses:
        flash("Hata: Geçersiz rezervasyon durumu.", 'danger')
        return redirect(url_for('admin_dashboard'))

    # Oda Atama Mantığı (Sadece Onaylandı durumuna geçerken çalışır)
    room_id_param = request.args.get('room_id')
    if new_status == 'Onaylandı' and room_id_param:
        try:
            chosen_room_id = int(room_id_param)
        except ValueError:
            flash("Hata: Geçersiz oda seçimi.", 'danger')
            return redirect(url_for('admin_dashboard'))

        # Çakışma kontrolü (Kritik)
        conflict = Reservation.query.filter(
            Reservation.room_id == chosen_room_id,
            Reservation.id != reservation.id,
            and_(
                Reservation.check_out > reservation.check_in,
                Reservation.check_in < reservation.check_out,
                or_(
                    Reservation.status == 'Onaylandı',
                    Reservation.status == 'Telefon Onaylı',
                    Reservation.status == 'Giriş Yaptı'
                )
            )
        ).first()

        if conflict:
            conflict_room = Room.query.get(chosen_room_id)
            flash(f"Hata: Seçilen oda ({conflict_room.room_number if conflict_room else chosen_room_id}) bu tarihlerde dolu!", 'danger')
            return redirect(url_for('admin_dashboard'))

        # Çakışma yoksa odayı ata
        reservation.room_id = chosen_room_id

    reservation.status = new_status
    
    if new_status == 'Çıkış Yaptı':
        pass # Sadakat puanı verme mantığı buraya eklenecek

    db.session.commit()
    
    flash(f'Rezervasyon ID {reservation_id} durumu \"{new_status}\" olarak güncellendi.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-reservation/<int:reservation_id>')
@login_required
def delete_reservation(reservation_id):
    # YÖNETİCİ KONTROLÜ
    if not current_user.is_admin:
        flash("Bu işleme erişim yetkiniz bulunmamaktadır.", 'danger')
        return redirect(url_for('profil')) 
    
    reservation = Reservation.query.get_or_404(reservation_id)
    guest_name = reservation.guest_name 

    db.session.delete(reservation)
    db.session.commit()

    flash(f'{guest_name} misafirin rezervasyonu (ID: {reservation_id}) başarıyla İPTAL EDİLDİ ve silindi.', 'warning')
    return redirect(url_for('admin_dashboard'))




# --- UYGULAMA BAŞLANGIÇ KISMI ---

@app.route('/kvkk-aydinlatma')
def kvkk_aydinlatma():
    # KVKK metnini bu yeni sayfaya gönderiyoruz
    return render_template('kvkk_metni.html', 
                           title="KVKK Metni", 
                           nav_links=NAV_LINKS,
                           KVKK_TEXT=KVKK_TEXT) # Dikkat: Değişken adı aynı

if __name__ == '__main__':
    with app.app_context():
        # Veritabanını oluştur
        db.create_all()

        # 🏠 Başlangıç odalarını ekle (eğer hiç oda yoksa)
        if Room.query.count() == 0:
            initial_rooms = [
                Room(room_number='STD01', room_type='standart', capacity=2),
                Room(room_number='STD02', room_type='standart', capacity=2),
                Room(room_number='STD03', room_type='standart', capacity=2),
                Room(room_number='STD04', room_type='standart', capacity=2),
                Room(room_number='SUI01', room_type='suit', capacity=5),
                Room(room_number='PET01', room_type='petsuit', capacity=4),
                Room(room_number='STD07', room_type='standart', capacity=2),
                Room(room_number='LSU01', room_type='largesuit', capacity=3),
            ]

            db.session.add_all(initial_rooms)
            db.session.commit()
            print(f"\n✅ Başlangıç odaları başarıyla oluşturuldu ({Room.query.count()} oda)\n")

        # 👑 Admin kullanıcısını kontrol et / oluştur
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@kaanmotel.com',
                password_hash=generate_password_hash('sifre123', method='pbkdf2:sha256'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("\n✅ İlk admin kullanıcısı oluşturuldu → Kullanıcı Adı: admin | Şifre: sifre123\n")

    # 🌐 Sunucuyu başlat
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
