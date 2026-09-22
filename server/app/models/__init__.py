from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

handler_group_roles = Table(
    "handler_group_roles",
    Base.metadata,
    Column("group_id", ForeignKey("handler_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("role_id", name="uq_handler_group_role"),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary=user_roles, back_populates="users", lazy="selectin"
    )


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users: Mapped[list[User]] = relationship(
        "User", secondary=user_roles, back_populates="roles", lazy="selectin"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary=role_permissions, back_populates="roles", lazy="selectin"
    )
    handler_groups: Mapped[list["HandlerGroup"]] = relationship(
        "HandlerGroup", secondary=handler_group_roles, back_populates="roles", lazy="selectin"
    )


class HandlerGroup(Base):
    __tablename__ = "handler_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    leader_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    roles: Mapped[list[Role]] = relationship(
        "Role", secondary=handler_group_roles, back_populates="handler_groups", lazy="selectin"
    )
    leader: Mapped[User | None] = relationship("User", foreign_keys=[leader_id], lazy="joined")


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("code", name="uq_permission_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    roles: Mapped[list[Role]] = relationship(
        "Role", secondary=role_permissions, back_populates="permissions", lazy="selectin"
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    contact_name: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    industry: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    # 1 启用，0 停用
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="customer"
    )
    user: Mapped[User | None] = relationship("User", foreign_keys=[user_id], lazy="joined")


class TicketCategory(Base):
    __tablename__ = "ticket_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TicketPriority(Base):
    __tablename__ = "ticket_priorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sla_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    warn_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=4)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_no: Mapped[str] = mapped_column(String(32), nullable=False, default="", index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("ticket_categories.id"), nullable=True, index=True
    )
    priority_id: Mapped[int | None] = mapped_column(
        ForeignKey("ticket_priorities.id"), nullable=True, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    service_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    expected_finish_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estimated_resolve_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_resolve_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unassigned", index=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="staff")
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    group_role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id"), nullable=True, index=True
    )
    handler_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("handler_groups.id"), nullable=True, index=True
    )
    group_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    resolution: Mapped[str] = mapped_column(Text, nullable=False, default="")
    handler_reply: Mapped[str] = mapped_column(Text, nullable=False, default="")
    handler_solution: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evaluation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rating: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    followup_result: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    followup_remark: Mapped[str] = mapped_column(Text, nullable=False, default="")
    followup_method: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    followup_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    followup_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    pending_confirm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sla_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_paused_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sla_pause_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    customer: Mapped[Customer] = relationship("Customer", back_populates="tickets")
    category: Mapped[TicketCategory | None] = relationship("TicketCategory", lazy="joined")
    priority: Mapped[TicketPriority | None] = relationship("TicketPriority", lazy="joined")
    assignee: Mapped[User | None] = relationship("User", foreign_keys=[assignee_id], lazy="joined")
    creator: Mapped[User | None] = relationship("User", foreign_keys=[creator_id], lazy="joined")
    followup_user: Mapped[User | None] = relationship(
        "User", foreign_keys=[followup_user_id], lazy="joined"
    )
    handler_group: Mapped[HandlerGroup | None] = relationship(
        "HandlerGroup", foreign_keys=[handler_group_id], lazy="joined"
    )
    collaborators: Mapped[list[User]] = relationship(
        "User",
        secondary="ticket_collaborators",
        lazy="selectin",
    )
    logs: Mapped[list["TicketLog"]] = relationship(
        "TicketLog", back_populates="ticket", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["TicketAttachment"]] = relationship(
        "TicketAttachment", back_populates="ticket", cascade="all, delete-orphan"
    )


class TicketCollaborator(Base):
    __tablename__ = "ticket_collaborators"

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class TicketFormerAssignee(Base):
    __tablename__ = "ticket_former_assignees"

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="logs")
    operator: Mapped[User | None] = relationship("User", lazy="joined")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="file")
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="attachments")
    uploader: Mapped[User | None] = relationship("User", foreign_keys=[uploader_id], lazy="joined")


class DictType(Base):
    __tablename__ = "dict_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    items: Mapped[list["DictItem"]] = relationship(
        "DictItem", back_populates="dict_type", cascade="all, delete-orphan"
    )


class DictItem(Base):
    __tablename__ = "dict_items"
    __table_args__ = (UniqueConstraint("type_id", "name", name="uq_dict_item_type_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(
        ForeignKey("dict_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)

    dict_type: Mapped[DictType] = relationship("DictType", back_populates="items")
