
import pytest
from shipping_quote import process_shipments, monitor_container_pressures


# 1. Input validation branches

def test_empty_shipments_list():
    result = process_shipments([], 10)
    assert result == {"total_quote": 0.0, "status": "NO_CARGO"}


def test_invalid_shipments_and_negative_fee():
    with pytest.raises(ValueError):
        process_shipments("invalid", -5)


# 2. Manifest approval branches

def test_approved_and_unapproved_shipments():
    shipments = [
        {"manifest_approved": True, "mode": "ground", "packages": []},
        {"manifest_approved": False, "mode": "air", "packages": []}
    ]
    result = process_shipments(shipments, 10)
    assert result["total_quote"] == 10
    assert result["status"] == "CLEARED"


# 3. Transport mode branches

def test_air_transport():
    shipments = [{
        "manifest_approved": True,
        "mode": "air",
        "packages": [{"weight_kg": 5}]
    }]
    result = process_shipments(shipments, 10)
    assert result["total_quote"] == 70


def test_ground_transport():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [{"weight_kg": 5}]
    }]
    result = process_shipments(shipments, 10)
    assert result["total_quote"] == 30


def test_unsupported_transport_mode():
    shipments = [{
        "manifest_approved": True,
        "mode": "sea",
        "packages": [{"weight_kg": 5}]
    }]
    result = process_shipments(shipments, 10)
    assert result["status"] == "NO_CARGO"


# 4. Package loop and weight branches

def test_shipment_with_no_packages():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": []
    }]
    result = process_shipments(shipments, 10)
    assert result["total_quote"] == 10


def test_zero_and_negative_weights():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [
            {"weight_kg": 0},
            {"weight_kg": -5}
        ]
    }]
    result = process_shipments(shipments, 10)
    assert result["status"] == "CLEARED"
    assert result["total_quote"] == 10


def test_weight_exactly_30_kg():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [{"weight_kg": 30}]
    }]
    result = process_shipments(shipments, 0)
    assert result["total_quote"] == 120


def test_weight_above_30_kg():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [{"weight_kg": 31}]
    }]
    result = process_shipments(shipments, 0)
    assert result["total_quote"] == 186


# 5. Hazardous material and fragile branches

def test_non_hazmat_package():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "is_fragile": False,
        "packages": [{"weight_kg": 10, "is_hazmat": False}]
    }]
    result = process_shipments(shipments, 0)
    assert result["total_quote"] == 40


def test_hazmat_non_fragile_package():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "is_fragile": False,
        "packages": [{"weight_kg": 10, "is_hazmat": True}]
    }]
    result = process_shipments(shipments, 0)
    assert result["total_quote"] == 50


def test_hazmat_fragile_stops_package_processing():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "is_fragile": True,
        "packages": [
            {"weight_kg": 10, "is_hazmat": True},
            {"weight_kg": 5, "is_hazmat": False}
        ]
    }]
    result = process_shipments(shipments, 0)
    assert result["total_quote"] == 0
    assert result["status"] == "NO_CARGO"


# 6. Express priority branches

def test_express_priority_enabled():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "express_priority": True,
        "packages": [{"weight_kg": 10}]
    }]
    result = process_shipments(shipments, 0)
    assert result["total_quote"] == 50


def test_express_priority_disabled():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "express_priority": False,
        "packages": [{"weight_kg": 10}]
    }]
    result = process_shipments(shipments, 0)
    assert result["total_quote"] == 40


# 7. Rejected parcel and final status branches

def test_exactly_three_rejected_parcels():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [
            {"weight_kg": 0},
            {"weight_kg": -1},
            {"weight_kg": 0}
        ]
    }]
    result = process_shipments(shipments, 5)
    assert result["status"] == "CLEARED"


def test_more_than_three_rejected_parcels():
    shipments = [{
        "manifest_approved": True,
        "mode": "ground",
        "packages": [
            {"weight_kg": 0},
            {"weight_kg": -1},
            {"weight_kg": 0},
            {"weight_kg": -2}
        ]
    }]
    result = process_shipments(shipments, 5)
    assert result["status"] == "FLAGGED_REVIEW"


# 8. Container pressure monitoring branches

def test_empty_pressure_logs():
    assert monitor_container_pressures([]) == "NO_DATA"


def test_empty_container_readings():
    assert monitor_container_pressures([[]]) == "STABLE"


def test_single_low_pressure_reading():
    assert monitor_container_pressures([[13.0]]) == "STABLE"


def test_two_consecutive_low_pressure_readings():
    assert monitor_container_pressures([[13.0, 12.0]]) == "LEAK_DETECTED"


def test_normal_pressure_resets_low_pressure_streak():
    assert monitor_container_pressures(
        [[13.0, 15.0, 13.0, 14.0]]
    ) == "STABLE"


def test_leak_in_later_container():
    assert monitor_container_pressures(
        [[15.0, 16.0], [13.0, 12.0]]
    ) == "LEAK_DETECTED"
