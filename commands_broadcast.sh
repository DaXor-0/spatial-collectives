#!/usr/bin/env bash
# set -e

ARCH="${ARCH:-wse2}"
MEASUREMENT_REPEATS=5
: "${CEREBRAS_SIM_ENVIRONMENT:=1}"
export CEREBRAS_SIM_ENVIRONMENT
if [ "${CEREBRAS_SIM_ENVIRONMENT}" = "1" ]; then
  MEASUREMENT_REPEATS=1
fi

for vec_len in {0..12}
do
  for ((repeat=1; repeat<=MEASUREMENT_REPEATS; repeat++))
  do
    cslc layout_broadcast.csl --arch="$ARCH" --fabric-dims=519,3 \
    --fabric-offsets=4,1 --params=Nx:$((2**$vec_len)),Pw:512,Algo:0,is_allred:0,step:0 -o out --memcpy --channels=1
    cs_python run_bcast.py --name out
  done
done

for log_pes in {2..9}
do
  for ((repeat=1; repeat<=MEASUREMENT_REPEATS; repeat++))
  do
    cslc layout_broadcast.csl --arch="$ARCH" --fabric-dims=519,3 \
    --fabric-offsets=4,1 --params=Nx:256,Pw:$((2**$log_pes)),Algo:0,is_allred:0,step:0 -o out --memcpy --channels=1
    cs_python run_bcast.py --name out
  done
done
