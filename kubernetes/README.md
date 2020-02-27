# Docker NewArch Instructions 

For the new architecture this is all you should need to do to have the proper containers.


For the usercloud:
   ```
   docker build -f docker/Dockerfile -t emission/test-server:latest ./docker
   ```

For the querier:
   ```
   docker build -f docker/Dockerfile-querier -t emission/test-querier:latest ./docker
   ```

For Mongo image:
   ```
   docker build -f docker/Dockerfile-mongo -t emission/mongo-custom:latest ./docker
   ```

If you want to add additional queriers you will also need to build additional images. We make the assumption that you will have a unique docker compose file for each query type, called:

  ```
  docker-compose-<query_name>.yml
  ```

which will build a querier service that depends on the image.

  ```
  emission/<query_name>
  ```

If you make any changes, any launched docker images will update because the docker image relies on a git pull command. Thus updates can be done just be pushing to target repo and without rebuilding any of hte images.
