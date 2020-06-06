cp -r ../../conf .
cp -r ../../shared_apis .
docker build -t emission/pm:1.0 .
docker build -t emission/custom-mongo:1.0 custom-mongo/
