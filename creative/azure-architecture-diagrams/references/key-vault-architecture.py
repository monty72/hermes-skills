#!/usr/bin/env python3
"""Azure Key Vault Reference Architecture — worked example."""
from diagrams import Diagram, Edge, Cluster
from diagrams.azure.security import KeyVaults, MicrosoftDefenderForCloud
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.compute import AppServices, FunctionApps, AKS
from diagrams.azure.database import SQLDatabases, CosmosDb
from diagrams.azure.network import Firewall, PrivateEndpoint, VirtualNetworks
from diagrams.azure.integration import APIManagement
from diagrams.azure.storage import BlobStorage
from diagrams.azure.monitor import Monitor, LogAnalyticsWorkspaces, ApplicationInsights
from diagrams.onprem.client import Users
from diagrams.onprem.ci import GithubActions
from diagrams.generic.blank import Blank

output_path = "/home/matth/azure-key-vault-reference-architecture"

with Diagram("Azure Key Vault — Enterprise Reference Architecture", show=False, direction="TB",
    filename=output_path, outformat="png",
    graph_attr={"bgcolor":"#0f172a","fontcolor":"#e2e8f0","fontname":"JetBrains Mono","dpi":"200","pad":"1.0","ranksep":"0.9","nodesep":"0.5","splines":"ortho"},
    node_attr={"fontcolor":"#e2e8f0","fontname":"JetBrains Mono","fontsize":"9"},
    edge_attr={"fontcolor":"#94a3b8","fontname":"JetBrains Mono","fontsize":"7"}):

    with Cluster("Management Plane", graph_attr={"bgcolor":"#1e293b","fontcolor":"#fbbf24","style":"dashed","pencolor":"#fbbf24"}):
        entra = ActiveDirectory("Entra ID (RBAC + PIM)")
        admin = Users("Admins (Security/Platform)")
        policy = Blank("Azure Policy (KV Governance)")
        defender = MicrosoftDefenderForCloud("Defender for Cloud")
        sentinel = Blank("Sentinel (Audit Logs)")

    with Cluster("Azure Key Vault — Data Plane", graph_attr={"bgcolor":"#1e293b","fontcolor":"#facc15","pencolor":"#facc15"}):
        secrets = Blank("Secrets\n(DB creds, API keys)")
        keys = Blank("Keys\n(CMK: storage, DB, encryption)")
        certs = Blank("Certificates\n(TLS/SSL, code signing)")
        vnet = VirtualNetworks("VNet Injection")
        private_endpoint = PrivateEndpoint("Private Endpoint")
        kv_firewall = Firewall("KV Firewall (IP rules)")

    with Cluster("Consuming Workloads", graph_attr={"bgcolor":"#1e293b","fontcolor":"#34d399","pencolor":"#34d399"}):
        apps = AppServices("App Service (Managed ID)")
        aks = AKS("AKS (CSI Driver)")
        fn = FunctionApps("Functions (Managed ID)")
        sql = SQLDatabases("SQL Database (TDE + CMK)")
        cosmos = CosmosDb("Cosmos DB (CMK)")
        blob = BlobStorage("Storage Account (Infra encryption)")
        apim = APIManagement("API Management (Cert auth)")

    with Cluster("Secrets Lifecycle", graph_attr={"bgcolor":"#1e293b","fontcolor":"#22d3ee","pencolor":"#22d3ee"}):
        cicd = GithubActions("GitHub Actions (OIDC to KV)")

    admin >> Edge(color="#fbbf24", style="dotted") >> entra
    entra >> Edge(color="#fbbf24") >> secrets
    policy >> Edge(color="#fb7185", style="dashed") >> defender
    defender >> Edge(color="#fb7185", style="dashed") >> sentinel
    secrets >> Edge(color="#34d399") >> apps
    secrets >> Edge(color="#34d399") >> aks
    secrets >> Edge(color="#34d399") >> fn
    keys >> Edge(color="#a78bfa") >> sql
    keys >> Edge(color="#a78bfa") >> cosmos
    keys >> Edge(color="#a78bfa") >> blob
    certs >> Edge(color="#facc15") >> apim
    vnet >> Edge(color="#94a3b8") >> private_endpoint
    private_endpoint >> Edge(color="#94a3b8") >> secrets
    for w in [apps, aks, fn, sql, cosmos, blob]:
        w >> Edge(color="#94a3b8", style="dotted") >> kv_firewall
    cicd >> Edge(color="#22d3ee") >> secrets
    cicd >> Edge(color="#22d3ee", style="dotted") >> secrets
    for r in [secrets, keys, certs]:
        r >> Edge(color="#fb7185", style="dashed") >> sentinel
