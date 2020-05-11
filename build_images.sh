# docker build -f docker/Dockerfile -t emission/test-server:1.0 ./docker
# docker build -f docker/Dockerfile-calendar -t emission/test-calendar:1.0 ./docker
docker build -f docker/Dockerfile-pipeline -t gcr.io/upc-masters/test-pipeline:1.0 ./docker
#docker build -f docker/Dockerfile-metrics -t gcr.io/emission/test-metrics:1.0 ./docker
docker build -f docker/Dockerfile-mongo -t gcr.io/upc-masters/mongo-custom:1.0 ./docker
