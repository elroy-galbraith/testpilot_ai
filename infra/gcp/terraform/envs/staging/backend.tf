terraform {
  backend "gcs" {
    bucket = "testpilot-ai-terraform-state-staging-testpilotai-467409"
    prefix = "terraform/state"
  }
}
