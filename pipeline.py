import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import json
from datetime import datetime

PROJECT_ID = "your-gcp-project-id"
BUCKET_NAME = f"{PROJECT_ID}-temp"


class ParseTransaction(beam.DoFn):

    def process(self, element):

        record = json.loads(element.decode("utf-8"))
        record["event_time"] = datetime.fromisoformat(record["event_time"])

        yield record


class DetectFraud(beam.DoFn):

    def process(self, record):

        suspicious = False
        fraud_reason = None

        if record["amount"] > 1500:
            suspicious = True
            fraud_reason = "HIGH_AMOUNT"

        if record["amount"] <= 0:
            suspicious = True
            fraud_reason = "INVALID_AMOUNT"

        if suspicious:
            record["fraud_reason"] = fraud_reason
            yield beam.pvalue.TaggedOutput("fraud", record)
        else:
            yield record


options = PipelineOptions(
    streaming=True,
    runner="DataflowRunner",
    project=PROJECT_ID,
    region="asia-south2",
    temp_location=f"gs://{BUCKET_NAME}/temp",
    staging_location=f"gs://{BUCKET_NAME}/staging",
    job_name="fraud-detection-stream-test"
)


with beam.Pipeline(options=options) as p:

    transactions = (
        p
        | "Read from PubSub"
        >> beam.io.ReadFromPubSub(
            subscription=f"projects/{PROJECT_ID}/subscriptions/tramsaction-sub"
        )
    )

    parsed_transactions = (
        transactions
        | "Parse JSON"
        >> beam.ParDo(ParseTransaction())
    )

    results = (
        parsed_transactions
        | "Detect Fraud"
        >> beam.ParDo(DetectFraud()).with_outputs("fraud", main="normal")
    )

    normal_transactions = results.normal
    fraud_transactions = results.fraud

    normal_transactions | "Write Normal Transactions" >> beam.io.WriteToBigQuery(
    table=f"{PROJECT_ID}:fraud_detection.transactions",
    schema="transaction_id:STRING,card_id:STRING,merchant:STRING,amount:FLOAT,location:STRING,event_time:TIMESTAMP",
    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
    create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER
    )

    fraud_transactions | "Write Fraud Alerts" >> beam.io.WriteToBigQuery(
    table=f"{PROJECT_ID}:fraud_detection.fraud_alerts",
    schema="transaction_id:STRING,card_id:STRING,merchant:STRING,amount:FLOAT,location:STRING,event_time:TIMESTAMP,fraud_reason:STRING",
    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
    create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER
    )