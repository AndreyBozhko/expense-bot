"""Package the code as zip archive, upload to S3,
and update the Lambda function."""
import os
import shutil
import subprocess
import sysconfig
from pathlib import Path

import boto3

py = sysconfig.get_python_version()

OBJECT_NAME = "expense_bot/lambda.zip"

PROJECT_DIR = Path(__file__).parent.parent.absolute()
TMP_DIR = PROJECT_DIR / "tmp"
DST_DIR = TMP_DIR / ".venv" / "lib" / f"python{py}" / "site-packages"
HANDLER = PROJECT_DIR / "lambda.py"
ARCHIVE = PROJECT_DIR / "lambda.zip"


if __name__ == "__main__":
    if TMP_DIR.exists():
        print(f"-> Removing folder {TMP_DIR}")
        shutil.rmtree(TMP_DIR)

    if ARCHIVE.exists():
        print(f"-> Removing archive {ARCHIVE}")
        os.remove(ARCHIVE)

    print(f"-> Creating folder {TMP_DIR}")
    TMP_DIR.mkdir()

    print(f"-> Copying project files to {TMP_DIR}")
    shutil.copyfile(PROJECT_DIR / "pyproject.toml", TMP_DIR / "pyproject.toml")
    shutil.copyfile(PROJECT_DIR / "uv.lock", TMP_DIR / "uv.lock")

    print(f"-> Installing packages into {TMP_DIR}")
    subprocess.run(
        f"uv sync --frozen --no-default-groups --no-install-project --project {TMP_DIR}".split(),
        check=True,
    )
    subprocess.run(
        f"uv pip install . --no-deps --python {TMP_DIR}/.venv/".split(),
        check=True,
    )

    print(f"-> Copying lambda handler to {DST_DIR}")
    shutil.copyfile(HANDLER, DST_DIR / HANDLER.name)

    print(f"-> Creating zip archive {ARCHIVE}")
    subprocess.run(
        ["bash", "-c", f"pushd {DST_DIR} && zip -q -r {ARCHIVE} * && popd"],
        check=True,
    )

    print(f"-> Removing folder {TMP_DIR}")
    shutil.rmtree(TMP_DIR)

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
