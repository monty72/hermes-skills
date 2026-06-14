#!/usr/bin/env python3
"""Azure Landing Zone — UK Regulated Enterprise.
   Generate with: python3 this_script.py
   Requires: pip install diagrams && sudo apt-get install graphviz
"""

from diagrams import Diagram, Edge, Cluster
from diagrams.azure.compute import AppServices, FunctionApps, AKS
from diagrams.azure.database import SQLDatabases, CosmosDb, CacheForRedis
from diagrams.azure.network import FrontDoors, ApplicationGateway, Firewall, ExpressrouteCircuits, PrivateEndpoint, VirtualNetworks
from diagrams.azure.security import KeyVaults, MicrosoftDefenderForCloud
from diagrams.azure.integration import ServiceBus, APIManagement, EventGridTopics
from diagrams.azure.analytics import EventHubs
from diagrams.azure.storage import BlobStorage
from diagrams.azure.monitor import Monitor, ApplicationInsights, LogAnalyticsWorkspaces
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.ml import MachineLearningServiceWorkspaces, CognitiveServices
from diagrams.onprem.client import Users
from diagrams.generic.blank import Blank

output_path = "/home/matth/azure-landing-zone-architecture"

with Diagram(
    "Azure Landing Zone — UK Regulated Enterprise",
    show=False, direction="LR", filename=output_path, outformat="png",
    graph_attr={"bgcolor": "#0f172a", "fontcolor": "#e2e8f0", "fontname": "JetBrains Mono",
                "dpi": "200", "pad": "1.0", "ranksep": "1.2", "nodesep": "0.6", "splines": "ortho"},
    node_attr={"fontcolor": "#e2e8f0", "fontname": "JetBrains Mono", "fontsize": "9"},
    edge_attr={"fontcolor": "#94a3b8", "fontname": "JetBrains Mono", "fontsize": "7"},
):
    users = Users("Users / Clients")

    with Cluster("Hub Network — UK South", graph_attr={"bgcolor": "#1e293b", "fontcolor": "#fbbf24", "style": "dashed", "pencolor": "#fbbf24"}):
        with Cluster("Connectivity"):
            express_route = ExpressrouteCircuits("ExpressRoute\n(10 Gbps)")
            firewall = Firewall("Azure Firewall")
            front_door = FrontDoors("Front Door + WAF")
        with Cluster("Identity & Security"):
            entra = ActiveDirectory("Entra ID (PIM)")
            kv = KeyVaults("Key Vault (CMK)")
            defender = MicrosoftDefenderForCloud("Defender Cloud")
        with Cluster("Observability"):
            monitor = Monitor("Azure Monitor")
            insights = ApplicationInsights("App Insights")

    with Cluster("Prod Workload Spoke", graph_attr={"bgcolor": "#1e293b", "fontcolor": "#34d399", "pencolor": "#34d399"}):
        with Cluster("Ingress"):
            apim = APIManagement("API Management")
            gw = ApplicationGateway("App Gateway WAFv2")
        with Cluster("Compute"):
            apps = AppServices("App Service (Pv3)")
            aks = AKS("AKS Production")
            fn = FunctionApps("Functions (Prem)")
        with Cluster("Integration"):
            sb = ServiceBus("Service Bus (Prem)")
            eh = EventHubs("Event Hubs")
            eg = EventGridTopics("Event Grid")
        with Cluster("Data"):
            sql = SQLDatabases("SQL Hyperscale\n(Geo-replicated)")
            cosmos = CosmosDb("Cosmos DB\n(Multi-region)")
            redis = CacheForRedis("Redis Cache (Prem)")
            blob = BlobStorage("Blob RA-GRS")
        with Cluster("AI"):
            mlw = MachineLearningServiceWorkspaces("AI Foundry\n(Azure OpenAI)")
            cs = CognitiveServices("Content Safety")

    with Cluster("Non-Prod Workload Spoke", graph_attr={"bgcolor": "#1e293b", "fontcolor": "#a78bfa", "pencolor": "#a78bfa"}):
        apps_dev = AppServices("App Service (Std)")
        aks_dev = AKS("AKS Dev/Test")
        sql_dev = SQLDatabases("SQL GP")

    with Cluster("Management Spoke", graph_attr={"bgcolor": "#1e293b", "fontcolor": "#fb7185", "pencolor": "#fb7185"}):
        log_analytics = LogAnalyticsWorkspaces("Log Analytics")
        backup = BlobStorage("Backup Vault")

    with Cluster("CI/CD (GitHub Enterprise)", graph_attr={"bgcolor": "#1e293b", "fontcolor": "#22d3ee", "pencolor": "#22d3ee"}):
        actions = Blank("GitHub Actions\n(OIDC Auth)")

    # Edges
    users >> Edge(color="#94a3b8", style="dashed") >> front_door
    front_door >> Edge(color="#fbbf24", label="WAF") >> apim
    apim >> Edge(color="#34d399") >> apps
    apim >> Edge(color="#34d399") >> aks
    apps >> Edge(color="#22d3ee") >> sb
    fn >> Edge(color="#22d3ee") >> sb
    fn >> Edge(color="#22d3ee") >> eg
    apps >> Edge(color="#a78bfa") >> sql
    aks >> Edge(color="#a78bfa") >> cosmos
    apps >> Edge(color="#a78bfa") >> redis
    fn >> Edge(color="#a78bfa") >> blob
    apps >> Edge(color="#38bdf8") >> mlw
    apps >> Edge(color="#38bdf8") >> cs
    apps >> Edge(color="#fb7185", style="dashed") >> insights
    aks >> Edge(color="#fb7185", style="dashed") >> insights
    insights >> Edge(color="#fb7185") >> monitor
    actions >> Edge(color="#22d3ee") >> apps
    actions >> Edge(color="#22d3ee") >> aks
    actions >> Edge(color="#22d3ee") >> sql

print(f"Saved: {output_path}.png")
