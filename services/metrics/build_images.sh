cp -r ../../conf/* conf/
cp -r ../../shared_apis .
docker build -t e-mission/metrics:1.0 .
