from email.policy import default
from http import server
import sqlalchemy
import enum
from sqlalchemy import Enum, Table
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
)
metadata = MetaData()
Base = declarative_base(metadata=metadata)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
tracks_id = "tracks.id"
users_id = "users.id"
tags_id = "tags.id"


class Voice(str, enum.Enum):
    she_her = 0
    he_him = 1
    they_them = 2
    she_he = 3
    she_they = 4
    he_they = 5
    she_he_they = 6
    
class Status(str, enum.Enum):
    draft = 0
    publish = 1
    banned = 2
    deleted = 3
    
    
class LanguageTable(Base):
    __tablename__ = 'languages'
    id = sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, unique=True)
    language = sqlalchemy.Column("language", sqlalchemy.String, primary_key=True, unique=True)
    __table_args__ = (sqlalchemy.Index("id_language_unique", "id", "language", unique=True), )

tracktagtable = Table("tracktags", Base.metadata,
    sqlalchemy.Column("track_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(tracks_id), nullable=False),
    sqlalchemy.Column("tag_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(tags_id), nullable=False),
    sqlalchemy.Index('track_tag_unique', "track_id", "tag_id", unique=True)
)

trackcheckedtable = Table("trackchecked", Base.metadata,
    sqlalchemy.Column("track_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(tracks_id), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(users_id), nullable=False),
    sqlalchemy.Column("liked", sqlalchemy.Boolean(), default=False, nullable=False),
    sqlalchemy.Index('track_user_unique', "track_id", "user_id", unique=True)
    )

trackseentable = Table("trackseen", Base.metadata,
    sqlalchemy.Column("track_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(tracks_id), nullable=False),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(users_id), nullable=False),
    sqlalchemy.Column("liked", sqlalchemy.Boolean(), default=False, nullable=False),
    sqlalchemy.Index('track_user_seen_unique', "track_id", "user_id", unique=True)
    )


class TrackTable(Base):
    __tablename__ = 'tracks'
    id = sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    user_id = sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(users_id), nullable=False)
    language_id = sqlalchemy.Column("language_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(LanguageTable.id), nullable=False)
    name = sqlalchemy.Column("name", sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column("description", sqlalchemy.String)
    path = sqlalchemy.Column("path", sqlalchemy.String, nullable=False)
    voice = sqlalchemy.Column("voice", Enum(Voice), default=Voice.they_them)
    status = sqlalchemy.Column("status", Enum(Status), default=Status.publish)
    created_at = sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now())
    updated_at = sqlalchemy.Column("updated_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())
    __table_args__ = (sqlalchemy.Index('user_trackname_unique', "user_id", "name", unique=True), )
    tags = sqlalchemy.orm.relationship('TagTable', secondary='tracktags', back_populates="tracks", cascade="save-update")
    checks = sqlalchemy.orm.relationship('UserTable', secondary='trackchecked', back_populates="checked", cascade="save-update")
    views = sqlalchemy.orm.relationship('UserTable', secondary='trackseen', back_populates="viewed", cascade="save-update")
    
class UserTable(Base):
    __tablename__ = 'users'
    id = sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    email = sqlalchemy.Column("email", sqlalchemy.String, primary_key=True, unique=True, nullable=False)
    hash_password = sqlalchemy.Column("hash_password", sqlalchemy.String, nullable=False)
    update_token = sqlalchemy.Column("update_token", sqlalchemy.String, nullable=False)
    email_confirm = sqlalchemy.Column("email_confirm", sqlalchemy.Boolean, default=False, nullable=False)
    created_at = sqlalchemy.Column("created_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now())
    updated_at = sqlalchemy.Column("updated_at", sqlalchemy.DateTime, server_default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())
    tracks = sqlalchemy.orm.relationship(TrackTable, backref='owner')
    checked = sqlalchemy.orm.relationship(TrackTable, secondary='trackchecked', back_populates="checks")
    viewed = sqlalchemy.orm.relationship(TrackTable, secondary='trackseen', back_populates="views")
    
class TagTable(Base):
    __tablename__ = 'tags'
    id = sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    tag = sqlalchemy.Column("tag", sqlalchemy.String, primary_key=True, unique=True)
    tracks = sqlalchemy.orm.relationship(TrackTable, secondary='tracktags', back_populates="tags")