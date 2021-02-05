cp -r ../../conf/* conf/
cp -r ../../shared_apis .
docker build -t e-mission/count:1.0 .
