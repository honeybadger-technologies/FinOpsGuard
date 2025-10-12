# Example Azure Infrastructure
# Demonstrates comprehensive Azure resource support in FinOpsGuard

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "example" {
  name     = "finopsguard-example-rg"
  location = "eastus"
}

# Virtual Machine
resource "azurerm_linux_virtual_machine" "web" {
  name                = "webserver"
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
  vm_size             = "Standard_D2s_v3"
  
  admin_username = "adminuser"
  
  network_interface_ids = [
    azurerm_network_interface.example.id,
  ]
  
  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }
  
  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }
}

# Azure Kubernetes Service (AKS)
resource "azurerm_kubernetes_cluster" "k8s" {
  name                = "finopsguard-aks"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  dns_prefix          = "finopsguard"
  
  default_node_pool {
    name       = "default"
    node_count = 3
    vm_size    = "Standard_DS2_v2"
  }
  
  identity {
    type = "SystemAssigned"
  }
}

# SQL Database
resource "azurerm_mssql_server" "sql" {
  name                         = "finopsguard-sqlserver"
  resource_group_name          = azurerm_resource_group.example.name
  location                     = azurerm_resource_group.example.location
  version                      = "12.0"
  administrator_login          = "sqladmin"
  administrator_login_password = "P@ssw0rd1234!"
}

resource "azurerm_mssql_database" "db" {
  name      = "finopsguard-database"
  server_id = azurerm_mssql_server.sql.id
  sku_name  = "S2"
}

# Storage Account
resource "azurerm_storage_account" "storage" {
  name                     = "finopsguardstorage"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
}

# App Service Plan
resource "azurerm_service_plan" "app_plan" {
  name                = "finopsguard-appplan"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  os_type             = "Linux"
  sku_name            = "P1v2"
}

# Linux Web App
resource "azurerm_linux_web_app" "webapp" {
  name                = "finopsguard-webapp"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  service_plan_id     = azurerm_service_plan.app_plan.id
  
  site_config {}
}

# Function App
resource "azurerm_linux_function_app" "function" {
  name                = "finopsguard-function"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  service_plan_id     = azurerm_service_plan.app_plan.id
  
  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  
  site_config {}
}

# Redis Cache
resource "azurerm_redis_cache" "redis" {
  name                = "finopsguard-redis"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  capacity            = 2
  family              = "C"
  sku_name            = "Standard"
  enable_non_ssl_port = false
}

# Cosmos DB
resource "azurerm_cosmosdb_account" "cosmos" {
  name                = "finopsguard-cosmos"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  
  consistency_policy {
    consistency_level = "Session"
  }
  
  geo_location {
    location          = azurerm_resource_group.example.location
    failover_priority = 0
  }
}

# Container Instances
resource "azurerm_container_group" "aci" {
  name                = "finopsguard-aci"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  os_type             = "Linux"
  
  container {
    name   = "hello-world"
    image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
    cpu    = "0.5"
    memory = "1.5"
    
    ports {
      port     = 80
      protocol = "TCP"
    }
  }
}

# Load Balancer
resource "azurerm_lb" "lb" {
  name                = "finopsguard-lb"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  sku                 = "Standard"
  
  frontend_ip_configuration {
    name                 = "PublicIPAddress"
    public_ip_address_id = azurerm_public_ip.example.id
  }
}

# Application Gateway
resource "azurerm_application_gateway" "appgw" {
  name                = "finopsguard-appgw"
  resource_group_name = azurerm_resource_group.example.name
  location            = azurerm_resource_group.example.location
  
  sku {
    name     = "WAF_v2"
    tier     = "WAF_v2"
    capacity = 2
  }
  
  gateway_ip_configuration {
    name      = "appgw-ip-config"
    subnet_id = azurerm_subnet.frontend.id
  }
  
  frontend_port {
    name = "frontend-port"
    port = 80
  }
  
  frontend_ip_configuration {
    name                 = "frontend-ip-config"
    public_ip_address_id = azurerm_public_ip.appgw.id
  }
  
  backend_address_pool {
    name = "backend-pool"
  }
  
  backend_http_settings {
    name                  = "backend-http-settings"
    cookie_based_affinity = "Disabled"
    port                  = 80
    protocol              = "Http"
    request_timeout       = 60
  }
  
  http_listener {
    name                           = "http-listener"
    frontend_ip_configuration_name = "frontend-ip-config"
    frontend_port_name             = "frontend-port"
    protocol                       = "Http"
  }
  
  request_routing_rule {
    name                       = "routing-rule"
    rule_type                  = "Basic"
    http_listener_name         = "http-listener"
    backend_address_pool_name  = "backend-pool"
    backend_http_settings_name = "backend-http-settings"
    priority                   = 100
  }
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "finopsguard-postgres"
  resource_group_name    = azurerm_resource_group.example.name
  location               = azurerm_resource_group.example.location
  version                = "13"
  administrator_login    = "psqladmin"
  administrator_password = "P@ssw0rd1234!"
  
  storage_mb = 32768
  sku_name   = "GP_Standard_D4s_v3"
}

# MySQL Flexible Server
resource "azurerm_mysql_flexible_server" "mysql" {
  name                   = "finopsguard-mysql"
  resource_group_name    = azurerm_resource_group.example.name
  location               = azurerm_resource_group.example.location
  administrator_login    = "mysqladmin"
  administrator_password = "P@ssw0rd1234!"
  
  sku_name   = "GP_Standard_D2ds_v4"
  storage_mb = 20480
}

# Data Factory
resource "azurerm_data_factory" "adf" {
  name                = "finopsguard-adf"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
}

# Virtual Network Gateway (VPN)
resource "azurerm_virtual_network_gateway" "vpn" {
  name                = "finopsguard-vpn"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  
  type     = "Vpn"
  vpn_type = "RouteBased"
  sku      = "VpnGw1"
  
  ip_configuration {
    name                          = "vnetGatewayConfig"
    public_ip_address_id          = azurerm_public_ip.vpn.id
    private_ip_address_allocation = "Dynamic"
    subnet_id                     = azurerm_subnet.gateway.id
  }
}

# Event Hub Namespace
resource "azurerm_eventhub_namespace" "eventhub" {
  name                = "finopsguard-eventhub"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  sku                 = "Standard"
  capacity            = 2
}

# Synapse Workspace
resource "azurerm_synapse_workspace" "synapse" {
  name                                 = "finopsguard-synapse"
  resource_group_name                  = azurerm_resource_group.example.name
  location                             = azurerm_resource_group.example.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.example.id
  sql_administrator_login              = "sqladminuser"
  sql_administrator_login_password     = "P@ssw0rd1234!"
}

# Supporting Resources (for completeness)
resource "azurerm_virtual_network" "example" {
  name                = "example-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
}

resource "azurerm_subnet" "frontend" {
  name                 = "frontend"
  resource_group_name  = azurerm_resource_group.example.name
  virtual_network_name = azurerm_virtual_network.example.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "gateway" {
  name                 = "GatewaySubnet"
  resource_group_name  = azurerm_resource_group.example.name
  virtual_network_name = azurerm_virtual_network.example.name
  address_prefixes     = ["10.0.255.0/27"]
}

resource "azurerm_network_interface" "example" {
  name                = "example-nic"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  
  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.frontend.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_public_ip" "example" {
  name                = "example-pip"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_public_ip" "appgw" {
  name                = "appgw-pip"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_public_ip" "vpn" {
  name                = "vpn-pip"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_storage_data_lake_gen2_filesystem" "example" {
  name               = "synapsefs"
  storage_account_id = azurerm_storage_account.storage.id
}

