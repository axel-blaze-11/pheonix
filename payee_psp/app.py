import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

from flask import Flask, jsonify, request, Response

from db import get_valadd_profile, init_db, seed_sample_users, seed_sample_valadd_profiles

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [payee_psp] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Set Flask's werkzeug logger to INFO to see all HTTP requests
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)

app = Flask(__name__)


# Request logging middleware
@app.before_request
def log_request():
    logger.info("==> Incoming %s %s | Content-Type: %s | Content-Length: %s | Remote: %s",
                request.method, request.path,
                request.content_type or "N/A",
                request.content_length or 0,
                request.remote_addr)
    if request.args:
        logger.info("    Query params: %s", dict(request.args))
    if request.is_json:
        logger.info("    JSON body: %s", request.get_json())


@app.after_request
def log_response(response):
    logger.info("<== Response %s %s | Status: %s | Content-Type: %s | Content-Length: %s",
                request.method, request.path,
                response.status_code,
                response.content_type or "N/A",
                response.content_length or 0)
    return response

NS = "http://npci.org/upi/schema/"

# SQLite session factory; set at startup.
_session_factory = None


def _qname(local: str) -> str:
    return f"{{{NS}}}{local}"


def _parse_reqvaladd(data: bytes) -> tuple[ET.Element, ET.Element, Optional[ET.Element]]:
    root = ET.fromstring(data)
    head = root.find(_qname("Head"))
    txn = root.find(_qname("Txn"))
    payee = root.find(_qname("Payee"))
    if head is None or txn is None:
        raise ValueError("ReqValAdd must have Head and Txn")
    return head, txn, payee


def _set_opt(elem: ET.Element, attr: str, val: Optional[str]) -> None:
    if val:
        elem.set(attr, val)


def _build_resp_valadd(
    head: ET.Element,
    txn: ET.Element,
    profile: Optional[object],
    result: str = "SUCCESS",
    fail_msg: Optional[str] = None,
) -> str:
    req_msg_id = head.get("msgId") or ""
    resp_msg_id = f"resp-{req_msg_id}" if req_msg_id else f"resp-{uuid.uuid4().hex[:12]}"
    org_id = os.environ.get("PAYEE_PSP_ORG_ID", "PAYEE_PSP")
    if profile and getattr(profile, "org_id", None):
        org_id = profile.org_id
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    root = ET.Element(_qname("RespValAdd"))

    h = ET.SubElement(root, _qname("Head"))
    h.set("ver", head.get("ver") or "2.0")
    h.set("ts", ts)
    h.set("orgId", org_id)
    h.set("msgId", resp_msg_id)
    h.set("prodType", head.get("prodType") or "UPI")

    t = ET.SubElement(root, _qname("Txn"))
    t.set("id", txn.get("id") or "")
    t.set("type", txn.get("type") or "VALADD")
    for attr in ("ts", "note", "custRef", "refId", "refUrl"):
        val = txn.get(attr)
        if val is not None:
            t.set(attr, val)

    resp = ET.SubElement(root, _qname("Resp"))
    resp.set("reqMsgId", req_msg_id)
    resp.set("result", result)
    if fail_msg:
        resp.set("failMsg", fail_msg)
    if profile:
        _set_opt(resp, "maskName", getattr(profile, "mask_name", None))
        _set_opt(resp, "code", getattr(profile, "code", None))
        _set_opt(resp, "type", getattr(profile, "type", None))
        _set_opt(resp, "IFSC", getattr(profile, "ifsc", None))
        _set_opt(resp, "accType", getattr(profile, "acc_type", None))
        _set_opt(resp, "IIN", getattr(profile, "iin", None))
        _set_opt(resp, "pType", getattr(profile, "p_type", None))
        # Merchant (optional)
        if any(
            getattr(profile, a, None)
            for a in (
                "mid", "sid", "tid", "merchant_type", "merchant_genre",
                "pin_code", "reg_id_no", "tier", "on_boarding_type",
                "brand_name", "legal_name", "franchise_name", "ownership_type",
            )
        ):
            m = ET.SubElement(resp, _qname("Merchant"))
            if any(getattr(profile, a, None) for a in ("mid", "sid", "tid", "merchant_type", "merchant_genre", "pin_code", "reg_id_no", "tier", "on_boarding_type")):
                ident = ET.SubElement(m, _qname("Identifier"))
                _set_opt(ident, "mid", getattr(profile, "mid", None))
                _set_opt(ident, "sid", getattr(profile, "sid", None))
                _set_opt(ident, "tid", getattr(profile, "tid", None))
                _set_opt(ident, "merchantType", getattr(profile, "merchant_type", None))
                _set_opt(ident, "merchantGenre", getattr(profile, "merchant_genre", None))
                _set_opt(ident, "pinCode", getattr(profile, "pin_code", None))
                _set_opt(ident, "regIdNo", getattr(profile, "reg_id_no", None))
                _set_opt(ident, "tier", getattr(profile, "tier", None))
                _set_opt(ident, "onBoardingType", getattr(profile, "on_boarding_type", None))
            if any(getattr(profile, a, None) for a in ("brand_name", "legal_name", "franchise_name")):
                name = ET.SubElement(m, _qname("Name"))
                _set_opt(name, "brand", getattr(profile, "brand_name", None))
                _set_opt(name, "legal", getattr(profile, "legal_name", None))
                _set_opt(name, "franchise", getattr(profile, "franchise_name", None))
            if getattr(profile, "ownership_type", None):
                own = ET.SubElement(m, _qname("Ownership"))
                _set_opt(own, "type", getattr(profile, "ownership_type", None))
        # FeatureSupported (optional)
        if getattr(profile, "feature_supported", None):
            fs = ET.SubElement(resp, _qname("FeatureSupported"))
            fs.set("value", profile.feature_supported)

    xml_str = ET.tostring(root, encoding="unicode", method="xml")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str


@app.get("/health")
def health() -> tuple[dict, int]:
    return jsonify(status="ok"), 200


@app.post("/api/reqvaladd")
def reqvaladd() -> tuple[Response | dict, int]:
    """
    Receive ReqValAdd from NPCI; send RespValAdd to NPCI (as HTTP response).
    Look up ValAddProfile by Payee.addr (VPA) in SQLite; build Resp from DB. upi_req_valadd.xsd, upi_resp_valadd.xsd.
    """
    if not request.data:
        return jsonify(error="Missing body"), 400
    try:
        head, txn, payee = _parse_reqvaladd(request.data)
    except ET.ParseError as e:
        return jsonify(error=f"Invalid XML: {e}"), 400
    except ValueError as e:
        return jsonify(error=str(e)), 400

    if _session_factory is None:
        _startup()
    vpa = (payee.get("addr") or "").strip() if payee is not None else ""
    profile = None
    if vpa:
        session = _session_factory()
        try:
            profile = get_valadd_profile(session, vpa)
            logger.info("[payee_psp] Processing ReqValAdd for VPA: %s | Profile found: %s", vpa, profile is not None)
        finally:
            session.close()

    # New validation rule: block payees with code == "1111"
    if profile and getattr(profile, "code", None) == "1111":
        logger.info("[payee_psp] Payee code 1111 blocked; rejecting.")
        body = _build_resp_valadd(head, txn, profile, result="FAILURE", fail_msg="Code Blocked for Demo")
        return Response(body, status=200, mimetype="application/xml")

    # Validation: minimum transaction amount must be >= 1 Rs
    amount_str = txn.get("amount")
    if amount_str:
        try:
            amount = float(amount_str)
            if amount < 1:
                logger.info("[payee_psp] Transaction amount %s below minimum 1 Rs; rejecting.", amount_str)
                body = _build_resp_valadd(head, txn, profile, result="FAILURE")
                return Response(body, status=200, mimetype="application/xml")
        except ValueError:
            logger.warning("[payee_psp] Invalid amount format: %s", amount_str)
            # proceed without amount validation

    body = _build_resp_valadd(head, txn, profile)
    logger.info("[payee_psp] Sending RespValAdd | VPA: %s | Result: %s", vpa, "SUCCESS" if profile else "NOT_FOUND")
    return Response(body, status=200, mimetype="application/xml")


# ============================================================================
# Phase 2: AI Agent Integration
# ============================================================================

_payee_psp_agent = None


def _get_payee_psp_agent():
    """Get Payee PSP Agent instance (lazy initialization)."""
    global _payee_psp_agent
    if _payee_psp_agent is None:
        try:
            from agents import PayeePSPAgent
            from llm import LLM

            try:
                llm = LLM(
                    model=os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    base_url=os.environ.get("LLM_BASE_URL"),
                )
                logger.info("[Payee PSP Agent] LLM initialized")
            except Exception as e:
                logger.warning(f"[Payee PSP Agent] LLM initialization failed: {e}, using fallback mode")
                llm = None

            _payee_psp_agent = PayeePSPAgent(llm_instance=llm)
            logger.info(f"[Payee PSP Agent] Initialized: {_payee_psp_agent.agent_name}")
        except ImportError as e:
            logger.error(f"[Payee PSP Agent] Failed to import agent infrastructure: {e}")
            _payee_psp_agent = None
    return _payee_psp_agent


@app.post("/api/agent/manifest")
def receive_manifest_endpoint():
    """Receive manifest via A2A protocol."""
    agent = _get_payee_psp_agent()
    if not agent:
        return jsonify(error="Payee PSP Agent not available"), 503

    data = request.json
    if not data:
        return jsonify(error="Missing request body"), 400

    try:
        from manifest import ChangeManifest

        payload = data.get("payload", {})
        manifest_dict = payload.get("manifest", {})

        if not manifest_dict:
            return jsonify(error="Missing manifest in payload"), 400

        manifest = ChangeManifest.from_dict(manifest_dict)

        result = agent.receive_manifest(manifest)

        try:
            import requests
            orchestrator_url = os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:6000")
            try:
                requests.post(
                    f"{orchestrator_url}/api/orchestrator/status",
                    json={
                        "change_id": manifest.change_id,
                        "agent_id": agent.agent_id,
                        "status": "RECEIVED",
                        "details": f"Received manifest: '{manifest.description[:100]}'"
                    },
                    timeout=2,
                )
            except Exception:
                requests.post(
                    "http://localhost:9991/api/orchestrator/status",
                    json={
                        "change_id": manifest.change_id,
                        "agent_id": agent.agent_id,
                        "status": "RECEIVED",
                        "details": f"Received manifest: '{manifest.description[:100]}'"
                    },
                    timeout=2,
                )
        except Exception as e:
            logger.warning(f"Failed to update orchestrator: {e}")

        try:
            process_result = agent.process_manifest(manifest)

            try:
                import requests
                orchestrator_url = os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:6000")
                final_message = process_result.get("message", "")
                if not final_message:
                    applied_count = len(process_result.get("applied_changes", []))
                    final_message = f"Processing complete. {applied_count} file(s) updated successfully."

                requests.post(
                    f"{orchestrator_url}/api/orchestrator/status",
                    json={
                        "change_id": manifest.change_id,
                        "agent_id": agent.agent_id,
                        "status": process_result.get("status", "RECEIVED"),
                        "details": {"message": final_message, **process_result},
                    },
                    timeout=5,
                )
            except Exception as e:
                logger.warning(f"[Payee PSP Agent] Failed to update orchestrator: {e}")

            return jsonify(process_result), 200
        except Exception as e:
            logger.error(f"[Payee PSP Agent] Error processing manifest: {e}")
            return jsonify({**result, "processing_error": str(e)}), 200

    except Exception as e:
        logger.error(f"[Payee PSP Agent] Error receiving manifest: {e}")
        return jsonify(error=str(e)), 500


@app.get("/api/agent/status/<change_id>")
def get_agent_status(change_id: str):
    """Get agent status for a specific change."""
    agent = _get_payee_psp_agent()
    if not agent:
        return jsonify(error="Payee PSP Agent not available"), 503

    status = agent.get_status(change_id)
    if status:
        return jsonify(status), 200
    return jsonify(error="Change not found"), 404


def _startup() -> None:
    global _session_factory
    _session_factory = init_db()
    session = _session_factory()
    try:
        seed_sample_valadd_profiles(session)
        seed_sample_users(session)
    finally:
        session.close()


if __name__ == "__main__":
    _startup()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
