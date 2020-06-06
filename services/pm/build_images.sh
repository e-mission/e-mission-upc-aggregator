cp -r ../../conf .
cp -r ../../shared_apis .
docker build -t e-mission/pm:1.0 .
docker build -t e-mission/custom-mongo:1.0 custom-mongo/
