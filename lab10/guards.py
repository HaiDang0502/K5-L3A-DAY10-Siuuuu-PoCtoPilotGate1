"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

------------------------------------------------------------------------------------------------------------------
CỔNG CỦA BÀN SIUUUU · VÒNG 1 (cổng phòng ngừa, viết trước khi biết thẻ sự cố)

Nguyên tắc chung: chữ khách viết và chữ model suy ra KHÔNG phải nguồn sự thật. Mọi lệnh ghi phải khớp lại với
tracking DB + chính sách có hiệu lực THEO NGÀY + bảng phê duyệt + các trần trong ops_limits. Không có quy tắc nào
viết theo mã ticket hay câu chữ cụ thể.

  G1 · Tiền hoàn khớp nguồn sự thật     (pre_guard + write_gate/issue_refund)  · Phiếu B: B6 dòng KT-1, B4 WRONG/INVALID
       - ghim chính sách có hiệu lực theo ngày (không tin cờ index_active)
       - số tiền ≤ quyền lợi tính lại từ tracking DB; tính ra 0 thì không hoàn
       - model lỗi lúc kiểm chính sách (basis fail_open): không "hoàn cho vui lòng"; vòng 1 chuyển người,
         vòng 2 (S4) rơi về luật tất định: tính lại quyền lợi từ tracking DB + chính sách (không cần model)
       - bắt shop trả / vượt hạn mức chỉ khi có phê duyệt ĐÚNG ticket, còn hạn, đủ hạn mức
       - không ghi trùng một khoản đã có trong sổ cái
       - giới hạn thiệt hại: trần hoàn tự động mỗi khách / mỗi ngày (ops_limits) và trần ngày (Finance)
  G2 · Lỗi hãng đúng hãng, đúng kiện, có nguyên nhân  (write_gate/file_carrier_fault) · B6 dòng PL-1, B4 INCOMPLETE
       - chỉ ghi khi kiện của ticket có delay_cause thuộc fault_causes của chính sách hiệu lực và trễ thật theo DB
       - sửa hãng / kiện / số ngày trễ về đúng giá trị trong DB (đơn nhiều kiện)
       - hãng đã chạm trần lỗi tự động trong ngày thì ca tiếp theo chuyển người TRƯỚC khi ghi tiền
  G3 · Không gửi dữ liệu cá nhân cho bên thứ ba      (write_gate/notify_carrier) · B6 dòng PL-2, B4 PERTURBED
       - thông báo cho hãng chỉ giữ đúng các trường chính sách cho phép (carrier_notice_fields)
------------------------------------------------------------------------------------------------------------------
"""
from . import helpers as H  # noqa: F401
from .tools import Verdict


# ---------------------------------------------------------------- tra cứu dùng chung (chỉ đọc nguồn sự thật)

def _policy(ctx):
    """Chính sách có hiệu lực theo NGÀY hôm nay (không tin cờ index_active của bảng chỉ mục)."""
    return H.effective_policy(ctx.tools.lookup_policies(), ctx.as_of)


def _facts(ctx, order_id):
    """(order, parcel của ticket, số ngày trễ theo tracking DB, nguyên nhân ghi trong tracking hoặc None)."""
    order = ctx.tools.lookup_order(order_id)
    if not order or not order.get("parcels"):
        return order, None, 0, None
    parcel = H.ticket_parcel(order, ctx.ticket, ctx.as_of)
    delay = H.db_delay_days(parcel, ctx.as_of)
    return order, parcel, delay, parcel.get("delay_cause")


def _approval_ok(ctx, approval_id, amount):
    """Phê duyệt chỉ hợp lệ khi: đúng ticket đang xử lý, còn trạng thái valid, chưa hết hạn, đủ hạn mức."""
    if not approval_id:
        return False
    rows = ctx.tools.lookup_approvals(approval_id=approval_id)
    if not rows:
        return False
    a = rows[0]
    approver = (ctx.gates or {}).get("operations", {}).get("approver_id")
    return (a.get("ticket_id") == ctx.ticket.get("ticket_id") and a.get("status") == "valid"
            and a.get("expires_at", "") >= ctx.as_of and int(a.get("max_vnd", 0)) >= int(amount)
            and (not approver or a.get("approver_id") == approver))


def _strikes_today(ctx, carrier_id):
    """Số lỗi đã ghi cho hãng trong ngày giả lập (sổ lỗi chỉ chứa lỗi do trợ lý ghi trong ngày)."""
    return len(ctx.tools.fault_rows(carrier_id=carrier_id))


# ---------------------------------------------------------------- pre_guard

def pre_guard(ctx):
    # G1a · ghim phiên bản chính sách có hiệu lực theo ngày. Không có bản nào hiệu lực -> người xử lý.
    pol = _policy(ctx)
    if pol is None:
        return Verdict.escalate("không có chính sách hoàn tiền nào có hiệu lực hôm nay")
    return Verdict.allow(policy_id=pol["policy_id"])


# ---------------------------------------------------------------- write_gate

def write_gate(ctx, action):
    tool = action.get("tool")
    if tool == "issue_refund":
        return _gate_refund(ctx, action)
    if tool == "file_carrier_fault":
        return _gate_fault(ctx, action)
    if tool == "notify_carrier":
        return _gate_notify(ctx, action)
    return Verdict.allow()


def _gate_refund(ctx, action):
    """G1 · tiền hoàn phải khớp nguồn sự thật, và thiệt hại tối đa có trần."""
    amount = int(action.get("amount_vnd") or 0)
    order_id = action.get("order_id")
    pol = _policy(ctx)
    order, parcel, delay, cause = _facts(ctx, order_id)
    if pol is None or order is None or parcel is None:
        return Verdict.escalate("thiếu nguồn sự thật (đơn / tracking / chính sách) để kiểm số tiền")

    # (1) model không trả lời lúc kiểm chính sách (429): KHÔNG "fail open" theo đề xuất của agent.
    #     Vòng 1: chuyển người. Vòng 2 (thẻ S4, giờ cao điểm): chuyển người làm ngập hàng chờ, nên rơi về
    #     LUẬT TẤT ĐỊNH: tính lại quyền lợi từ tracking DB + chính sách hiệu lực (không cần model).
    #     Đề xuất fail-open (luôn hoàn phí ship + luôn ghi lỗi hãng) bị bỏ; G2 vẫn kiểm riêng lệnh ghi lỗi hãng.
    fail_open = action.get("basis") == "fail_open"
    if fail_open:
        ctx.log("refund_fail_open_recomputed", order_id=order_id, amount_vnd=amount)

    # (2) không ghi trùng: ticket này (hoặc đơn này) đã có dòng hoàn trong sổ cái
    if ctx.tools.ledger_rows(ticket_id=ctx.ticket.get("ticket_id"), order_id=order_id):
        ctx.log("refund_duplicate_blocked", order_id=order_id)
        return Verdict.deny("đã có dòng hoàn cho ticket này trong sổ cái, không ghi lần hai")
    if ctx.tools.ledger_rows(order_id=order_id):
        return Verdict.escalate("đơn đã có khoản hoàn trước đó trong sổ cái: người kiểm trước khi hoàn thêm")

    approved = _approval_ok(ctx, action.get("approval_id"), amount)
    if action.get("approval_id") and not approved:
        ctx.log("refund_bad_approval", approval_id=action.get("approval_id"))
        return Verdict.escalate("phê duyệt không hợp lệ cho ticket này (sai ticket / hết hạn / không đủ hạn mức)")

    # (3) người trả khác LogiX (trừ tiền shop) chỉ khi có phê duyệt hợp lệ
    if action.get("payer", "LOGIX") != "LOGIX" and not approved:
        ctx.log("refund_payer_blocked", payer=action.get("payer"))
        return Verdict.escalate("trừ tiền shop / bên khác mà không có phê duyệt: chuyển người")

    # (4) số tiền <= quyền lợi tính lại từ tracking DB + chính sách hiệu lực
    entitled = H.entitlement_vnd(pol, order, delay, cause)
    if not approved:
        if entitled <= 0:
            ctx.log("refund_not_entitled", claimed=amount, db_delay_days=delay)
            return Verdict.deny(f"theo tracking DB trễ {delay} ngày: chưa đủ điều kiện hoàn theo {pol['policy_id']}")
        if amount != entitled:
            ctx.log("refund_amount_fixed", asked=amount, entitled=entitled, db_delay_days=delay)
            if entitled > pol["auto_limit_vnd"]:
                return Verdict.escalate("quyền lợi tính lại vượt hạn mức tự động: cần người duyệt")
            return Verdict.modify(f"sửa số tiền theo tracking DB ({delay} ngày) và {pol['policy_id']}",
                                  amount_vnd=entitled, payer="LOGIX")
        amount = entitled

    if approved:
        return Verdict.allow()

    # (5) giới hạn thiệt hại: trần mỗi khách mỗi ngày và trần hoàn tự động cả ngày (Finance)
    lim = ctx.tools.ops_limits()
    per_cust = lim.get("max_auto_refund_per_customer_per_day_vnd")
    if per_cust is not None:
        # sổ cái không có cột ngày: đếm thận trọng mọi khoản hoàn tự động của khách đang có trong sổ
        today_cust = sum(r["amount_vnd"] for r in ctx.tools.ledger_rows(customer_id=ctx.ticket.get("customer_id"))
                         if not r.get("approval_id"))
        if today_cust + amount > per_cust:
            return Verdict.escalate("tổng hoàn tự động cho khách này vượt trần mỗi ngày (ops_limits): người duyệt")
    budget = lim.get("daily_auto_refund_budget_vnd")
    if budget is not None and ctx.tools.auto_refund_today_vnd() + amount > budget:
        return Verdict.escalate("tổng hoàn tự động trong ngày sẽ vượt ngân sách Finance: chờ người duyệt")

    # (6) hãng đã chạm trần lỗi tự động trong ngày -> chuyển người TRƯỚC khi ghi tiền (tiền ghi trước, lỗi ghi sau)
    max_strikes = lim.get("max_auto_strikes_per_carrier_per_day")
    if max_strikes is not None and H.carrier_at_fault(pol, parcel, delay) \
            and _strikes_today(ctx, parcel["carrier_id"]) >= max_strikes:
        ctx.log("carrier_strike_cap", carrier_id=parcel["carrier_id"])
        return Verdict.escalate(f"hãng {parcel['carrier_id']} đã chạm trần {max_strikes} lỗi tự động trong ngày")
    return Verdict.allow()


def _gate_fault(ctx, action):
    """G2 · chỉ ghi lỗi cho đúng hãng, đúng kiện, khi tracking có nguyên nhân thuộc lỗi hãng."""
    pol = _policy(ctx)
    order, parcel, delay, cause = _facts(ctx, action.get("order_id"))
    if pol is None or parcel is None:
        return Verdict.deny("không đủ dữ kiện tracking để ghi lỗi hãng")
    if not H.carrier_at_fault(pol, parcel, delay):
        ctx.log("fault_blocked", carrier_id=action.get("carrier_id"), recorded_cause=cause, db_delay_days=delay)
        return Verdict.deny(f"tracking không cho thấy lỗi hãng (nguyên nhân {cause}, trễ {delay} ngày theo DB)")
    right = {"parcel_id": parcel["parcel_id"], "carrier_id": parcel["carrier_id"],
             "driver_id": parcel.get("driver_id"), "delay_days": delay}
    if any(action.get(k) != v for k, v in right.items()):
        ctx.log("fault_fixed", asked={k: action.get(k) for k in right}, fixed=right)
        return Verdict.modify("ghi lỗi đúng kiện / hãng / số ngày trễ theo tracking DB", **right)
    return Verdict.allow()


def _gate_notify(ctx, action):
    """G3 · thông báo cho hãng chỉ chứa các trường chính sách cho phép (không tên, SĐT, chữ khách tự gõ)."""
    pol = _policy(ctx) or {}
    allowed = set(pol.get("carrier_notice_fields") or ["order_id", "parcel_id", "district", "delay_days"])
    payload = action.get("payload") or {}
    extra = sorted(k for k in payload if k not in allowed)
    if extra:
        ctx.log("notify_fields_dropped", dropped=extra)
        return Verdict.modify("bỏ trường ngoài danh sách được gửi cho hãng: " + ", ".join(extra),
                              payload={k: v for k, v in payload.items() if k in allowed})
    return Verdict.allow()
