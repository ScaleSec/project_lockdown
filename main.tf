# TODO: put in a feature request for the below functionality

# module "function" {
#   for_each = var.enabled_modules
#   source   = "./modules/${each.key}"
  
#   org_id = lookup(each.value, "org_id")
#   project = lookup(each.value, "project")
#   region = lookup(each.value, "region")
#   name = lookup(each.value, "name")
#   function_perms = lookup(each.value, "function_perms")
# }


module "function" {
  for_each = var.enabled_modules
  source   = "./terraform"
  function_name = each.key
  
  org_id = lookup(each.value, "org_id")
  project = lookup(each.value, "project")
  region = lookup(each.value, "region")
  name = lookup(each.value, "name")
  function_perms = lookup(each.value, "function_perms")
}


