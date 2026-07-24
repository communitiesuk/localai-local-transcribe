#privileged role, granted all necessary permissions
resource "postgresql_role" "app_role" {
  name  = "app_role"
  login = false

}

#object owner role - owns tables/sequences, each rotated
#user maintains the necessary & identical permissons
resource "postgresql_role" "app_owner_role" {
  name  = "app_owner_role"
  login = false

}

#application entry point <-> user to be cloned & rotated 
resource "postgresql_role" "backend_user" {
  name                = "backend_user"
  login               = true
  password_wo         = var.backend_user_password
  password_wo_version = 1
  roles               = [postgresql_role.app_role.name]

}

#Migrations: special role pointed to alembic with more 
#privileges than the backend_user

resource "postgresql_role" "db_migrations" {
  name     = "db_migrations"
  login    = true
  password = "todo"
  roles = [
    postgresql_role.app_role.name,
    postgresql_role.app_owner_role.name
  ]

}


## GRANTS & PRIVILEGES

#allow db connection
resource "postgresql_grant" "app_db" {
  database    = var.db_name
  role        = postgresql_role.app_role.name
  object_type = "database"
  privileges  = ["CONNECT"]

}

#allow schema usage & creation
resource "postgresql_grant" "app_schema_usage" {
  database    = var.db_name
  schema      = "public"
  role        = postgresql_role.app_role.name
  object_type = "schema"
  privileges  = ["USAGE"]
}

resource "postgresql_grant" "app_schema_create" {
  database    = var.db_name
  schema      = "public"
  role        = postgresql_role.app_owner_role.name
  object_type = "schema"
  privileges  = ["CREATE", "USAGE"]
}


#full DML access
resource "postgresql_grant" "db_all_tables" {
  database    = var.db_name
  schema      = "public"
  role        = postgresql_role.app_role.name
  object_type = "table"
  privileges  = ["SELECT", "INSERT", "UPDATE", "DELETE"]

}

#existing sequences
resource "postgresql_grant" "db_all_sequences" {
  database    = var.db_name
  schema      = "public"
  role        = postgresql_role.app_role.name
  object_type = "sequence"
  privileges  = ["SELECT", "UPDATE", "USAGE"]

}


## Default privileges, ensures permissions persist on rotation
## mapped to postgresql_role.app_owner_role which backend_user 
## and its eventual clone belong to


resource "postgresql_default_privileges" "app_future_tables" {
  database    = var.db_name
  schema      = "public"
  role        = postgresql_role.app_role.name
  owner       = postgresql_role.app_owner_role.name
  object_type = "table"
  privileges  = ["SELECT", "INSERT", "UPDATE", "DELETE"]
}

resource "postgresql_default_privileges" "app_future_sequences" {
  database    = var.db_name
  schema      = "public"
  role        = postgresql_role.app_role.name
  owner       = postgresql_role.app_owner_role.name
  object_type = "sequence"
  privileges  = ["SELECT", "UPDATE", "USAGE"]

}

