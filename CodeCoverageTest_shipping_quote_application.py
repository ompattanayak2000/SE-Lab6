
import pytest
from shipping_quote import process_shipments, monitor_container_pressures


def test_invalid_shipments_type():
    with pytest.raises(ValueError):
        process_shipments("invalid", 10)


def test_negative_handling_fee():
    with pytest.raises(ValueError):
        process_shipments([], -5)


def test_unapproved_shipment():
    shipments = [
        {"manifest_approved": False, "mode": "ground"}
    ]
    result = process_shipments(shipments, 10)
    assert result["status"] == "NO_CARGO"


def test_invalid_transport_mode():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "sea",
            "packages": []
        }
    ]
    result = process_shipments(shipments, 10)
    assert result["status"] == "NO_CARGO"


def test_invalid_package_weight():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [{"weight_kg": 0}]
        }
    ]
    result = process_shipments(shipments, 5)
    assert result["total_quote"] == 5
    assert result["status"] == "CLEARED"


def test_hazmat_non_fragile():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": False,
            "packages": [{"weight_kg": 10, "is_hazmat": True}]
        }
    ]
    result = process_shipments(shipments, 10)
    assert result["total_quote"] == 60


def test_hazmat_fragile():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "is_fragile": True,
            "packages": [{"weight_kg": 10, "is_hazmat": True}]
        }
    ]
    result = process_shipments(shipments, 10)
    assert result["total_quote"] == 0
    assert result["status"] == "NO_CARGO"


def test_heavy_package():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [{"weight_kg": 40, "is_hazmat": False}]
        }
    ]
    result = process_shipments(shipments, 10)
    assert result["total_quote"] == 250


def test_air_express_shipment():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "air",
            "express_priority": True,
            "packages": [{"weight_kg": 2, "is_hazmat": False}]
        }
    ]
    result = process_shipments(shipments, 5)
    assert result["total_quote"] == 36.25


def test_flagged_review():
    shipments = [
        {
            "manifest_approved": True,
            "mode": "ground",
            "packages": [
                {"weight_kg": 0},
                {"weight_kg": -1},
                {"weight_kg": 0},
                {"weight_kg": -2}
            ]
        }
    ]
    result = process_shipments(shipments, 1)
    assert result["status"] == "FLAGGED_REVIEW"


def test_empty_pressure_logs():
    assert monitor_container_pressures([]) == "NO_DATA"


def test_leak_detected():
    pressure_logs = [[15.0, 13.0, 12.0]]
    assert monitor_container_pressures(pressure_logs) == "LEAK_DETECTED"


def test_stable_pressure():
    pressure_logs = [[15.0, 16.0, 15.0]]
    assert monitor_container_pressures(pressure_logs) == "STABLE"


def test_pressure_streak_reset():
    pressure_logs = [[13.0, 14.0, 13.0]]
    assert monitor_container_pressures(pressure_logs) == "STABLE"
