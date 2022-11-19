resource "aws_iam_user" "iam-user" {
  name = "${var.aws_iam_username}"
  path = "${var.aws_iam_grouppath}"
  
}