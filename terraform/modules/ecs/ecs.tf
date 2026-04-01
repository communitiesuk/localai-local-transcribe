#tfsec:ignore:aws-ecs-enable-container-insight: We can enable insights later if required

resource "aws_ecs_cluster" "main" {
  name = "${var.environment_name}-app"
}

resource "aws_ecs_service" "frontend" {
  name                               = "${var.environment_name}-frontend"
  cluster                            = aws_ecs_cluster.main.arn
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100 # There should always be at least the desired count running during a deployment
  desired_count                      = var.frontend_task_desired_count
  enable_execute_command             = var.allow_exec
  force_new_deployment               = true
  launch_type                        = "FARGATE"
  scheduling_strategy                = "REPLICA"
  task_definition                    = aws_ecs_task_definition.frontend.arn

  load_balancer {
    container_name   = "frontend"
    container_port   = var.frontend_port
    target_group_arn = var.lb_target_group_arn
  }

  network_configuration {
    security_groups  = [aws_security_group.frontend.id]
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }
}

resource "aws_ecs_service" "backend" {
  name                               = "${var.environment_name}-backend"
  cluster                            = aws_ecs_cluster.main.arn
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100 # There should always be at least the desired count running during a deployment
  desired_count                      = var.backend_task_desired_count
  enable_execute_command             = var.allow_exec
  force_new_deployment               = true
  launch_type                        = "FARGATE"
  scheduling_strategy                = "REPLICA"
  task_definition                    = aws_ecs_task_definition.backend.arn

  network_configuration {
    security_groups  = [aws_security_group.backend.id]
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }
}

resource "aws_ecs_service" "worker" {
  name                               = "${var.environment_name}-backend"
  cluster                            = aws_ecs_cluster.main.arn
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100 # There should always be at least the desired count running during a deployment
  desired_count                      = var.worker_task_desired_count
  enable_execute_command             = var.allow_exec
  force_new_deployment               = true
  launch_type                        = "FARGATE"
  scheduling_strategy                = "REPLICA"
  task_definition                    = aws_ecs_task_definition.worker.arn

  network_configuration {
    security_groups  = [aws_security_group.worker.id]
    subnets          = var.private_subnet_ids
    assign_public_ip = false
  }
}

resource "aws_service_discovery_private_dns_namespace" "private_dns_namespace" {
  name        = "local-transcribe-internal"
  description = "local-transcribe private dns namespace"
  vpc         = var.vpc_id
}

resource "aws_service_discovery_service" "backend_service_discovery_service" {
  name = "local-transcribe-backend"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.private_dns_namespace.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }
}