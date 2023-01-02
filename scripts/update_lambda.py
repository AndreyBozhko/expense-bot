"""Package the code as zip archive, upload to S3,
and update the Lambda function."""
import os
import shutil
import subprocess
from pathlib import Path

import boto3

OBJECT_NAME = "expense_bot/lambda.zip"

PROJECT_DIR = Path(__file__).parent.parent.absolute()
TMP_DIR = PROJECT_DIR / "tmp"
HANDLER = PROJECT_DIR / "lambda.py"
ARCHIVE = PROJECT_DIR / "lambda.zip"


if __name__ == "__main__":
    assert "PIP_PREFIX" not in os.environ, "PIP_PREFIX should not be set!"

    if TMP_DIR.exists():
        print(f"-> Removing folder {TMP_DIR}")
        shutil.rmtree(TMP_DIR)

    if ARCHIVE.exists():
        print(f"-> Removing archive {ARCHIVE}")
        os.remove(ARCHIVE)

    print(f"-> Creating folder {TMP_DIR}")
    TMP_DIR.mkdir()

    print(f"-> Installing packages into {TMP_DIR}")
    subprocess.run(
        f"pip install -r reqs/requirements.txt --target {TMP_DIR}".split(),
        check=True,
    )
    subprocess.run(
        f"pip install . --no-deps --target {TMP_DIR}".split(),
        check=True,
    )

    print(f"-> Copying lambda handler to {TMP_DIR}")
    shutil.copyfile(HANDLER, TMP_DIR / HANDLER.name)

    print(f"-> Creating zip archive {ARCHIVE}")
    subprocess.run(
        ["bash", "-c", f"pushd {TMP_DIR} && zip -q -r {ARCHIVE} * && popd"],
        check=True,
    )

    s3 = boto3.client("s3")
    buckets = s3.list_buckets()["Buckets"]

    BUCKET_NAME = buckets[0]["Name"]

    print(f"-> Uploading archive to s3://{BUCKET_NAME}/{OBJECT_NAME}")
    s3.upload_file(str(ARCHIVE), BUCKET_NAME, OBJECT_NAME)

    print("-> Updating lambda function")
    client = boto3.client("lambda")
    client.update_function_code(
        FunctionName="expense_bot",
        S3Bucket=BUCKET_NAME,
        S3Key=OBJECT_NAME,
    )

    print("-> Done")
