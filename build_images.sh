docker build -f docker/Dockerfile -t emission/test-server:1.0 ./docker
docker build -f docker/Dockerfile-calendar -t emission/test-calendar:1.0 ./docker
#docker build -f docker/Dockerfile-controller -t emission/test-controller:1.0 ./docker
docker build -f docker/Dockerfile-querier -t emission/test-querier:1.0 ./docker
docker build -f docker/Dockerfile-mongo -t emission/mongo-custom:1.0 ./docker
