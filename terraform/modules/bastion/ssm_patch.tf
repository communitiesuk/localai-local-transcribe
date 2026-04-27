resource "aws_ssm_maintenance_window" "bastion_patch" {
  name     = "${var.environment_name}-ssm-patch-window"
  schedule = "cron(0 2 ? * WED *)" # Every Wednesday at 2 AM UTC
  duration = 3
  cutoff   = 1
}

resource "aws_ssm_maintenance_window_task" "bastion_patch" {
  window_id       = aws_ssm_maintenance_window.bastion_patch.id
  max_errors      = 1
  max_concurrency = 1
  task_type       = "RUN_COMMAND"
  task_arn        = "AWS-RunPatchBaseline"
  priority        = 1

  targets {
    key    = "InstanceIds"
    values = aws_instance.bastion[*].id
  }

  task_invocation_parameters {
    run_command_parameters {
      comment = "Default Baseline Install"
      parameter {
        name   = "Operation"
        values = ["Install"]
      }
    }
  }
}

# Auto Update SSM agents on existing instances
resource "aws_ssm_association" "bastion_patch_ssm_agent_update" {
  name                = "AWS-UpdateSSMAgent"
  schedule_expression = "cron(0 2 ? * TUE *)" # Every Tuesday at 2 AM UTC

  targets {
    key    = "InstanceIds"
    values = aws_instance.bastion[*].id
  }
}