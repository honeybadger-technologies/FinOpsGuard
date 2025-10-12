"""Unit tests for Azure Terraform parsing."""

import pytest
from finopsguard.parsers.terraform import parse_terraform_to_crmodel


class TestAzureTerraformParser:
    """Test Azure resource parsing from Terraform HCL."""
    
    def test_parse_azure_virtual_machine(self):
        """Test parsing Azure Virtual Machine."""
        hcl = '''
resource "azurerm_linux_virtual_machine" "example" {
  name                = "example-vm"
  location            = "eastus"
  vm_size            = "Standard_D2s_v3"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        vm = model.resources[0]
        assert vm.type == 'azure_virtual_machine'
        assert vm.region == 'eastus'
        assert vm.size == 'Standard_D2s_v3'
    
    def test_parse_azure_sql_database(self):
        """Test parsing Azure SQL Database."""
        hcl = '''
resource "azurerm_mssql_server" "example" {
  name                = "example-sqlserver"
  location            = "westus2"
}

resource "azurerm_mssql_database" "example" {
  name      = "example-db"
  server_id = azurerm_mssql_server.example.id
  sku_name  = "S2"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 2
        
        db = [r for r in model.resources if r.type == 'azure_sql_database'][0]
        assert db.size == 'S2'
    
    def test_parse_azure_storage_account(self):
        """Test parsing Azure Storage Account."""
        hcl = '''
resource "azurerm_storage_account" "example" {
  name                     = "examplestorage"
  location                 = "westeurope"
  account_tier             = "Premium"
  account_replication_type = "GRS"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        storage = model.resources[0]
        assert storage.type == 'azure_storage_account'
        assert storage.size == 'Premium_GRS'
        assert storage.region == 'westeurope'
    
    def test_parse_azure_kubernetes_cluster(self):
        """Test parsing Azure Kubernetes Service (AKS)."""
        hcl = '''
resource "azurerm_kubernetes_cluster" "example" {
  name       = "example-aks"
  location   = "eastus"
  
  default_node_pool {
    name       = "default"
    node_count = 3
    vm_size    = "Standard_D4s_v3"
  }
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        aks = model.resources[0]
        assert aks.type == 'azure_kubernetes_cluster'
        assert 'Standard_D4s_v3' in aks.size
        assert '3nodes' in aks.size
        assert aks.metadata['node_count'] == 3
    
    def test_parse_azure_app_service_plan(self):
        """Test parsing Azure App Service Plan."""
        hcl = '''
resource "azurerm_service_plan" "example" {
  name     = "example-plan"
  location = "westus"
  sku_name = "P1v2"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        plan = model.resources[0]
        assert plan.type == 'azure_app_service_plan'
        assert plan.size == 'P1v2'
    
    def test_parse_azure_function_app(self):
        """Test parsing Azure Function App."""
        hcl = '''
resource "azurerm_linux_function_app" "example" {
  name                = "example-function"
  location            = "eastus"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        func = model.resources[0]
        assert func.type == 'azure_function_app'
        assert func.region == 'eastus'
    
    def test_parse_azure_load_balancer(self):
        """Test parsing Azure Load Balancer."""
        hcl = '''
resource "azurerm_lb" "example" {
  name     = "example-lb"
  location = "westus"
  sku      = "Standard"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        lb = model.resources[0]
        assert lb.type == 'azure_load_balancer'
        assert lb.size == 'Standard'
    
    def test_parse_azure_redis_cache(self):
        """Test parsing Azure Redis Cache."""
        hcl = '''
resource "azurerm_redis_cache" "example" {
  name                = "example-redis"
  location            = "eastus"
  sku_name            = "Premium"
  family              = "P"
  capacity            = 1
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        redis = model.resources[0]
        assert redis.type == 'azure_redis_cache'
        assert redis.size == 'Premium_P1'
    
    def test_parse_azure_cosmosdb(self):
        """Test parsing Azure Cosmos DB."""
        hcl = '''
resource "azurerm_cosmosdb_account" "example" {
  name                = "example-cosmos"
  location            = "westus"
  consistency_level   = "Strong"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        cosmos = model.resources[0]
        assert cosmos.type == 'azure_cosmosdb_account'
        assert cosmos.size == 'Strong'
    
    def test_parse_azure_container_instances(self):
        """Test parsing Azure Container Instances."""
        hcl = '''
resource "azurerm_container_group" "example" {
  name     = "example-aci"
  location = "eastus"
  
  container {
    name   = "hello-world"
    image  = "mcr.microsoft.com/azuredocs/aci-helloworld:latest"
    cpu    = 0.5
    memory = 1.5
  }
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        aci = model.resources[0]
        assert aci.type == 'azure_container_instances'
        assert '0.5cpu' in aci.size
        assert '1.5gb' in aci.size
        assert aci.metadata['cpu'] == 0.5
        assert aci.metadata['memory'] == 1.5
    
    def test_parse_azure_application_gateway(self):
        """Test parsing Azure Application Gateway."""
        hcl = '''
resource "azurerm_application_gateway" "example" {
  name     = "example-appgw"
  location = "westus"
  
  sku {
    name     = "WAF_v2"
    capacity = 2
  }
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        appgw = model.resources[0]
        assert appgw.type == 'azure_application_gateway'
        assert 'WAF_v2' in appgw.size
        assert appgw.metadata['capacity'] == 2
    
    def test_parse_azure_postgresql(self):
        """Test parsing Azure PostgreSQL."""
        hcl = '''
resource "azurerm_postgresql_flexible_server" "example" {
  name                = "example-psql"
  location            = "eastus"
  sku_name            = "GP_Standard_D4s_v3"
  storage_mb          = 32768
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        psql = model.resources[0]
        assert psql.type == 'azure_postgresql_server'
        assert 'GP_Standard_D4s_v3' in psql.size
        assert psql.metadata['storage_gb'] == 32
    
    def test_parse_azure_mysql(self):
        """Test parsing Azure MySQL."""
        hcl = '''
resource "azurerm_mysql_flexible_server" "example" {
  name       = "example-mysql"
  location   = "westus"
  sku_name   = "GP_Standard_D2ds_v4"
  storage_mb = 20480
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        mysql = model.resources[0]
        assert mysql.type == 'azure_mysql_server'
        assert 'GP_Standard_D2ds_v4' in mysql.size
        assert mysql.metadata['storage_gb'] == 20
    
    def test_parse_azure_sql_managed_instance(self):
        """Test parsing Azure SQL Managed Instance."""
        hcl = '''
resource "azurerm_sql_managed_instance" "example" {
  name                = "example-sqlmi"
  location            = "eastus"
  sku_name            = "GP_Gen5"
  vcores              = 8
  storage_size_in_gb  = 256
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        sqlmi = model.resources[0]
        assert sqlmi.type == 'azure_sql_managed_instance'
        assert 'GP_Gen5' in sqlmi.size
        assert '8vCore' in sqlmi.size
        assert sqlmi.metadata['vcores'] == 8
        assert sqlmi.metadata['storage_gb'] == 256
    
    def test_parse_azure_data_factory(self):
        """Test parsing Azure Data Factory."""
        hcl = '''
resource "azurerm_data_factory" "example" {
  name                = "example-adf"
  location            = "eastus"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        adf = model.resources[0]
        assert adf.type == 'azure_data_factory'
        assert adf.size == 'standard'
    
    def test_parse_azure_vpn_gateway(self):
        """Test parsing Azure Virtual Network Gateway."""
        hcl = '''
resource "azurerm_virtual_network_gateway" "example" {
  name     = "example-vnetgw"
  location = "westus"
  type     = "Vpn"
  sku      = "VpnGw1"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        vnetgw = model.resources[0]
        assert vnetgw.type == 'azure_virtual_network_gateway'
        assert 'Vpn' in vnetgw.size
        assert 'VpnGw1' in vnetgw.size
    
    def test_parse_azure_synapse(self):
        """Test parsing Azure Synapse Workspace."""
        hcl = '''
resource "azurerm_synapse_workspace" "example" {
  name                = "example-synapse"
  location            = "eastus"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        synapse = model.resources[0]
        assert synapse.type == 'azure_synapse_workspace'
        assert synapse.size == 'workspace'
    
    def test_parse_azure_eventhub(self):
        """Test parsing Azure Event Hub Namespace."""
        hcl = '''
resource "azurerm_eventhub_namespace" "example" {
  name     = "example-eventhub"
  location = "eastus"
  sku      = "Standard"
  capacity = 2
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        eventhub = model.resources[0]
        assert eventhub.type == 'azure_eventhub_namespace'
        assert 'Standard' in eventhub.size
        assert eventhub.metadata['capacity'] == 2
    
    def test_parse_multiple_azure_resources(self):
        """Test parsing multiple Azure resources together."""
        hcl = '''
resource "azurerm_linux_virtual_machine" "web" {
  name     = "web-vm"
  location = "eastus"
  vm_size  = "Standard_B2s"
}

resource "azurerm_mssql_database" "app_db" {
  name     = "app-database"
  sku_name = "S1"
}

resource "azurerm_storage_account" "data" {
  name                     = "datastorage"
  location                 = "eastus"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_kubernetes_cluster" "k8s" {
  name     = "k8s-cluster"
  location = "westus"
  
  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_DS2_v2"
  }
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 4
        
        types = [r.type for r in model.resources]
        assert 'azure_virtual_machine' in types
        assert 'azure_sql_database' in types
        assert 'azure_storage_account' in types
        assert 'azure_kubernetes_cluster' in types
    
    def test_azure_default_location(self):
        """Test that Azure resources use default location when not specified."""
        hcl = '''
resource "azurerm_linux_virtual_machine" "example" {
  name     = "example-vm"
  vm_size  = "Standard_B1s"
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        vm = model.resources[0]
        assert vm.region == 'eastus'  # Default Azure location
    
    def test_azure_count_parameter(self):
        """Test that Azure resources respect count parameter."""
        hcl = '''
resource "azurerm_linux_virtual_machine" "cluster" {
  name     = "cluster-vm"
  location = "eastus"
  vm_size  = "Standard_D2s_v3"
  count    = 5
}
'''
        model = parse_terraform_to_crmodel(hcl)
        assert len(model.resources) == 1
        
        vm = model.resources[0]
        assert vm.count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

