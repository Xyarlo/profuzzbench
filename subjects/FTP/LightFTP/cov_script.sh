#!/bin/bash

folder=$1   #fuzzer result folder
pno=$2      #port number
step=$3     #step to skip running gcovr and outputting data to covfile
            #e.g., step=5 means we run gcovr after every 5 test cases
covfile=$4  #path to coverage file
fmode=$5    #file mode -- structured or not
            #fmode = 0: the test case is a concatenated message sequence -- there is no message boundary
            #fmode = 1: the test case is a structured file keeping several request messages

#delete the existing coverage file
rm $covfile; touch $covfile

#clear gcov data
#since the source files of LightFTP are stored in the parent folder of the current folder
#we use '..' instead of '.' as usual. You may need to update this accordingly for your subject
gcovr -r .. -s -d > /dev/null 2>&1

#output the header of the coverage file which is in the CSV format
#Time: timestamp, l_per/b_per and l_abs/b_abs: line/branch coverage in percentage and absolutate number
echo "Time,l_per,l_abs,b_per,b_abs,states_abs,fuzzed_seeds" >> $covfile

#clear ftp data
#this is a LightFTP-specific step
#we need to clean the ftp shared folder to prevent underterministic behaviors.
ftpclean

#files stored in replayable-* folders are structured
#in such a way that messages are separated
if [ $fmode -eq "1" ]; then
  testdir="replayable-queue"
  replayer="aflnet-replay"
else
  testdir="queue"
  replayer="afl-replay"
fi

#process initial seed corpus first
for f in $(echo $folder/$testdir/*.raw); do 
  time=$(stat -c %Y $f)

  #terminate running server(s)
  pkill fftp

  ftpclean  
  $replayer $f FTP $pno 1 > /dev/null 2>&1 &
  timeout -k 0 -s SIGUSR1 3s ./fftp fftp.conf $pno > /dev/null 2>&1
  
  wait
  cov_data=$(gcovr -r .. -s | grep "[lb][a-z]*:")
  l_per=$(echo "$cov_data" | grep lines | cut -d" " -f2 | rev | cut -c2- | rev)
  l_abs=$(echo "$cov_data" | grep lines | cut -d" " -f3 | cut -c2-)
  b_per=$(echo "$cov_data" | grep branch | cut -d" " -f2 | rev | cut -c2- | rev)
  b_abs=$(echo "$cov_data" | grep branch | cut -d" " -f3 | cut -c2-)

  # Extract state coverage from the file
  states_abs=$(strings "$f" | grep -oP '(?<=# State Coverage: )\d+')
  states_abs=${states_abs:-0}  # Default to 0 if not found

  # Extract fuzzed seeds from the file
  fuzzed_seeds=$(strings "$f" | grep -oP '(?<=# Fuzzed Seeds: )\d+')
  fuzzed_seeds=${fuzzed_seeds:-0}  # Default to 0 if not found

  # Log the coverage data along with state coverage and fuzzed seeds
  echo "$time,$l_per,$l_abs,$b_per,$b_abs,$states_abs,$fuzzed_seeds" >> $covfile

done

#process fuzzer-generated testcases
count=0
for f in $(echo $folder/$testdir/id*); do 
  time=$(stat -c %Y $f)

  #terminate running server(s)
  pkill fftp
  
  ftpclean  
  $replayer $f FTP $pno 1 > /dev/null 2>&1 &
  timeout -k 0 -s SIGUSR1 3s ./fftp fftp.conf $pno > /dev/null 2>&1

  wait
  count=$(expr $count + 1)
  rem=$(expr $count % $step)
  if [ "$rem" != "0" ]; then continue; fi
  cov_data=$(gcovr -r .. -s | grep "[lb][a-z]*:")
  l_per=$(echo "$cov_data" | grep lines | cut -d" " -f2 | rev | cut -c2- | rev)
  l_abs=$(echo "$cov_data" | grep lines | cut -d" " -f3 | cut -c2-)
  b_per=$(echo "$cov_data" | grep branch | cut -d" " -f2 | rev | cut -c2- | rev)
  b_abs=$(echo "$cov_data" | grep branch | cut -d" " -f3 | cut -c2-)

  # Extract state coverage from the file
  states_abs=$(strings "$f" | grep -oP '(?<=# State Coverage: )\d+')
  states_abs=${states_abs:-0}  # Default to 0 if not found

  # Extract fuzzed seeds from the file
  fuzzed_seeds=$(strings "$f" | grep -oP '(?<=# Fuzzed Seeds: )\d+')
  fuzzed_seeds=${fuzzed_seeds:-0}  # Default to 0 if not found

  # Log the coverage data along with state coverage and fuzzed seeds
  echo "$time,$l_per,$l_abs,$b_per,$b_abs,$states_abs,$fuzzed_seeds" >> $covfile

done

#ouput cov data for the last testcase(s) if step > 1
if [[ $step -gt 1 ]]
then
  time=$(stat -c %Y $f)
  cov_data=$(gcovr -r .. -s | grep "[lb][a-z]*:")
  l_per=$(echo "$cov_data" | grep lines | cut -d" " -f2 | rev | cut -c2- | rev)
  l_abs=$(echo "$cov_data" | grep lines | cut -d" " -f3 | cut -c2-)
  b_per=$(echo "$cov_data" | grep branch | cut -d" " -f2 | rev | cut -c2- | rev)
  b_abs=$(echo "$cov_data" | grep branch | cut -d" " -f3 | cut -c2-)

  # Extract state coverage from the file
  states_abs=$(strings "$f" | grep -oP '(?<=# State Coverage: )\d+')
  states_abs=${states_abs:-0}  # Default to 0 if not found

  # Extract fuzzed seeds from the file
  fuzzed_seeds=$(strings "$f" | grep -oP '(?<=# Fuzzed Seeds: )\d+')
  fuzzed_seeds=${fuzzed_seeds:-0}  # Default to 0 if not found

  # Log the coverage data along with state coverage and fuzzed seeds
  echo "$time,$l_per,$l_abs,$b_per,$b_abs,$states_abs,$fuzzed_seeds" >> $covfile

fi
