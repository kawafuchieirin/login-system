output "users_table_name" {
  value = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  value = aws_dynamodb_table.users.arn
}

output "todos_table_name" {
  value = aws_dynamodb_table.todos.name
}

output "todos_table_arn" {
  value = aws_dynamodb_table.todos.arn
}

output "webauthn_credentials_table_name" {
  value = aws_dynamodb_table.webauthn_credentials.name
}

output "webauthn_credentials_table_arn" {
  value = aws_dynamodb_table.webauthn_credentials.arn
}

output "auth_challenges_table_name" {
  value = aws_dynamodb_table.auth_challenges.name
}

output "auth_challenges_table_arn" {
  value = aws_dynamodb_table.auth_challenges.arn
}
