#!/usr/bin/env python3
"""
Enhanced configuration for AWS AI Cost Calculator
Enables high-accuracy cost tracking with real-time data
"""

# AI Service Configuration with exact resource mappings
AI_SERVICE_CONFIG = {
    "bedrock": {
        "name": "Amazon Bedrock",
        "cost_percentage": 100,  # 100% of Bedrock costs are AI-related
        "service_codes": ["AmazonBedrock"],
        "resources": {
            "ask-eva": [
                "ask-eva-poc-agent-quick-start-i87ch",
                "agent-quick-start-npl14",
                "sa-ai-ask-eva-tone-agent-quick-start-rc5o4",
                "askk-eva-poc-knowledge-base-quick-start-xejg1",
                "knowledge-base-quick-start-bmm8s"
            ],
            "models": ["Claude 3 Haiku", "Claude 3 Sonnet", "Claude 3.5 Sonnet"]
        }
    },
    "kendra": {
        "name": "Amazon Kendra",
        "cost_percentage": 100,  # 100% of Kendra costs are AI-related
        "service_codes": ["AWSKendraEnterprise", "AWSKendraDeveloper"],
        "resources": {
            "indexes": ["ask-eva-index", "iep-report-index"]
        }
    },
    "lambda": {
        "name": "AWS Lambda",
        "cost_percentage": 30,  # Estimated 30% of Lambda costs are AI-related
        "service_codes": ["AWSLambda"],
        "resources": {
            "ask-eva": [
                "sa-ai-ask-eva-Lambda",
                "sa-ai-ask-eva-list-conv-history"
            ],
            "iep-report": [
                "iepreport-GetAssessmentsFunction-l53azaI4m9i1",
                "iep_performacne",
                "iepreport-GetScholarDataFunction-sBjjEsEyEvUf",
                "iepreport-PdfGenerationFunction-cIR8b8PdbzpU",
                "querykb"
            ]
        }
    },
    "s3": {
        "name": "Amazon S3",
        "cost_percentage": 20,  # Estimated 20% of S3 costs are AI-related
        "service_codes": ["AmazonS3"],
        "resources": {
            "buckets": [
                "sa-ai-ask-eva",
                "sa-ai-ask-eva-frontend",
                "sa-ai-modeltraining"
            ]
        }
    },
    "dynamodb": {
        "name": "Amazon DynamoDB",
        "cost_percentage": 25,  # Estimated 25% of DynamoDB costs are AI-related
        "service_codes": ["AmazonDynamoDB"],
        "resources": {
            "tables": ["sa_ai_ask_eva_conversation_history"]
        }
    },
    "sagemaker": {
        "name": "Amazon SageMaker",
        "cost_percentage": 100,  # 100% of SageMaker costs are AI-related
        "service_codes": ["AmazonSageMaker", "AWSSageMakerNotebooks"],
        "resources": {}
    },
    "comprehend": {
        "name": "Amazon Comprehend",
        "cost_percentage": 100,  # 100% of Comprehend costs are AI-related
        "service_codes": ["AmazonComprehend"],
        "resources": {}
    },
    "transcribe": {
        "name": "Amazon Transcribe",
        "cost_percentage": 100,  # 100% of Transcribe costs are AI-related
        "service_codes": ["AmazonTranscribe"],
        "resources": {}
    },
    "polly": {
        "name": "Amazon Polly",
        "cost_percentage": 100,  # 100% of Polly costs are AI-related
        "service_codes": ["AmazonPolly"],
        "resources": {}
    },
    "api-gateway": {
        "name": "Amazon API Gateway",
        "cost_percentage": 25,  # Estimated 25% for AI endpoints
        "service_codes": ["AmazonApiGateway"],
        "resources": {}
    },
    "cloudwatch": {
        "name": "Amazon CloudWatch",
        "cost_percentage": 15,  # Estimated 15% for AI monitoring
        "service_codes": ["AmazonCloudWatch"],
        "resources": {}
    }
}

# Cost allocation tags for more accurate tracking
COST_ALLOCATION_TAGS = [
    "Project",
    "Environment",
    "Application",
    "ai-project",
    "cost-center"
]

# Projects and their expected resources
AI_PROJECTS = {
    "ask-eva": {
        "name": "Ask Eva Bot",
        "status": "POC",
        "environment": "sandbox",
        "description": "Bot simulating answers from school staff"
    },
    "iep-report": {
        "name": "IEP Report Generator",
        "status": "MVP",
        "environment": "sandbox",
        "description": "Generate PDF reports for scholars from URLs"
    },
    "financial-aid": {
        "name": "Financial Aid Filter",
        "status": "MVP",
        "environment": "sandbox",
        "description": "Filter financial aid letters to show actual costs"
    },
    "resume-knockout": {
        "name": "Resume Knockout",
        "status": "Paused",
        "environment": "sandbox",
        "description": "Resume filtering based on business criteria"
    },
    "resume-scoring": {
        "name": "Resume Scoring",
        "status": "Paused",
        "environment": "TBD",
        "description": "Ranking resumes based on business criteria"
    }
}

# AWS Account mappings
AWS_ACCOUNTS = {
    "339713126986": {
        "name": "SA Sandbox",
        "environment": "sandbox",
        "type": "development"
    },
    "123456789012": {  # Update with actual non-prod account ID
        "name": "SA Non-Prod",
        "environment": "non-production",
        "type": "staging"
    }
}

# Date range for cost calculations
DEFAULT_DATE_RANGE = {
    "months_back": 3,  # Look back 3 months
    "include_current": True  # Include current month
}

# High accuracy settings
ACCURACY_SETTINGS = {
    "use_tags": True,  # Use cost allocation tags
    "detailed_metrics": True,  # Get detailed metrics
    "resource_matching": True,  # Match specific resources
    "real_time": True,  # Use real-time data where available
    "cache_duration": 300  # Cache results for 5 minutes
}