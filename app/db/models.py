import enum
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class StockMovementReason(str, enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    WASTE = "waste"
    INITIAL = "initial"


class PriceHistoryField(str, enum.Enum):
    PRICE = "price"
    COST = "cost"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PREPARED = "prepared"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ShipmentStatus(str, enum.Enum):
    LABEL_CREATED = "label_created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, nullable=True, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    aliases: Mapped[str | None] = mapped_column(String(300), nullable=True)
    unit: Mapped[str] = mapped_column(String(10))
    price: Mapped[float] = mapped_column(Float)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    stock: Mapped[float] = mapped_column(Float, default=0)
    low_stock_threshold: Mapped[float] = mapped_column(Float, default=0)
    max_stock: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    supplier_links: Mapped[list["ProductSupplier"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="PriceHistory.changed_at.desc()",
    )
    stock_movements: Mapped[list["StockMovement"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="StockMovement.created_at.desc()",
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), default=OrderStatus.PENDING
    )
    total: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    promised_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    shipment: Mapped["Shipment | None"] = relationship(
        back_populates="order", uselist=False, cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[float] = mapped_column(Float)
    unit_price: Mapped[float] = mapped_column(Float)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    tracking_no: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    carrier: Mapped[str] = mapped_column(String(50), default="MockKargo")
    status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus, name="shipment_status"), default=ShipmentStatus.LABEL_CREATED
    )
    last_event_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estimated_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    current_location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="shipment")


class AdminUser(Base):
    """Web panel kullanicilari (isletme yoneticileri).

    Musterilerden ayri model — Customer Telegram tarafi, AdminUser panel tarafi.
    """

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    briefing_enabled: Mapped[bool] = mapped_column(default=False)
    # Marketplace komşu önerileri için KOBİ konumu
    city: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    district: Mapped[str | None] = mapped_column(String(80), nullable=True)
    preferred_carrier: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Marketplace: kategori, kargo şirketi, konum (komşu eşleşme + filtre için)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    carrier: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    district: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    product_links: Mapped[list["ProductSupplier"]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )


class ProductSupplier(Base):
    __tablename__ = "product_suppliers"
    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id", name="uq_product_supplier"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), index=True
    )
    supplier_sku: Mapped[str | None] = mapped_column(String(60), nullable=True)
    last_unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_purchase_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_preferred: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="supplier_links")
    supplier: Mapped["Supplier"] = relationship(back_populates="product_links")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    field: Mapped[PriceHistoryField] = mapped_column(
        Enum(PriceHistoryField, name="price_history_field")
    )
    old_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_value: Mapped[float] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    changed_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    product: Mapped["Product"] = relationship(back_populates="price_history")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    warehouse_id: Mapped[int | None] = mapped_column(
        ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lot_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_lots.id", ondelete="SET NULL"), nullable=True, index=True
    )
    delta: Mapped[float] = mapped_column(Float)
    reason: Mapped[StockMovementReason] = mapped_column(
        Enum(StockMovementReason, name="stock_movement_reason")
    )
    reference_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    balance_after: Mapped[float] = mapped_column(Float)
    created_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    product: Mapped["Product"] = relationship(back_populates="stock_movements")
    warehouse: Mapped["Warehouse | None"] = relationship()


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    code: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class StockBalance(Base):
    __tablename__ = "stock_balances"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_stock_balance"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[float] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    product: Mapped["Product"] = relationship()
    warehouse: Mapped["Warehouse"] = relationship()


class LotActionType(str, enum.Enum):
    DISCOUNT = "discount"  # Indirim önerisi
    BUNDLE = "bundle"  # Paket/promosyon
    WASTE = "waste"  # Fire olarak işle
    NOTIFY = "notify"  # Müşterilere bildirim
    DELAY_REORDER = "delay_reorder"  # Yeni siparişi ertele


class LotActionStatus(str, enum.Enum):
    PENDING = "pending"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class StockLot(Base):
    """Lot/batch + son kullanma tarihi takibi.

    Bir StockBalance.quantity, ayni product_id + warehouse_id icin tum StockLot
    quantity'lerinin toplami olabilir. Lot bazli kullanim opsiyonel — lot olmadan
    da sistem calismaya devam eder (mevcut StockBalance tek dogruluk kaynagi).
    """

    __tablename__ = "stock_lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"), index=True
    )
    lot_number: Mapped[str] = mapped_column(String(60))
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0)
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    product: Mapped["Product"] = relationship()
    warehouse: Mapped["Warehouse"] = relationship()
    supplier: Mapped["Supplier | None"] = relationship()


class LotAction(Base):
    """SKT'si yaklasan lot icin AI advisor agent'inin uretdigi aksiyon onerileri.

    Her oneri: konu + 2-3 cumlelik aciklama + onerilen indirim yuzdesi
    (action_type=discount ise) + oncelik seviyesi (1=acil, 3=dusuk).
    """

    __tablename__ = "lot_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column(
        ForeignKey("stock_lots.id", ondelete="CASCADE"), index=True
    )
    action_type: Mapped[LotActionType] = mapped_column(
        Enum(LotActionType, name="lot_action_type")
    )
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1500))
    suggested_discount_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1=acil, 3=düşük
    status: Mapped[LotActionStatus] = mapped_column(
        Enum(LotActionStatus, name="lot_action_status"),
        default=LotActionStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    lot: Mapped["StockLot"] = relationship()


class SocialPlatform(str, enum.Enum):
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    THREADS = "threads"
    LINKEDIN = "linkedin"


class SocialPostStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class SocialAssetType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class SocialAssetStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class SocialAccount(Base):
    """Sosyal medya hesabı bağlantısı. access_token gerçek API entegrasyonunda."""

    __tablename__ = "social_accounts"
    __table_args__ = (
        UniqueConstraint("platform", "handle", name="uq_social_platform_handle"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[SocialPlatform] = mapped_column(
        Enum(SocialPlatform, name="social_platform"), index=True
    )
    handle: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    access_token: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SocialPost(Base):
    """Sosyal medya gönderisi (multi-platform).

    target_platforms: virgülle ayrılmış platform değerleri (örn. 'instagram,tiktok')
    hashtags: virgülle ayrılmış (örn. 'kobi,bal,dogal')
    """

    __tablename__ = "social_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(String(3000))
    target_platforms: Mapped[str] = mapped_column(String(200))
    hashtags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[SocialPostStatus] = mapped_column(
        Enum(SocialPostStatus, name="social_post_status"),
        default=SocialPostStatus.DRAFT,
        index=True,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ai_generated: Mapped[bool] = mapped_column(default=False)
    prompt: Mapped[str | None] = mapped_column(String(500), nullable=True)
    related_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    assets: Mapped[list["SocialAsset"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    related_product: Mapped["Product | None"] = relationship()


class SocialAsset(Base):
    """Bir post için üretilmiş görsel/video.

    provider: 'placeholder' (mock), 'openai' (DALL-E), 'replicate' vb.
    Mock placeholder URL'leri picsum.photos veya statik logo döner.
    """

    __tablename__ = "social_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("social_posts.id", ondelete="CASCADE"), index=True
    )
    asset_type: Mapped[SocialAssetType] = mapped_column(
        Enum(SocialAssetType, name="social_asset_type")
    )
    prompt: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[SocialAssetStatus] = mapped_column(
        Enum(SocialAssetStatus, name="social_asset_status"),
        default=SocialAssetStatus.PENDING,
    )
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    post: Mapped["SocialPost"] = relationship(back_populates="assets")


class ExpenseCategory(str, enum.Enum):
    RENT = "rent"
    SALARIES = "salaries"
    UTILITIES = "utilities"
    MARKETING = "marketing"
    LOGISTICS = "logistics"
    MAINTENANCE = "maintenance"
    TAX = "tax"
    SUPPLIES = "supplies"
    INSURANCE = "insurance"
    OTHER = "other"


class Expense(Base):
    """Isletme gideri — kira, maas, fatura, lojistik, vergi vs.

    incurred_at: Giderin gerceklestigi tarih (fatura kesim tarihi).
    created_at: Sistem kaydi zamani — gecmise donuk girilebilir.
    """

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(ExpenseCategory, name="expense_category"), index=True
    )
    amount: Mapped[float] = mapped_column(Float)
    vendor: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    incurred_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    is_recurring: Mapped[bool] = mapped_column(default=False)
    created_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CustomerComplaint(Base):
    """Sikayet riski tespitleri — hem reaktif (Telegram mesaj sinyali) hem
    proaktif (kargo gecikmesi, bayat siparis, mukerrer sikayet vs.) kaynaklar.

    Reactive: webhook handler regex+LLM ile mesaja skor verir.
    Proactive: scheduled agent sistem verisinde anomaliler arar, her bulgu
    icin subject+description'i kendisi yazar.
    """

    __tablename__ = "customer_complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    message_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, index=True)
    signals: Mapped[str | None] = mapped_column(String(300), nullable=True)
    source: Mapped[str] = mapped_column(
        String(40), default="telegram_message", index=True
    )
    related_entity_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    related_entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auto_generated: Mapped[bool] = mapped_column(default=False, index=True)
    resolved: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class TelegramSession(Base):
    """Telegram konusma state'i ve bekleyen siparis niyetleri."""

    __tablename__ = "telegram_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    pending_intent: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# ============================================================================
# Marketplace — Tedarikçi pazarı, satınalma siparişleri, komşu KOBİ önerileri
# ============================================================================


class PurchaseOrderStatus(str, enum.Enum):
    """Tedarikçiye verilen sipariş yaşam döngüsü."""

    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    """KOBİ'nin bir tedarikçiye verdiği satınalma siparişi (inbound).

    Order (müşteri siparişi) modelinin tersi — burada KOBİ alıcı, supplier satıcı.
    RECEIVED durumuna geçince her item için StockMovement.PURCHASE yazılır
    ve toplam stok artar.
    """

    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, name="purchase_order_status"),
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    expected_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_suggested: Mapped[bool] = mapped_column(default=False, index=True)
    suggestion_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    supplier: Mapped["Supplier"] = relationship()
    items: Mapped[list["PurchaseOrderItem"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[float] = mapped_column(Float)
    unit_cost: Mapped[float] = mapped_column(Float)

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class NearbyShop(Base):
    """Mock multi-tenant — yakın KOBİ. Demo amaçlı seed verisi.

    Gerçek multi-tenant olmadığı için "diğer KOBİ'lerin satınalmaları" bu tablodan.
    Hackathon scope'unda bu yeterli; production'da AdminUser/Organization ile
    aynı yapı olur, query farklı.
    """

    __tablename__ = "nearby_shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    shop_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    city: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_carrier: Mapped[str | None] = mapped_column(
        String(60), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    purchases: Mapped[list["NearbyShopPurchase"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )


class NearbyShopPurchase(Base):
    """Komşu KOBİ'nin tarihsel satınalmaları — AI advisor için sinyal kaynağı."""

    __tablename__ = "nearby_shop_purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(
        ForeignKey("nearby_shops.id", ondelete="CASCADE"), index=True
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product_name: Mapped[str] = mapped_column(String(120), index=True)
    product_category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    quantity: Mapped[float] = mapped_column(Float)
    unit_cost: Mapped[float] = mapped_column(Float)
    carrier: Mapped[str | None] = mapped_column(String(60), nullable=True)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    shop: Mapped["NearbyShop"] = relationship(back_populates="purchases")
    supplier: Mapped["Supplier | None"] = relationship()


class MarketplaceRecommendation(Base):
    """AI advisor'ın ürettiği komşu trend bazlı satınalma önerisi.

    Cron job ile günlük üretilir, admin panelde gösterilir, dismiss veya
    apply (purchase order'a çevirme) eylemleri var.
    """

    __tablename__ = "marketplace_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    product_name: Mapped[str] = mapped_column(String(120), index=True)
    suggested_supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
    )
    suggested_quantity: Mapped[float] = mapped_column(Float)
    estimated_unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    # Neden öneri: "Aynı kargoyu kullanan 3 komşu KOBİ son 14 günde aldı"
    reasoning: Mapped[str] = mapped_column(String(800))
    nearby_signal_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(
        String(20), default="active", index=True
    )  # active | dismissed | applied
    applied_purchase_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    suggested_supplier: Mapped["Supplier | None"] = relationship()
    product: Mapped["Product | None"] = relationship()
