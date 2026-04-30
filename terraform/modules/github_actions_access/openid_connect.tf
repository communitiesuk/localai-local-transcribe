resource "aws_iam_openid_connect_provider" "main" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # The README for the Github action explains that this must be provided but AWS ignores it when using Github as a IdP
  # https://github.com/aws-actions/configure-aws-credentials
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]
}