locals {
  shared_environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = terraform.workspace
    }, {
      name  = "PORT"
      value = var.backend_port
    }, {
      name  = "REPO"
      value = "minute"
    }, {
      name  = "APP_URL"
      value = var.app_url
    }, {
      name  = "DOCKER_BUILDER_CONTAINER"
      value = "minute"
    }, {
      name  = "POSTGRES_HOST"
      value = "jdbc:postgresql://${var.database_host}"
    }, {
      name  = "POSTGRES_PORT"
      value = var.database_port
    }, {
      name  = "POSTGRES_USER"
      value = var.database_user
    }, {
      name  = "POSTGRES_PASSWORD"
      value = var.database_password
    }, {
      name  = "AUTH_PROVIDER_PUBLIC_KEY"
      value = "placeholder"
    }, {
      name  = "AZURE_OPENAI_API_VERSION"
      value = "2024-10-21"
    }, {
      name  = "TRANSCRIPTION_QUEUE_NAME"
      value = var.transcription_queue_name
    }, {
      name  = "TRANSCRIPTION_DEADLETTER_QUEUE_NAME"
      value = var.transcription_deadletter_queue_name
    }, {
      name  = "LLM_QUEUE_NAME"
      value = var.llm_queue_name
    }, {
      name  = "LLM_DEADLETTER_QUEUE_NAME"
      value = var.llm_deadletter_queue_name
    }, {
      name  = "TRANSCRIPTION_SERVICES"
      value = "[\"azure_stt_synchronous\",\"azure_stt_batch\"]"
    }, {
      name  = "MAX_TRANSCRIPTION_PROCESSES"
      value = var.max_transcription_processes
    }, {
      name  = "MAX_LLM_PROCESSES"
      value = var.max_llm_processes
    }, {
      name  = "AZURE_TRANSCRIPTION_CONTAINER_NAME"
      value = "transcriptions"
    }, {
      name = "FAST_LLM_PROVIDER"
      value = "gemini"
    }, {
      name = "FAST_LLM_MODEL_NAME"
      value = "gemini-2.5-flash-lite"
    }, {
      name = "BEST_LLM_PROVIDER"
      value = "gemini"
    }, {
      name = "BEST_LLM_MODEL_NAME"
      value = "gemini-2.5-flash"
    },
  ]
  frontend_environment_variables = [
    {
      name = "ENVIRONMENT"
      value = terraform.workspace
    }, {
      name = "APP_NAME"
      value = "minute-frontend"
    }, {
      name = "PORT"
      value = var.frontend_port
    }, {
      name = "REPO"
      value = "minute"
    }, {
      name  = "BACKEND_HOST"
      value = "http://${aws_service_discovery_service.backend_service_discovery_service.name}.${aws_service_discovery_private_dns_namespace.private_dns_namespace.name}:${var.backend_port}"
    },
  ]
}

resource "aws_ecs_task_definition" "frontend" {
  family             = "frontend-${var.environment_name}"
  cpu                = 2048
  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  memory = 2048 #MiB
  network_mode       = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn      = aws_iam_role.frontend_ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      essential = true
      image     = var.frontend_image_name
      user = "root" # TODO probably shouldn't be root

      portMappings = [
        {
          protocol      = "tcp"
          containerPort = var.frontend_port
          hostPort      = var.frontend_port
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend_log_group.id
          awslogs-region        = "eu-west-2"
          awslogs-stream-prefix = var.environment_name
          mode                  = "non-blocking"
          max-buffer-size       = "4m"
          # See this analysis of how to choose a buffer size in non-blocking mode: https://github.com/moby/moby/issues/45999.
        }
      }

      environment = local.frontend_environment_variables
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
}

resource "aws_ecs_task_definition" "backend" {
  family             = "backend-${var.environment_name}"
  cpu                = 2048
  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  memory = 2048 #MiB
  network_mode       = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn      = aws_iam_role.backend_ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      essential = true
      image     = var.backend_image_name
      user = "root" # TODO probably shouldn't be root

      portMappings = [
        {
          protocol      = "tcp"
          containerPort = var.backend_port
          hostPort      = var.backend_port
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend_log_group.id
          awslogs-region        = "eu-west-2"
          awslogs-stream-prefix = var.environment_name
          mode                  = "non-blocking"
          max-buffer-size       = "4m"
          # See this analysis of how to choose a buffer size in non-blocking mode: https://github.com/moby/moby/issues/45999.
        }
      }

      environment = merge(local.shared_environment_variables, {
        "APP_NAME" : "minute-backend",
      })
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
}

resource "aws_ecs_task_definition" "worker" {
  family             = "worker-${var.environment_name}"
  cpu                = 4096
  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  memory = 8192 #MiB
  network_mode       = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn      = aws_iam_role.worker_ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      essential = true
      image     = var.worker_image_name
      user = "root" # TODO probably shouldn't be root

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker_log_group.id
          awslogs-region        = "eu-west-2"
          awslogs-stream-prefix = var.environment_name
          mode                  = "non-blocking"
          max-buffer-size       = "4m"
          # See this analysis of how to choose a buffer size in non-blocking mode: https://github.com/moby/moby/issues/45999.
        }
      }

      environment = merge(local.shared_environment_variables, {
        "APP_NAME" : "minute-worker",
        "AUTH_API_URL" : "unused", # Worker settings need refactoring so we can remove this
      })
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }
}
