# Infrastructure Quick Reference

## 🗑️ Destroy Everything (Clean Slate)

```bash
# 1. Destroy Terraform environments
docker run --rm -it -v $(pwd):/workspace -v ~/.aws:/root/.aws -w /workspace/infra/terraform/envs/staging infra terraform destroy
docker run --rm -it -v $(pwd):/workspace -v ~/.aws:/root/.aws -w /workspace/infra/terraform/envs/production infra terraform destroy

# 2. Destroy backend infrastructure
cd infra/terraform
./scripts/destroy-backend.sh
```

## 🔄 Rebuild Everything

```bash
# 1. Initialize backend
cd infra/terraform
./scripts/init-backend.sh

# 2. Deploy staging
cd envs/staging
docker run --rm -it -v $(pwd):/workspace -v ~/.aws:/root/.aws -w /workspace/infra/terraform/envs/staging infra terraform init
docker run --rm -it -v $(pwd):/workspace -v ~/.aws:/root/.aws -w /workspace/infra/terraform/envs/staging infra terraform apply

# 3. Deploy production
cd ../production
docker run --rm -it -v $(pwd):/workspace -v ~/.aws:/root/.aws -w /workspace/infra/terraform/envs/production infra terraform init
docker run --rm -it -v $(pwd):/workspace -v ~/.aws:/root/.aws -w /workspace/infra/terraform/envs/production infra terraform apply
```

## 🔍 Check Status

```bash
# List S3 buckets
aws s3 ls --profile default

# List DynamoDB tables
aws dynamodb list-tables --profile default

# Check Terraform state
docker run --rm -it -v $(pwd):/workspace -v ~/.aws:/root/.aws -w /workspace/infra/terraform/envs/staging infra terraform state list
```

## 💰 Cost Monitoring

- Set up AWS Cost Explorer
- Enable billing alerts
- Monitor Free Tier usage
- Use AWS Budgets for spending limits

## ⚠️ Important Notes

- Always run `terraform destroy` before switching AWS accounts
- Keep your Terraform code in version control
- Test in staging before production
- Monitor costs regularly
- Use Free Tier when possible 