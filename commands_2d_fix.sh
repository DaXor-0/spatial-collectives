#!/usr/bin/env bash
# set -e
# 2D Reduce and Allreduce

ARCH="${ARCH:-wse2}"
MEASUREMENT_REPEATS=5
: "${CEREBRAS_SIM_ENVIRONMENT:=1}"
export CEREBRAS_SIM_ENVIRONMENT
if [ "${CEREBRAS_SIM_ENVIRONMENT}" = "1" ]; then
  MEASUREMENT_REPEATS=1
fi

for algo in {0..3}
do
  sqrt_result=$(echo "sqrt(512)" | bc -l)
  int_result=${sqrt_result%.*}
  cslc layout_2d_test.csl --arch="$ARCH" --fabric-dims=519,514 \
  --fabric-offsets=4,1 --params=Nx_start:1,Pw:512,Ph:512,Algo:$algo,is_allred:0,step:$int_result,repeats:$MEASUREMENT_REPEATS -o out --memcpy --channels=1
  cs_python run_2d_test.py --name out
done

for algo in {0..3}
do
  sqrt_result=$(echo "sqrt(512)" | bc -l)
  int_result=${sqrt_result%.*}
  cslc layout_2d_test.csl --arch="$ARCH" --fabric-dims=519,514 \
  --fabric-offsets=4,1 --params=Nx_start:1,Pw:512,Ph:512,Algo:$algo,is_allred:1,step:$int_result,repeats:$MEASUREMENT_REPEATS -o out --memcpy --channels=1
  cs_python run_2d_test.py --name out
done
