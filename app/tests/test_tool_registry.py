from app.tools.registry import TOOL_REGISTRY


def test_run_nmap_registry_entry_is_structured():
    entry = TOOL_REGISTRY["run_nmap"]
    card = entry.card

    assert card.key == "run_nmap"
    assert card.display_name == "Nmap Service Scan"
    assert card.approval_class == "explicit_approval"
    assert card.scope_rule == "single_target"
    assert card.allowed_categories == ("recon",)
    assert card.arguments[0].name == "target"
    assert card.arguments[0].required is True
    assert "nmap_stdout.txt" in card.artifacts
    assert "run_http_probe" in card.common_followups
    assert "Target must pass single-target scope validation." in card.preconditions
    assert "A tool run record is stored." in card.postconditions
    assert "Do not use against multiple targets." in card.safety_notes
    assert "target must be a single IPv4, IPv6, or hostname value" in card.argument_validation

    assert entry.parser is not None
    assert entry.stores_findings is True
    assert entry.generates_report is True
    assert entry.uses_watcher is True