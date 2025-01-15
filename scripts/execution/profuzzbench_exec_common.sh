#!/bin/bash

DOCIMAGE=$1   #name of the docker image
RUNS=$2       #number of runs
SAVETO=$3     #path to folder keeping the results

FUZZER=$4     #fuzzer name (e.g., aflnet) -- this name must match the name of the fuzzer folder inside the Docker container
OUTDIR=$5     #name of the output folder created inside the docker container
OPTIONS=$6    #all configured options for fuzzing
TIMEOUT=$7    #time for fuzzing
SKIPCOUNT=$8  #used for calculating coverage over time. e.g., SKIPCOUNT=5 means we run gcovr after every 5 test cases
DELETE=$9

WORKDIR="/home/ubuntu/experiments"

#keep all container ids
cids=()

# Get git branch and latest commit ID for ProFuzzBench repository
PROF_BRANCH=$(git -C "$(dirname "$0")" rev-parse --abbrev-ref HEAD)
PROF_COMMIT=$(git -C "$(dirname "$0")" rev-parse HEAD)

# Prepare to retrieve fuzzer repository information
# The fuzzer's repository will be cloned inside the Docker container. We will retrieve the information by running a temporary container.
TEMP_CONTAINER=$(docker create $DOCIMAGE /bin/bash)
docker start $TEMP_CONTAINER

# Ensure the container is running before retrieving git information
FUZZ_BRANCH=$(docker exec $TEMP_CONTAINER bash -c "cd '/home/ubuntu/${FUZZER}' && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown'")
FUZZ_COMMIT=$(docker exec $TEMP_CONTAINER bash -c "cd '/home/ubuntu/${FUZZER}' && git rev-parse HEAD 2>/dev/null || echo 'unknown'")

# Stop and remove the temporary container after use
docker stop $TEMP_CONTAINER > /dev/null
docker rm -f $TEMP_CONTAINER > /dev/null

# Save the information to a file
INFO_FILE="${SAVETO}/${FUZZER}_info.txt"
echo "ProFuzzBench Repository:" > "$INFO_FILE"
echo "Branch: $PROF_BRANCH" >> "$INFO_FILE"
echo "Latest Commit: $PROF_COMMIT" >> "$INFO_FILE"
echo "" >> "$INFO_FILE"
echo "Fuzzer Repository:" >> "$INFO_FILE"
echo "Branch: $FUZZ_BRANCH" >> "$INFO_FILE"
echo "Latest Commit: $FUZZ_COMMIT" >> "$INFO_FILE"

# Create one container for each run
for i in $(seq 1 $RUNS); do
  id=$(docker run --cpus=1 -d -it $DOCIMAGE /bin/bash -c "cd ${WORKDIR} && run ${FUZZER} ${OUTDIR} '${OPTIONS}' ${TIMEOUT} ${SKIPCOUNT}")
  cids+=(${id::12}) #store only the first 12 characters of a container ID
done

dlist="" #docker list
for id in ${cids[@]}; do
  dlist+=" ${id}"
done

#wait until all these dockers are stopped
printf "\n${FUZZER^^}: Fuzzing in progress ..."
printf "\n${FUZZER^^}: Waiting for the following containers to stop: ${dlist}"
docker wait ${dlist} > /dev/null
wait

#collect the fuzzing results from the containers
printf "\n${FUZZER^^}: Collecting results and save them to ${SAVETO}"
index=1
for id in ${cids[@]}; do
  printf "\n${FUZZER^^}: Collecting results from container ${id}"
  docker cp ${id}:/home/ubuntu/experiments/${OUTDIR}.tar.gz ${SAVETO}/${OUTDIR}_${index}.tar.gz > /dev/null
  if [ ! -z $DELETE ]; then
    printf "\nDeleting ${id}"
    docker rm ${id} # Remove container now that we don't need it
  fi
  index=$((index+1))
done

printf "\n${FUZZER^^}: I am done!\n"
