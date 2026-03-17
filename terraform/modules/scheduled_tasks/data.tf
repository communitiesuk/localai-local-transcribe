# Use Resource Groups Tagging API to find all ECS task definitions tagged with task-type=scheduled
data "aws_resourcegroupstaggingapi_resources" "scheduled_task_definitions" {
  tag_filter {
    key    = "Type"
    values = ["scheduled-task"]
  }

  resource_type_filters = ["ecs:task-definition"]
}

locals {
  task_name_tag = "ScheduledTaskName"
  tasks = merge([
    for task_def in data.aws_resourcegroupstaggingapi_resources.scheduled_task_definitions.resource_tag_mapping_list : {
      (task_def.tags[local.task_name_tag]) = {
        task_family_arn = replace(
          task_def.resource_arn,
          "/:[0-9]+$/",
          ""
        )
        schedule_expression = var.schedule_expressions[task_def.tags[local.task_name_tag]].schedule_expression
      }
    }
    if can(var.schedule_expressions[task_def.tags[local.task_name_tag]])
  ]...)
}
