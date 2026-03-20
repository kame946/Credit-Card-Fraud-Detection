# Credit Card Fraud Detection Pipeline

This project implements a real-time credit card fraud detection pipeline using Google Cloud Platform (GCP) services and Apache Beam. The pipeline processes transaction data streamed from Pub/Sub, detects potential fraudulent activities based on simple rules, and stores the results in BigQuery for further analysis.

## Architecture Overview

The pipeline consists of the following components:

1. **Data Producer** (`producer.py`): Generates synthetic credit card transaction data and publishes it to a Google Cloud Pub/Sub topic.
2. **Apache Beam Pipeline** (`pipeline.py`): Consumes messages from Pub/Sub, processes the data in real-time, applies fraud detection logic, and writes results to BigQuery.
3. **Google Cloud Services**:
   - **Pub/Sub**: For real-time message streaming.
   - **Dataflow**: As the runner for the Apache Beam pipeline.
   - **BigQuery**: For storing processed transaction data.

### GCP Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Data Producer │────▶│  Pub/Sub Topic  │────▶│  Dataflow Job   │────▶│  BigQuery       │
│   (producer.py) │     │                 │     │ (Apache Beam)   │     │  Tables         │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                            │
                                                            ▼
                                               ┌─────────────────┐
                                               │ Fraud Detection │
                                               │   Logic         │
                                               └─────────────────┘
                                                            │
                                               ┌─────────────────┐
                                               │   Normal TX     │
                                               │   Fraud Alerts  │
                                               └─────────────────┘
```

**Flow Description:**
- **Data Producer**: Runs locally or on a VM, generates transaction data.
- **Pub/Sub**: Acts as the message buffer for real-time streaming.
- **Dataflow**: Executes the Apache Beam pipeline, scales automatically.
- **BigQuery**: Stores processed data in tables for analytics and reporting.

## Data Flow

1. The producer generates fake transaction records with fields like transaction ID, card ID, merchant, amount, location, and timestamp.
2. Transactions are published to a Pub/Sub topic.
3. The Apache Beam pipeline reads from the Pub/Sub subscription.
4. Each transaction is parsed from JSON format.
5. Fraud detection logic is applied:
   - Transactions with amount > 1500 are flagged as "HIGH_AMOUNT".
   - Transactions with amount <= 0 are flagged as "INVALID_AMOUNT".
6. Normal transactions are written to the `transactions` table in BigQuery.
7. Fraudulent transactions are written to the `fraud_alerts` table in BigQuery with an additional `fraud_reason` field.

## Prerequisites

- Google Cloud Platform account with billing enabled.
- GCP project with the following APIs enabled:
  - Cloud Pub/Sub API
  - Cloud Dataflow API
  - BigQuery API
- Google Cloud SDK installed and authenticated.
- Python 3.7+ installed.

## Setup Instructions

1. **Clone or download the project files.**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure GCP settings:**
   - Update `PROJECT_ID` in both `producer.py` and `pipeline.py` with your actual GCP project ID.
   - Ensure the Pub/Sub topic and subscription exist, or create them:
     ```bash
     gcloud pubsub topics create transaction-topic
     gcloud pubsub subscriptions create transaction-sub --topic=transaction-topic
     ```
   - Create the BigQuery dataset and tables:
     ```bash
     bq mk fraud_detection
     bq mk --table fraud_detection.transactions transaction_id:STRING,card_id:STRING,merchant:STRING,amount:FLOAT,location:STRING,event_time:TIMESTAMP
     bq mk --table fraud_detection.fraud_alerts transaction_id:STRING,card_id:STRING,merchant:STRING,amount:FLOAT,location:STRING,event_time:TIMESTAMP,fraud_reason:STRING
     ```
   - Create a GCS bucket for Dataflow staging (replace `your-project-id`):
     ```bash
     gsutil mb gs://your-project-id-temp
     ```

4. **Update configuration:**
   - In `producer.py`, set `PROJECT_ID` and `TOPIC_ID` as needed.
   - In `pipeline.py`, ensure `PROJECT_ID` is set correctly, and update the subscription name if different.

## Running the Pipeline

1. **Start the data producer:**
   ```bash
   python producer.py
   ```
   This will begin generating and publishing fake transactions to Pub/Sub every second.

2. **Run the Apache Beam pipeline:**
   ```bash
   python pipeline.py
   ```
   This will launch the Dataflow job to process the streaming data.

3. **Monitor the pipeline:**
   - Check the Dataflow console in GCP for job status.
   - Query BigQuery tables to see processed data:
     ```sql
     SELECT * FROM `your-project-id.fraud_detection.transactions` LIMIT 10;
     SELECT * FROM `your-project-id.fraud_detection.fraud_alerts` LIMIT 10;
     ```

## Customization

- **Fraud Detection Rules**: Modify the `DetectFraud` class in `pipeline.py` to add more sophisticated fraud detection logic.
- **Data Schema**: Update the BigQuery schemas in `pipeline.py` if you add new fields to transactions.
- **Scalability**: Adjust Dataflow worker settings in `PipelineOptions` for production workloads.

## Files Description

- `pipeline.py`: Main Apache Beam pipeline code.
- `producer.py`: Data producer script for generating test transactions.
- `requirements.txt`: Python dependencies.
- `README.md`: This documentation file.

## Troubleshooting

- Ensure all GCP services are enabled and you have appropriate permissions.
- Check Pub/Sub topic and subscription names match between producer and pipeline.
- Verify BigQuery dataset and table names.
- Monitor Dataflow logs for any runtime errors.
