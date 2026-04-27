locals {
  shared_worker_backend_environment_variables = [
    {
      name  = "ENVIRONMENT"
      value = var.environment
    }, {
      name  = "USE_ELASTICMQ"
      value = "false"
    }, {
      name  = "DATA_S3_BUCKET"
      value = var.data_s3_bucket_name
    }, {
      name  = "PORT"
      value = tostring(var.backend_port)
    }, {
      name  = "REPO"
      value = "local-transcribe"
    }, {
      name  = "APP_URL"
      value = var.app_url
    }, {
      name  = "DOCKER_BUILDER_CONTAINER"
      value = "local-transcribe"
    }, {
      name  = "POSTGRES_HOST"
      value = var.database_host
    }, {
      name  = "POSTGRES_PORT"
      value = tostring(var.database_port)
    }, {
      name  = "POSTGRES_USER"
      value = var.database_user
    }, {
      name  = "POSTGRES_DB"
      value = var.database_name
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
      value = "[\"aws_transcribe\"]" # TODO replace with APIM - AIILG-481
    }, {
      name  = "MAX_TRANSCRIPTION_PROCESSES"
      value = tostring(var.max_transcription_processes)
    }, {
      name  = "MAX_LLM_PROCESSES"
      value = tostring(var.max_llm_processes)
    }, {
      name  = "AZURE_TRANSCRIPTION_CONTAINER_NAME"
      value = "transcriptions"
    }, {
      name = "FAST_LLM_PROVIDER"
      value = "azure_apim"
    }, {
      name = "FAST_LLM_MODEL_NAME"
      value = "gpt-4o"
    }, {
      name = "BEST_LLM_PROVIDER"
      value = "azure_apim"
    }, {
      name = "BEST_LLM_MODEL_NAME"
      value = "gpt-4o"
    }, {
      name  = "ALB_ARN"
      value = var.alb_arn
    }, {
      name  = "OIDC_ISSUER"
      value = var.oidc_issuer
    }, {
      name  = "AWS_REGION"
      value = var.aws_region
    }, {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }, {
      name  = "AZURE_APIM_AUTH_METHOD"
      value = "client_secret"
    }, {
    name  = "AZURE_APIM_URL"
    value = "https://api.azc.test.communities.gov.uk/minute/"
    }, {
    name  = "AZURE_APIM_API_VERSION"
    value = "2024-10-21"
    },
  ]
  shared_worker_backend_secrets = [
    {
      name      = "POSTGRES_PASSWORD"
      valueFrom = var.database_password_secret_arn
    },
    {
      name      = "AZURE_SPEECH_KEY"
      valueFrom = var.azure_speech_key_arn
    },
    {
      name      = "AZURE_SPEECH_REGION"
      valueFrom = var.azure_speech_region_arn
    },
    {
      name      = "AZURE_APIM_TENANT_ID"
      valueFrom = var.azure_apim_tenant_id_arn
    },
    {
      name      = "AZURE_APIM_CLIENT_ID"
      valueFrom = var.azure_apim_client_id_arn
    },
    {
      name      = "AZURE_APIM_CLIENT_SECRET"
      valueFrom = var.azure_apim_client_secret_arn
    },
    {
      name      = "AZURE_APIM_SCOPE"
      valueFrom = var.azure_apim_scope_arn
    },
    {
      name      = "AZURE_APIM_SUBSCRIPTION_KEY"
      valueFrom = var.azure_apim_subscription_key_arn
    },
  ]
  frontend_environment_variables = [
    {
      name = "ENVIRONMENT"
      value = var.environment
    }, {
      name = "APP_NAME"
      value = "local-transcribe-frontend"
    }, {
      name = "PORT"
      value = tostring(var.frontend_port)
    }, {
      name = "REPO"
      value = "local-transcribe"
    }, {
      name  = "BACKEND_HOST"
      value = "http://${aws_service_discovery_service.backend_service_discovery_service.name}.${aws_service_discovery_private_dns_namespace.private_dns_namespace.name}:${var.backend_port}"
    }, {
      name  = "ALB_ARN"
      value = var.alb_arn
    }, {
      name  = "OIDC_ISSUER"
      value = var.oidc_issuer
    },
  ]
}

resource "aws_ecs_task_definition" "frontend" {
  family             = "frontend-${var.environment_name}"
  cpu                = var.frontend_task_cpu
  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  memory             = var.frontend_task_memory
  network_mode       = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn      = aws_iam_role.frontend_ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      essential = true
      image     = var.frontend_image_name
      user = "root" # TODO shouldn't be root - AIILG-508

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
          awslogs-group         = module.frontend_log_group.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.environment_name
          mode                  = "non-blocking"
          max-buffer-size       = "4m"
          # See this analysis of how to choose a buffer size in non-blocking mode: https://github.com/moby/moby/issues/45999.
        }
      }

      environment = local.frontend_environment_variables

      healthCheck = {
        command     = ["CMD-SHELL", "wget -qO- http://$(hostname -i):${ var.frontend_port }/health || exit 1"]
        interval    = 60
        retries     = 3
        startPeriod = 60
        timeout     = 5
      }
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }
}

resource "aws_ecs_task_definition" "backend" {
  family             = "backend-${var.environment_name}"
  cpu                = var.backend_task_cpu
  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  memory             = var.backend_task_memory #MiB
  network_mode       = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn      = aws_iam_role.backend_ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      essential = true
      image     = var.backend_image_name
      user = "root" # TODO shouldn't be root - AIILG-508

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
          awslogs-group         = module.backend_log_group.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.environment_name
          mode                  = "non-blocking"
          max-buffer-size       = "4m"
          # See this analysis of how to choose a buffer size in non-blocking mode: https://github.com/moby/moby/issues/45999.
        }
      }

      environment = concat(local.shared_worker_backend_environment_variables, [
        {
        name  = "APP_NAME"
        value ="local-transcribe-backend"
        }
      ])

      secrets = local.shared_worker_backend_secrets

      healthCheck = {
        command     = ["CMD-SHELL", "curl --fail http://localhost:${ var.backend_port }/healthcheck"]
        interval    = 60
        retries     = 3
        startPeriod = 30
        timeout     = 5
      }
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }
}

resource "aws_ecs_task_definition" "worker" {
  family             = "worker-${var.environment_name}"
  cpu                = var.worker_task_cpu
  execution_role_arn = aws_iam_role.ecs_task_execution.arn
  memory = var.worker_task_memory #MiB
  network_mode       = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn      = aws_iam_role.worker_ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      essential = true
      image     = var.worker_image_name
      user = "root" # TODO shouldn't be root - AIILG-508

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = module.worker_log_group.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.environment_name
          mode                  = "non-blocking"
          max-buffer-size       = "4m"
          # See this analysis of how to choose a buffer size in non-blocking mode: https://github.com/moby/moby/issues/45999.
        }
      }

      environment = concat(local.shared_worker_backend_environment_variables, [
        {
          name  = "APP_NAME"
          value ="local-transcribe-worker"
        },
      ])

      secrets = local.shared_worker_backend_secrets

      healthCheck = {
        command     = ["CMD-SHELL", "python worker/healthcheck.py"]
        interval    = 60
        retries     = 3
        startPeriod = 60
        timeout     = 5
      }
    }
  ])

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }
}
