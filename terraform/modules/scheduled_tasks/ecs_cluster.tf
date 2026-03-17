#tfsec:ignore:aws-ecs-enable-container-insight: We do not currently need to enable container insights
resource "aws_ecs_cluster" "scheduled_tasks" {
  name = "${var.environment_name}-scheduled-tasks"
}



