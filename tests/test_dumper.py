import time
from unittest.mock import patch, MagicMock
from core.models import DumpOptions
from core.dumper import mask_uri_secrets, build_mongodump_args, MongoDumper

def test_mask_uri_secrets_standard():
    raw_cmd = "mongodump --uri=mongodb://admin:SuperSecretPass123!@localhost:27017/sales?authSource=admin --gzip"
    masked = mask_uri_secrets(raw_cmd)
    assert "SuperSecretPass123!" not in masked
    assert "mongodb://admin:***@localhost:27017/sales?authSource=admin" in masked

def test_mask_uri_secrets_srv():
    raw_cmd = "Connected to mongodb+srv://app_user:p%40ssw0rd!@cluster0.abcde.mongodb.net/test?retryWrites=true"
    masked = mask_uri_secrets(raw_cmd)
    assert "p%40ssw0rd!" not in masked
    assert "mongodb+srv://app_user:***@cluster0.abcde.mongodb.net/test?retryWrites=true" in masked

def test_mask_uri_secrets_no_auth():
    raw = "Connecting to mongodb://localhost:27017/mydb"
    masked = mask_uri_secrets(raw)
    assert masked == raw

def test_build_mongodump_args_archive():
    opts = DumpOptions(
        db="mydb",
        collection="mycol",
        output_mode="archive",
        output_path="backup.archive",
        gzip=True,
        num_parallel_collections=2,
        read_preference="secondaryPreferred",
        exclude_collections="logs,cache"
    )
    args = build_mongodump_args("/usr/bin/mongodump", "mongodb://localhost:27017", opts)
    assert args[0] == "/usr/bin/mongodump"
    assert "--uri=mongodb://localhost:27017" in args
    assert "--db=mydb" in args
    assert "--collection=mycol" in args
    assert "--archive=backup.archive" in args
    assert "--gzip" in args
    assert "--numParallelCollections=2" in args
    assert "--readPreference=secondaryPreferred" in args
    assert "--excludeCollection=logs" in args
    assert "--excludeCollection=cache" in args

def test_build_mongodump_args_directory():
    opts = DumpOptions(
        db="",
        collection="",
        output_mode="dir",
        output_path="./dump_dir",
        gzip=False
    )
    args = build_mongodump_args("mongodump", "mongodb://127.0.0.1:27017", opts)
    assert "--out=./dump_dir" in args
    assert "--gzip" not in args

def test_dumper_execution_and_callbacks():
    dumper = MongoDumper()
    logs = []
    finished_code = []

    def on_log(line):
        logs.append(line)

    def on_finished(code):
        finished_code.append(code)

    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout.readline.side_effect = [
        "2026-11-10T12:00:00.000 writing mydb.col to archive\n",
        "2026-11-10T12:00:01.000 done dumping mydb.col (100 documents)\n",
        ""
    ]
    mock_process.poll.side_effect = [None, None, 0]
    mock_process.wait.return_value = 0

    with patch("subprocess.Popen", return_value=mock_process):
        opts = DumpOptions(db="mydb")
        dumper.start("mongodump", "mongodb://localhost:27017", opts, on_log, on_finished)
        # Wait briefly for worker thread to finish
        dumper.wait(timeout=2.0)
        assert len(logs) == 4  # Initial command log + 2 stream logs + completion log
        assert "[Dump completed successfully]" in logs[-1]
        assert finished_code == [0]
        assert not dumper.is_running
