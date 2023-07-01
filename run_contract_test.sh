source ~/.bash_profile
sam local start-lambda
cfn generate && cfn submit --dry-run && cfn test