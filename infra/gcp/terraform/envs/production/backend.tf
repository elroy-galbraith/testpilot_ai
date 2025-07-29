terraform {
  backend "gcs" {
    bucket = "testpilot-ai-terraform-state-production-testpilotai-467409"
    prefix = "terraform/state"
  }
}
