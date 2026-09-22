from datetime import datetime, timedelta

# 业务时间统一按北京时间展示；库内仍存 UTC（datetime.utcnow）
CN_OFFSET = timedelta(hours=8)

STATUS_LABEL = {
    "unassigned": "待分派",
    "pending": "待处理",
    "processing": "处理中",
    "waiting_customer": "等待客户",
    "overdue": "已超时",
    "resolved": "已解决",
    "closed": "已关闭",
    "ended": "已结束",
    "reopened": "已重新打开",
}

OPEN_STATUSES = {
    "unassigned",
    "pending",
    "processing",
    "waiting_customer",
    "overdue",
    "reopened",
}

HANDLER_PENDING = {"pending", "processing", "waiting_customer", "overdue", "reopened"}

FOLLOWUP_METHODS = ("电话", "微信", "上门")
FOLLOWUP_RESULTS = ("满意", "一般", "不满意", "问题复发")


ACTION_LABEL = {
    "create": "创建",
    "assign": "分派",
    "transfer": "转派",
    "collaborator": "协作者",
    "status": "状态变更",
    "record": "处理记录",
    "internal": "内部备注",
    "resolve": "解决",
    "confirm_request": "提交客户确认",
    "confirm": "客户确认",
    "reopen": "重新打开",
    "escalate": "升级",
    "followup": "回访",
    "attachment": "附件",
    "ask": "客户提问",
    "edit": "编辑",
    "customer_feedback": "客户反馈",
    "close": "关闭",
}


def fmt_dt(value: datetime | None) -> str:
    if not value:
        return ""
    return (value + CN_OFFSET).strftime("%Y-%m-%d %H:%M:%S")


def parse_dt(value) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip().replace("T", " ")[:19]
    local = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    return local - CN_OFFSET


def build_ticket_no(ticket_id: int, created_at: datetime | None = None) -> str:
    base = created_at or datetime.utcnow()
    day = (base + CN_OFFSET).strftime("%Y%m%d")
    return f"GD{day}{ticket_id:04d}"


NEAR_TIMEOUT_MINUTES = 30
AUTO_CLOSE_HOURS = 72


def _fmt_hm(total_minutes: int) -> str:
    hours, minutes = divmod(max(int(total_minutes), 0), 60)
    if hours:
        return f"{hours}小时{minutes}分"
    return f"{minutes}分"


def sla_info(ticket, now: datetime | None = None) -> dict:
    now = now or datetime.utcnow()
    priority = ticket.priority
    base = {
        "slaState": "normal",
        "deadline": "",
        "slaHours": priority.sla_hours if priority else None,
        "durationText": "",
        "durationLevel": "none",
        "waitText": "",
        "waitLevel": "none",
    }
    if not ticket.created_at:
        return base
    finished = ticket.status in {"resolved", "closed", "ended"}
    end_at = ticket.actual_resolve_at or ticket.updated_at or now if finished else now
    if finished and ticket.created_at and end_at:
        elapsed_minutes = int((end_at - ticket.created_at).total_seconds() // 60)
        base["durationText"] = _fmt_hm(elapsed_minutes)
        base["durationLevel"] = "normal"
    if finished or not priority or not ticket.created_at:
        return base
    paused = int(getattr(ticket, "sla_paused_seconds", 0) or 0)
    if ticket.status == "waiting_customer" and getattr(ticket, "sla_pause_started_at", None):
        paused += int((now - ticket.sla_pause_started_at).total_seconds())
    deadline = (ticket.sla_started_at or ticket.created_at) + timedelta(
        hours=priority.sla_hours, seconds=paused
    )
    if ticket.status == "waiting_customer":
        base.update(
            {
                "slaState": "paused",
                "deadline": fmt_dt(deadline),
                "waitText": "等待客户，处理时限已暂停",
                "waitLevel": "none",
            }
        )
        return base
    remaining_minutes = int((deadline - now).total_seconds() // 60)
    if now >= deadline:
        state = "overdue"
        wait_text = "当前未处理已过期"
        wait_level = "danger"
    else:
        near = remaining_minutes <= NEAR_TIMEOUT_MINUTES
        state = "warning" if near else "normal"
        wait_text = _fmt_hm(remaining_minutes)
        wait_level = "danger" if near else "normal"
    base.update(
        {
            "slaState": state,
            "deadline": fmt_dt(deadline),
            "waitText": wait_text,
            "waitLevel": wait_level,
        }
    )
    return base
