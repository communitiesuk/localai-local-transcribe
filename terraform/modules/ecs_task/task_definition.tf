resource "aws_ecs_task_definition" "main" {
  family                   = "${var.task_name}-${var.environment_name}"
  cpu                      = var.task_cpu
  execution_role_arn       = var.ecs_task_execution_role_arn
  memory                   = var.task_memory #MiB
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name      = var.task_name
      essential = true
      image     = var.container_image
      user      = "root"

      portMappings = [
        {
          protocol      = "tcp"
          containerPort = var.container_port
          hostPort      = var.container_port
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.webapp_log_group.id
          awslogs-region        = "eu-west-2"
          awslogs-stream-prefix = var.environment_name
          mode                  = "non-blocking"
          max-buffer-size       = "4m" # See this analysis of how to choose a buffer size in non-blocking mode: https://github.com/moby/moby/issues/45999.
        }
      }

      environment = var.environment_variables
      secrets     = var.secrets
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  tags = var.tags
}