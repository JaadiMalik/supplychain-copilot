import re


SIGNALS = {
    "purchase_order_analysis": [
        r"\bpurchase\s+order",
        r"\bpo(?:s)?\b",
        r"\bopen\s+orders?\b",
        r"\boutstanding\s+orders?\b",
    ],
    "shipment_analysis": [
        r"\bshipment",
        r"\bdelivery",
        r"\bdelayed\b",
        r"\bin[\s-]+transit\b",
        r"\botif\b",
    ],
    "inventory_analysis": [
        r"\binventory\b",
        r"\bstock\b",
        r"\breorder\b",
        r"\bsku\b",
    ],
    "contract_analysis": [
        r"\bcontract",
        r"\bagreement",
        r"\bclause",
        r"\bpayment\s+term",
        r"\bpenalt",
        r"\bwarranty\b",
        r"\btermination\b",
        r"\bsla\b",
    ],
    "supplier_analysis": [
        r"\bsupplier",
        r"\bvendor",
        r"\bprocurement\b",
    ],
}


def _matched_signals(
    question: str,
    patterns: list[str],
) -> list[str]:
    text = question.casefold()
    found = []

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            found.append(match.group(0))

    return found


def resolve_intent(question: str) -> dict:
    found = {
        intent: _matched_signals(
            question,
            patterns,
        )
        for intent, patterns in SIGNALS.items()
    }

    shipment_operational_signals = [
        signal
        for signal in found["shipment_analysis"]
        if signal != "delivery"
    ]

    purchase_order_signals = (
        found["purchase_order_analysis"]
    )

    inventory_signals = (
        found["inventory_analysis"]
    )

    contract_signals = (
        found["contract_analysis"]
    )

    supplier_signals = (
        found["supplier_analysis"]
    )

    has_operational = bool(
        purchase_order_signals
        or shipment_operational_signals
        or inventory_signals
    )

    has_contract = bool(
        contract_signals
    )

    if has_operational and has_contract:
        signals = (
            purchase_order_signals
            + shipment_operational_signals
            + inventory_signals
            + contract_signals
            + supplier_signals
        )

        return {
            "name": "combined_operational_contract_analysis",
            "confidence": 1.0,
            "signals": sorted(set(signals)),
        }

    if purchase_order_signals:
        return {
            "name": "purchase_order_analysis",
            "confidence": 0.9,
            "signals": sorted(
                set(purchase_order_signals)
            ),
        }

    if shipment_operational_signals:
        return {
            "name": "shipment_analysis",
            "confidence": 0.9,
            "signals": sorted(
                set(shipment_operational_signals)
            ),
        }

    if inventory_signals:
        return {
            "name": "inventory_analysis",
            "confidence": 0.9,
            "signals": sorted(
                set(inventory_signals)
            ),
        }

    if contract_signals:
        return {
            "name": "contract_analysis",
            "confidence": 0.9,
            "signals": sorted(
                set(contract_signals)
            ),
        }

    if supplier_signals:
        return {
            "name": "supplier_analysis",
            "confidence": 0.8,
            "signals": sorted(
                set(supplier_signals)
            ),
        }

    return {
        "name": "general_supplychain_question",
        "confidence": 0.5,
        "signals": [],
    }
