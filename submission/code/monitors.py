"""★ FILE ĐỘI SỬA (2/3): chỉ số theo dõi (monitor). Thêm ÍT NHẤT MỘT chỉ số bắt được sự cố của bàn.

Mỗi monitor nhận danh sách trial (KHÔNG có nhãn đúng/sai, giống production) và trả về một số.
Một trial = {"ticket_id", "seed", "day", "status", "amount_vnd", "ticket", "events", "ledger", "faults", "outbound",
             "arrive_min", "warehouse", "cost_vnd", "review_kind", "queue_wait_min", "queue_stuck"}
  "day"            một ngày vận hành giả lập: các ticket cùng "day" và cùng "seed" chạy nối nhau trên cùng một sổ cái
  "arrive_min"     phút ticket tới trong ca (0..480)          "warehouse"   kho của đơn
  "cost_vnd"       tiền LLM + nền tảng đã tốn cho ticket      "review_kind" None / "escalated" (trợ lý chuyển người) /
  "queue_wait_min" số phút chờ người duyệt (None nếu không vào hàng chờ)     "recheck" (nhân viên tự kiểm lại)
Chỉ số có thể là kỹ thuật (tỉ lệ model đè số trong ticket lên DB), vận hành (số ca cần người trong giờ đông nhất),
hay kinh doanh (tỉ lệ ticket trợ lý đọc xong vẫn phải chuyển người).

lab10.grade kiểm: monitor chạy không lỗi, và giá trị trên gói sự cố khác giá trị trên bộ nền,
tức là monitor "sáng đèn" khi sự cố xảy ra.
"""


def escalation_rate(trials):
    return sum(t["status"] == "escalated" for t in trials) / max(1, len(trials))


# ---------------- chỉ số của bàn Siuuuu (không dùng nhãn; chỉ đọc trace, sổ cái, sổ lỗi, thông báo đi) ----------------

def _has(t, kind, **kw):
    return any(e.get("type") == kind and all(e.get(k) == v for k, v in kw.items()) for e in t.get("events", []))


def claim_override_rate(trials):
    """Kỹ thuật: tỉ lệ lần chạy mà model lấy số ngày khách tự khai đè lên tracking DB (sự kiện model_override)."""
    return sum(_has(t, "model_override") for t in trials) / max(1, len(trials))


def gate_intervention_rate(trials):
    """Kỹ thuật/vận hành: tỉ lệ lần chạy mà một cổng (code, config, pháp lý) phải chặn / sửa / chuyển người.
    Tăng vọt = đầu vào đổi (sự cố, drift) dù pass_rate có thể vẫn đẹp."""
    def hit(e):   # bỏ qua việc G3 lọc trường thông báo cho hãng: việc đó xảy ra ở mọi ca có ghi lỗi, không phải bất thường
        if e.get("type") == "gate":
            return e.get("tool") in ("issue_refund", "file_carrier_fault")
        return e.get("type") in ("pre_guard", "business_gate", "host_denied")
    return sum(any(hit(e) for e in t.get("events", [])) for t in trials) / max(1, len(trials))


def llm_error_rate(trials):
    """Hạ tầng: tỉ lệ lần chạy có lỗi LLM (429) hoặc phải dùng đường dự phòng."""
    return sum(_has(t, "llm_error") or _has(t, "llm_fallback") for t in trials) / max(1, len(trials))


def faults_without_recorded_cause(trials):
    """Pháp lý (bên thứ ba): số lỗi hãng đã ghi mà tracking không có nguyên nhân ghi sẵn."""
    n = 0
    for t in trials:
        tr = next((e for e in t.get("events", []) if e.get("type") == "tracking"), {})
        if t.get("faults") and tr and not tr.get("cause_recorded", True):
            n += len(t["faults"])
    return n


def max_strikes_per_carrier_day(trials):
    """Vận hành: số lỗi nhiều nhất ghi cho MỘT hãng trong MỘT ngày giả lập (so với trần 2 lỗi/hãng/ngày)."""
    cnt = {}
    for t in trials:
        for f in t.get("faults") or []:
            k = (t.get("seed"), t.get("day"), f.get("carrier_id"))
            cnt[k] = cnt.get(k, 0) + 1
    return max(cnt.values(), default=0)


def outbound_pii_fields(trials):
    """Pháp lý: số thông báo gửi hãng còn chứa trường ngoài danh sách tối thiểu (tên/SĐT người nhận, chữ khách gõ)."""
    allowed = {"order_id", "parcel_id", "district", "delay_days"}
    return sum(1 for t in trials for m in t.get("outbound") or []
               if str(m.get("to", "")).startswith("carrier:") and set(m.get("payload") or {}) - allowed)


def review_peak_per_hour(trials):
    """Vận hành: số ca cần người (chuyển người + kiểm lại) nhiều nhất trong một giờ của một ngày giả lập."""
    cnt = {}
    for t in trials:
        if t.get("review_kind"):
            k = (t.get("seed"), t.get("day"), int((t.get("arrive_min") or 0) // 60))
            cnt[k] = cnt.get(k, 0) + 1
    return max(cnt.values(), default=0)


MONITORS = {
    "escalation_rate": escalation_rate,     # có sẵn; KHÔNG tính là metric mới của đội
    "claim_override_rate": claim_override_rate,
    "gate_intervention_rate": gate_intervention_rate,
    "llm_error_rate": llm_error_rate,
    "faults_without_recorded_cause": faults_without_recorded_cause,
    "max_strikes_per_carrier_day": max_strikes_per_carrier_day,
    "outbound_pii_fields": outbound_pii_fields,
    "review_peak_per_hour": review_peak_per_hour,
}
STARTER_MONITORS = ("escalation_rate",)
