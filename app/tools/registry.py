from app.tools.tool_cards import ToolArgument, ToolCard, ToolRegistration
from app.tools.wrappers.nmap_wrapper import NmapWrapper
from app.parsers.nmap_parser import parse_nmap_output

RUN_NMAP_CARD = ToolCard(
    key="run_nmap",
    display_name="Nmap Service Scan",
    summary="Runs a local Nmap service/version scan against a single approved target.",
    approval_class="explicit_approval",
    scope_rule="single_target",
    allowed_categories=("recon",),
    arguments=(
        ToolArgument(
            name="target",
            kind="target",
            required=True,
            description="Single IPv4, IPv6, or hostname target.",
        ),
    ),
    artifacts=("nmap_stdout.txt", "nmap_stderr.txt"),
    common_followups=(
        "run_full_port_scan",
        "run_http_probe",
        "check_ssh_auth_methods",
        "run_udp_scan",
        "analyze_firewall_rules",
    ),
    failure_modes=(
        "nmap_not_installed",
        "target_out_of_scope",
        "nonzero_returncode",
        "no_open_ports_observed",
    ),
    operator_notes="Use for initial single-target reconnaissance after scope validation and explicit operator approval.",
    preconditions=(
        "Target must pass single-target scope validation.",
        "Operator must explicitly approve execution.",
        "Nmap must be installed and available in PATH.",
    ),
    postconditions=(
        "Raw stdout and stderr artifacts are saved.",
        "A tool run record is stored.",
        "Parsed findings are persisted when execution succeeds.",
        "A report is generated when execution succeeds.",
    ),
    safety_notes=(
        "Do not use against multiple targets.",
        "Do not bypass approval flow.",
        "Treat parser output as derived evidence; confirm with raw artifacts when needed.",
    ),
    argument_validation=(
        "target must be a single IPv4, IPv6, or hostname value",
    ),
)


TOOL_REGISTRY = {
    "run_nmap": ToolRegistration(
        card=RUN_NMAP_CARD,
        tool=NmapWrapper(),
        parser=parse_nmap_output,
        stores_findings=True,
        generates_report=True,
        uses_watcher=True,
    ),
}