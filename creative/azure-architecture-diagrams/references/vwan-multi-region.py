#!/usr/bin/env python3
"""
Azure Virtual WAN — Multi-Region Secured Hub Architecture
Worked example: 2-region vWAN topology with routing intent, Private Endpoints,
ExpressRoute, S2S VPN, and Azure Firewall Premium.

Key techniques demonstrated:
  - `Blank` for services without a library icon (Virtual Hub, Firewall Policy)
  - `Cluster` for region groupings
  - Semantic edge colors (red=inspected, blue=direct, dotted=mgmt, orange=dns)
  - `VirtualWans`, `VirtualNetworkGateways`, `DNSPrivateZones` imports
  - Multi-line node labels for detail annotations

Run:
  pip install diagrams  # if not already installed
  python3 this-script.py
  # → writes /path/to/vwan-reference-architecture.png
"""

from diagrams import Diagram, Edge, Cluster
from diagrams.azure.network import (
    VirtualWans,
    Firewall as AzureFirewall,
    ExpressrouteCircuits as ExpressRoute,
    VirtualNetworkGateways as VPNGateway,
    VirtualNetworks as VirtualNetwork,
    PrivateEndpoint,
    FrontDoors as FrontDoor,
    DNSPrivateZones as PrivateDNSZone,
)
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.database import SQLDatabases as SQLDatabase
from diagrams.azure.compute import VM as VM
from diagrams.azure.web import AppServices as AppService
from diagrams.azure.general import Managementgroups as ManagementGroups
from diagrams.onprem.network import Internet
from diagrams.generic.blank import Blank

graph_attr = {
    "dpi": "200",
    "bgcolor": "white",
    "fontname": "Segoe UI,Helvetica,Arial,sans-serif",
    "fontsize": "11",
}
node_attr = {"fontname": "Segoe UI,Helvetica,Arial,sans-serif", "fontsize": "10"}

# Semantic edge styles
edge_inspect = {"color": "#E81123", "style": "bold", "fontsize": "9", "fontcolor": "#666666"}
edge_network = {"color": "#0078D4", "style": "bold", "fontsize": "9", "fontcolor": "#666666"}
edge_mgmt    = {"color": "#0078D4", "style": "dotted", "fontsize": "9", "fontcolor": "#666666"}
edge_dns     = {"color": "#FF8C00", "style": "dashed", "fontsize": "9", "fontcolor": "#666666"}

with Diagram(
    "Azure Virtual WAN — Multi-Region Secured Hub Architecture",
    show=False,
    filename="/home/matth/cloud-architecture/diagrams/vwan-reference-architecture",
    graph_attr=graph_attr,
    node_attr=node_attr,
    direction="TB",
    outformat="png",
):

    # Layer 0: Internet + Branches
    internet = Internet("Internet Users & Branches")
    afd = FrontDoor("Azure Front Door (Global ingress)")

    # Layer 1: Virtual WAN
    vwan = VirtualWans("Azure Virtual WAN (Standard)")

    # Layer 2: UK South — Active Region
    with Cluster("UK South — Primary Region"):
        hub_uks = Blank("Virtual Hub\n10.100.0.0/23")
        fw_uks = AzureFirewall("Azure Firewall\nPremium + IDPS + TLS")
        er_uks = ExpressRoute("ExpressRoute\n10 Gbps")
        vpn_uks = VPNGateway("VPN Gateway\nS2S + P2S (20 Gbps)")

        spoke_a = VirtualNetwork("Spoke: Tracking\nvnet-trk-prod-uks")
        spoke_b = VirtualNetwork("Spoke: Sorting\nvnet-srt-prod-uks")
        spoke_c = VirtualNetwork("Spoke: HR Portal\nvnet-hr-prod-uks")

        sql = SQLDatabase("Azure SQL (Private Endpoint)")
        svc = AppService("App Service (Private Endpoint)")

    # Layer 3: UK West — DR Region
    with Cluster("UK West — DR Region"):
        hub_ukw = Blank("Virtual Hub\n10.100.1.0/23")
        fw_ukw = AzureFirewall("Azure Firewall\nPremium + IDPS + TLS")
        er_ukw = ExpressRoute("ExpressRoute\n10 Gbps")
        vpn_ukw = VPNGateway("VPN Gateway\nS2S + P2S (20 Gbps)")
        spoke_d = VirtualNetwork("Spoke: Tracking DR\nvnet-trk-prod-ukw")

    # Layer 4: On-prem + Infrastructure
    onprem = Blank("On-Prem DC (10.0.0.0/8)")
    dns = PrivateDNSZone("Private DNS Zones\n(DNS Resolver VNet)")

    # Layer 5: Management
    aad = ActiveDirectory("Entra ID (PIM)")
    mgmt = ManagementGroups("Azure Policy (vWAN Governance)")

    # ── Edges ──
    internet >> Edge(**edge_network, label="HTTPS") >> afd
    afd >> Edge(**edge_network, label="Private Link") >> spoke_a
    afd >> Edge(**edge_network) >> spoke_b

    vwan >> Edge(**edge_network) >> hub_uks
    vwan >> Edge(**edge_network) >> hub_ukw
    hub_uks >> Edge(**edge_network, label="Hub-to-hub mesh") >> hub_ukw

    hub_uks >> Edge(**edge_inspect, label="Routing Intent") >> fw_uks
    hub_uks >> Edge(**edge_network) >> er_uks
    hub_uks >> Edge(**edge_network) >> vpn_uks

    fw_uks >> Edge(**edge_inspect) >> spoke_a
    fw_uks >> Edge(**edge_inspect) >> spoke_b
    fw_uks >> Edge(**edge_inspect) >> spoke_c
    spoke_a >> Edge(**edge_network) >> sql
    spoke_a >> Edge(**edge_network) >> svc

    hub_ukw >> Edge(**edge_inspect) >> fw_ukw
    fw_ukw >> Edge(**edge_inspect) >> spoke_d

    onprem >> Edge(**edge_network, label="ExpressRoute") >> er_uks
    onprem >> Edge(**edge_network, label="ER (DR)") >> er_ukw

    spoke_a >> Edge(**edge_dns, label="DNS query") >> dns
    spoke_b >> Edge(**edge_dns) >> dns

    mgmt >> Edge(**edge_mgmt, label="Policy →") >> vwan
    aad >> Edge(**edge_mgmt, label="PIM →") >> hub_uks
