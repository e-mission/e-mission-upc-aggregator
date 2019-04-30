docker build -f docker/Dockerfile -t emission/test-server:latest ./docker
docker build -f docker/Dockerfile-querier -t emission/test-querier:latest ./docker
docker build -f docker/Dockerfile-mongo -t emission/mongo-custom:latest ./docker
