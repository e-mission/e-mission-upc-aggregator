cp -r ../../conf/* conf/
cp -r ../../shared_apis .
docker build -t e-mission/pipeline:1.0 .
