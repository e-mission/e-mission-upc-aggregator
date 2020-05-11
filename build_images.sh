# docker build -f docker/Dockerfile -t emission/test-server:1.0 ./docker
# docker build -f docker/Dockerfile-calendar -t emission/test-calendar:1.0 ./docker
docker build -f docker/Dockerfile-pipeline -t emission/test-pipeline:1.0 ./docker
docker build -f docker/Dockerfile-metrics -t emission/test-metrics:1.0 ./docker
docker build -f docker/Dockerfile-mongo -t emission/mongo-custom:1.0 ./docker
