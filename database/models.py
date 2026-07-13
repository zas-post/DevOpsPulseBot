import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PostStatus(enum.Enum):
    PENDING = "pending"  # Только скачан, еще не отправлен админу в ЛС
    SENT_TO_ADMIN = (
        "sent_admin"  # Карточка отправлена админу, ждет нажатия кнопки 👍/👎
    )
    PUBLISHED = "published"  # Одобрен и опубликован в канал
    REJECTED = "rejected"  # Отклонен админом


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    hub_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), default=PostStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
